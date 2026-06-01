from __future__ import annotations

import time
from types import ModuleType

import mujoco  # type: ignore[import-not-found]
import numpy as np
from scipy.spatial.transform import Rotation  # type: ignore[import-untyped]

from omniretarget.mujoco.collision import (  # noqa: E402
    geom_distance,
    geom_pair_allowed_for_object_or_ground,
    geometry_name,
    geometry_names,
    prefilter_pairs_with_mj_collision,
    should_enforce_non_penetration_pair,
)
from omniretarget.mujoco.kinematics import (  # noqa: E402
    body_id,
    link_positions,
    point_jacobian_qpos,
    qdot_to_qvel_transform,
    world_to_body_frame,
)
from omniretarget.mujoco.model_state import load_model_state  # noqa: E402
from omniretarget.solver import optimizer as frame_optimizer  # noqa: E402
from omniretarget.solver.frame_problem import FrameProblem  # noqa: E402
from omniretarget.visualization import viser_adapter  # noqa: E402


class InteractionMeshRetargeter:
    """
    A class to perform kinematic retargeting from human motion to a robot,
    preserving spatial relationships using an interaction mesh.
    """

    def __init__(
        self,
        task_constants: ModuleType,
        object_urdf_path: str,
        q_a_init_idx: int = -7,
        activate_foot_sticking: bool = True,
        activate_obj_non_penetration: bool = True,
        activate_joint_limits: bool = True,
        step_size: float = 0.2,
        collision_detection_threshold: float = 0.1,
        penetration_tolerance: float = 1e-3,
        foot_sticking_tolerance: float = 1e-3,
        visualize: bool = False,
        debug: bool = False,
        w_nominal_tracking_init: float = 5.0,
        nominal_tracking_tau: float = 10.0,
    ):
        """This kinematic retargeter solves the diffIK problem with hard constraints in SQP style.
        During each SQP iteration, the problem is solved with the following constraints and costs:
            1. [Cost] Minimize the Laplacian deformation in the object frame.
            2. [Constraint] Enforce the non-penetration constraints w/ the ground and (if activated) the object.
            3. [Constraint] Enforce the foot sticking constraints if activated.
            4. [Constraint] Enforce the joint limits if activated.
            5. [Constraint] Enforce trust region of dq.
        The constraints are linearized and the costs are quadratic with a trust region.

        Args:
            q_a_init_idx: the index in robot's configuration where the optimization variables start. -7: starts from the
            floating base, -3: starts from the translation of the floating base, 0: starts from the actuated DOF,
            12: starts from waist, 15: starts from left shoulder
            step_size: trust region for each SQP iteration.
            collision_detection_threshold: only start to detect collision
            when the distance is smaller than this threshold.
            penetration_tolerance: tolerance for penetration when enforcing non-penetration constraints.
            foot_sticking_tolerance: tolerance for foot sticking constraints in x, y.
            nominal_tracking_tau: the time constant for the nominal tracking cost.
        """

        self.robot_model_path = task_constants.ROBOT_URDF_FILE
        self.object_model_path = object_urdf_path
        self.object_name = task_constants.OBJECT_NAME
        self.collision_detection_threshold = collision_detection_threshold
        self.activate_foot_sticking = activate_foot_sticking
        self.activate_obj_non_penetration = activate_obj_non_penetration
        self.activate_joint_limits = activate_joint_limits
        self.foot_links = dict(zip(task_constants.FOOT_STICKING_LINKS, task_constants.FOOT_STICKING_LINKS))
        self.penetration_tolerance = penetration_tolerance
        self.step_size = step_size
        self.visualize = visualize
        self.debug = debug
        self.demo_joints = task_constants.DEMO_JOINTS
        self.laplacian_match_links = task_constants.JOINTS_MAPPING
        self.task_constants = task_constants

        self.smplh_mapped_joint_indices = [self.demo_joints.index(name) for name in self.laplacian_match_links]

        # Setup weights and parameters
        self.laplacian_weights = 10
        self.smooth_weight = 0.2
        # Tolerance for foot sticking constraints in x, y.
        self.foot_sticking_tolerance = foot_sticking_tolerance

        # Setup visualization if requested
        if self.visualize:
            self._setup_visualization()

        model_state = load_model_state(
            robot_model_path=self.robot_model_path,
            object_name=self.object_name,
            robot_dof=self.task_constants.ROBOT_DOF,
            scene_xml_file=getattr(self.task_constants, "SCENE_XML_FILE", None),
        )
        self.robot_model = model_state.model
        print("Loading robot model from: ", model_state.robot_xml_path)

        self.robot_data = model_state.data
        self.has_dynamic_object = model_state.has_dynamic_object

        self.nq = self.robot_model.nq

        self.q_a_init_idx = q_a_init_idx
        self.q_a_indices = np.arange(7 + self.q_a_init_idx, 7 + self.task_constants.ROBOT_DOF)

        self.nq_a = len(self.q_a_indices)

        # Build per-qpos limits using joint qpos addresses.
        # This is robust when the freejoint is named (e.g., Adam Pro's floating_base),
        # because we no longer assume "all named joints are 1-DoF actuated joints".
        large_number = 1e6
        complete_lower_limits = -large_number * np.ones(self.nq)
        complete_upper_limits = large_number * np.ones(self.nq)
        for joint_id in range(self.robot_model.njnt):
            joint_type = self.robot_model.jnt_type[joint_id]
            qpos_idx = self.robot_model.jnt_qposadr[joint_id]
            if joint_type in (mujoco.mjtJoint.mjJNT_HINGE, mujoco.mjtJoint.mjJNT_SLIDE):
                complete_lower_limits[qpos_idx] = self.robot_model.jnt_range[joint_id, 0]
                complete_upper_limits[qpos_idx] = self.robot_model.jnt_range[joint_id, 1]

        self.q_a_lb = complete_lower_limits[self.q_a_indices].copy()
        self.q_a_ub = complete_upper_limits[self.q_a_indices].copy()

        self.q_a_lb[np.array(list(self.task_constants.MANUAL_LB.keys())).astype(int)] = list(
            self.task_constants.MANUAL_LB.values()
        )
        self.q_a_ub[np.array(list(self.task_constants.MANUAL_UB.keys())).astype(int)] = list(
            self.task_constants.MANUAL_UB.values()
        )

        # Prevent too much waist twist
        self.Q_diag = np.zeros(self.nq_a) * 1e-3
        self.Q_diag[np.array(list(self.task_constants.MANUAL_COST.keys())).astype(int)] = list(
            self.task_constants.MANUAL_COST.values()
        )

        self.w_nominal_tracking_init = w_nominal_tracking_init
        self.nominal_tracking_tau = nominal_tracking_tau
        self.track_nominal_indices = task_constants.NOMINAL_TRACKING_INDICES

    def _setup_visualization(self):
        """Setup Viser visualization components."""
        viser_adapter.setup_visualization(self)

    def draw_mesh_from_geom(self, model, data, geom_id, geom_name, name="/mesh", color=(50, 150, 255), opacity=0.5):
        """
        Draw a single MuJoCo mesh geom (already baked to world coords) in viser.
        color is [0, 255] RGB ints; opacity is [0,1].
        """
        return viser_adapter.draw_mesh_from_geom(self, model, data, geom_id, geom_name, name, color, opacity)

    def draw_mesh_pair_with_contact(
        self,
        model,
        data,
        geom_id1,
        geom_id2,
        geom1_name,
        geom2_name,
        fromto=None,
        group_name="pair",
        color1=(50, 150, 255),
        color2=(255, 120, 60),
        opacity=0.45,
        show_segment=True,
    ):
        """
        Draw two meshes and (optionally) a contact/query segment.
        Uses the existing self.draw_keypoints(...) to visualize points.
        """
        return viser_adapter.draw_mesh_pair_with_contact(
            self,
            model,
            data,
            geom_id1,
            geom_id2,
            geom1_name,
            geom2_name,
            fromto=fromto,
            group_name=group_name,
            color1=color1,
            color2=color2,
            opacity=opacity,
            show_segment=show_segment,
        )

    def retarget_motion(
        self,
        human_joint_motions,
        object_poses,
        object_poses_augmented,
        object_points_local_demo,
        object_points_local,
        foot_sticking_sequences,
        q_a_init=None,
        q_nominal_list=None,
        original=True,
        dest_res_path=None,
    ):
        """
        The main function to retarget an entire motion sequence frame by frame.

        Args:
            human_joint_motions (np.ndarray): (num_frames, num_joints, 3) array.
            object_poses (np.ndarray): (num_frames, 7) array of demo object poses (quat, trans).
            object_poses_augmented (np.ndarray): (num_frames, 7) array of augmented object poses (quat, trans).
            object_points_local_demo (np.ndarray): Demo object points in local frame (rest pose).
            object_points_local (np.ndarray): Current object points in local frame (rest pose).
            foot_sticking_sequences (list): List of foot sticking sequences for each frame.
            q_a_init (np.ndarray, optional): Initial robot configuration.
            q_a_nominal (np.ndarray, optional): Nominal robot configuration.

        Returns:
            tuple: (retargeted_motions, obj_pts_demo_list, obj_pts_list, tetrahedra)
        """
        from omniretarget.solver import trajectory as trajectory_solver

        return trajectory_solver.solve_trajectory(
            self,
            human_joint_motions=human_joint_motions,
            object_poses=object_poses,
            object_poses_augmented=object_poses_augmented,
            object_points_local_demo=object_points_local_demo,
            object_points_local=object_points_local,
            foot_sticking_sequences=foot_sticking_sequences,
            q_a_init=q_a_init,
            q_nominal_list=q_nominal_list,
            original=original,
            dest_res_path=dest_res_path,
        )

    def solve_single_iteration(
        self,
        q_locked: np.ndarray,
        q_a_n_last: np.ndarray,
        q_t_last: np.ndarray,
        target_laplacian: np.ndarray,
        adj_list: list[list[int]],
        obj_pts_local: np.ndarray,
        foot_sticking: tuple[bool, bool],
        w_nominal_tracking: float = 0.0,
        q_a_nominal: np.ndarray | None = None,
        verbose=False,
        init_t=False,
    ):
        """The main function to solve a single iteration of the DiffIK problem.
        Args:
            q_locked: the locked robot and object configuration.
            q_a_n_last: the last optimized robot configuration at current time step.
            q_t_last: the robot and object configuration at the last time step.
            foot_sticking: a sequence of booleans indicating whether the foot [left, right] is sticking to the ground.
            smpl_joints: the (possibly scaled) SMPL joint positions to match for IK.
            q_ref: the reference robot configuration.
            smpl_joints_original: the original SMPL joint positions (used for contact matching).
            obj_original: the original object pose (used for contact matching).
            init_t: the current time step is the first time step.
        """
        solution = frame_optimizer.solve_frame_problem(
            self,
            FrameProblem(
                q_locked=q_locked,
                q_a_n_last=q_a_n_last,
                q_t_last=q_t_last,
                target_laplacian=target_laplacian,
                adj_list=adj_list,
                obj_pts_local=obj_pts_local,
                foot_sticking=foot_sticking,
                w_nominal_tracking=w_nominal_tracking,
                q_a_nominal=q_a_nominal,
                verbose=verbose,
                init_t=init_t,
            ),
        )
        return solution.q, solution.cost

    def _should_enforce_non_penetration_pair(self, pair_key: tuple[int, int]) -> bool:
        """Keep ground constraints always on and gate object constraints by config."""
        return should_enforce_non_penetration_pair(
            pair_key,
            geom_names=getattr(self, "_geom_names", None),
            object_name=self.object_name,
            activate_obj_non_penetration=self.activate_obj_non_penetration,
        )

    def iterate(
        self,
        q_locked: np.ndarray,
        q_n: np.ndarray,
        q_t_last: np.ndarray,
        target_laplacian: np.ndarray,
        adj_list: list[list[int]],
        obj_pts_local: np.ndarray,
        foot_sticking: tuple[bool, bool],
        w_nominal_tracking: float = 0.0,
        q_a_nominal: np.ndarray | None = None,
        init_t: bool = False,
        n_iter: int = 10,
    ):
        """Iterate the solver for multiple iterations."""
        from omniretarget.solver import trajectory as trajectory_solver

        return trajectory_solver.iterate_frame(
            self,
            q_locked=q_locked,
            q_n=q_n,
            q_t_last=q_t_last,
            target_laplacian=target_laplacian,
            adj_list=adj_list,
            obj_pts_local=obj_pts_local,
            foot_sticking=foot_sticking,
            w_nominal_tracking=w_nominal_tracking,
            q_a_nominal=q_a_nominal,
            init_t=init_t,
            n_iter=n_iter,
        )

    def draw_q(self, q: np.ndarray):
        """Draw a single robot configuration."""
        return viser_adapter.draw_q(self, q)

    def draw_keypoints(self, p, name="keypoint", rgba=(0, 0, 1, 1)):
        """Draw keypoints in visualization."""
        return viser_adapter.draw_keypoints(self, p, name=name, rgba=rgba)

    def visualize_motion(
        self,
        human_joint_motions,
        obj_pts_demo,
        obj_pts,
        retargeted_motions,
        tetrahedra,
        dt=1 / 30,
        visualize_tetrahedra=False,
    ):
        return viser_adapter.visualize_motion(
            self,
            human_joint_motions,
            obj_pts_demo,
            obj_pts,
            retargeted_motions,
            tetrahedra,
            dt=dt,
            visualize_tetrahedra=visualize_tetrahedra,
        )

    def visualize_tetrahedra(self, vertices, tetrahedra, name="tetrahedra", color=(0, 0, 0, 1)):
        return viser_adapter.visualize_tetrahedra(self, vertices, tetrahedra, name=name, color=color)

    def _compute_jacobian_for_contact_relative(self, geom1, geom2, geom1_name, geom2_name, fromto, dist):
        # Get closest points from fromto buffer
        pos1 = fromto[:3]  # closest point on geom1
        pos2 = fromto[3:]  # closest point on geom2

        v = pos1 - pos2
        norm_v = np.linalg.norm(v)

        if norm_v > 1e-12:
            nhat_BA_W = np.sign(dist) * (v / norm_v)
        # Degenerate: points coincide. Heuristics fallback.
        # If one side is a plane/ground, use its known normal.
        elif "ground" in geom2_name.lower():
            nhat_BA_W = np.array([0.0, 0.0, 1.0]) * (1.0 if dist >= 0 else -1.0)
        elif "ground" in geom1_name.lower():
            nhat_BA_W = np.array([0.0, 0.0, -1.0]) * (1.0 if dist >= 0 else -1.0)
        else:
            nhat_BA_W = np.array([0.0, 0.0, 0.0])

        J_bodyA = self._calc_contact_jacobian_from_point(geom1.bodyid, pos1, input_world=True)
        J_bodyB = self._calc_contact_jacobian_from_point(geom2.bodyid, pos2, input_world=True)

        # Compute relative Jacobian
        Jc = J_bodyA - J_bodyB

        return nhat_BA_W @ Jc

    def _prefilter_pairs_with_mj_collision(self, threshold: float):
        self._geom_names = geometry_names(self.robot_model)
        return prefilter_pairs_with_mj_collision(self.robot_model, self.robot_data, threshold)

    def _update_jacobians_and_phis_from_q(self, q: np.ndarray):
        self.robot_data.qpos[:] = q

        mujoco.mj_forward(self.robot_model, self.robot_data)  # kinematics & AABBs valid

        m, d = self.robot_model, self.robot_data
        threshold = float(self.collision_detection_threshold)

        # 1) Fast prefilter via mj_collision with temporary margins
        candidates = self._prefilter_pairs_with_mj_collision(threshold)

        Js, phis = {}, {}
        # 2) Precise distance only on candidates (early-exit at threshold)
        for g1, g2 in candidates:
            # Optional: keep your own filters here (e.g., skip object-ground, only keep interaction with object/ground)
            if not geom_pair_allowed_for_object_or_ground(m, self._geom_names, self.object_name, g1, g2):
                continue

            dist, fromto = geom_distance(m, d, g1, g2, threshold)
            if dist <= threshold:
                J_rel = self._compute_jacobian_for_contact_relative(
                    m.geom(g1), m.geom(g2), self._geom_names[g1], self._geom_names[g2], fromto, dist
                )
                Js[(g1, g2)] = J_rel
                phis[(g1, g2)] = float(dist)

                # For debug
                # self.draw_mesh_pair_with_contact(self.robot_model, self.robot_data, g1, g2,   \
                #     self._geom_names[g1], self._geom_names[g2], fromto=fromto)

        return Js, phis

    def _world_to_body_frame(self, p_w: np.ndarray, body_idx: int) -> np.ndarray:
        """Transform point from world frame to body frame."""
        return world_to_body_frame(self.robot_data, p_w, body_idx)

    def _get_geometry_name(self, geom_id: int) -> str:
        """Get geometry name from ID."""
        return geometry_name(self.robot_model, geom_id)

    def _build_transform_qdot_to_qvel_fast(self, use_world_omega=True):
        """
        Return T(q) (nv x nq) such that v = T(q) @ qdot.
        - Free root: qpos=[x,y,z, qw,qx,qy,qz], qvel=[vx,vy,vz, ωx,ωy,ωz]
        where ω and v are WORLD-expressed in MuJoCo.
        - 23 hinge joints: v = qdot.

        If use_world_omega=False, uses BODY-omega mapping (for debugging).
        """
        return qdot_to_qvel_transform(
            self.robot_model,
            self.robot_data,
            has_dynamic_object=self.has_dynamic_object,
            use_world_omega=use_world_omega,
        )

    def _calc_contact_jacobian_from_point(self, body_idx: int, p_body: np.ndarray, input_world=False):
        """
        Translational Jacobian J(q) (3 x nq) such that
        v_point_world = J(q) @ qdot.

        Fast analytic version: J_qdot = J_v @ T(q)
        """

        return point_jacobian_qpos(
            self.robot_model,
            self.robot_data,
            body_idx,
            p_body,
            input_world=input_world,
            has_dynamic_object=self.has_dynamic_object,
        )

    def _calc_manipulator_jacobians(
        self,
        q: np.ndarray,
        links: dict[str, str],
        obj_frame: bool = False,
        point_offsets: np.ndarray | None = None,
    ):
        """Compute position-based Jacobians using MuJoCo."""
        J_XC_dict = {}
        p_XC_dict = {}

        if obj_frame:
            if self.has_dynamic_object:
                obj_quat = q[-4:]
                obj_pos = q[-7:-4]
                obj_rot = Rotation.from_quat([obj_quat[1], obj_quat[2], obj_quat[3], obj_quat[0]]).as_matrix()
                obj_rot_inv = obj_rot.T
            else:
                obj_rot = Rotation.from_quat([0, 0, 0, 1]).as_matrix()
                obj_rot_inv = obj_rot.T
                obj_pos = np.zeros(3)

        q_mujoco = q.copy()
        self.robot_data.qpos[:] = q_mujoco

        mujoco.mj_forward(self.robot_model, self.robot_data)

        for name, link_name in links.items():
            body_idx = body_id(self.robot_model, link_name)

            if point_offsets is not None:
                pC_B = point_offsets
            else:
                pC_B = np.zeros(3)

            J = self._calc_contact_jacobian_from_point(body_idx, pC_B)
            pos_world = self.robot_data.xpos[body_idx]

            if obj_frame:
                p_XC = obj_rot_inv @ (pos_world - obj_pos)
                J_XC = obj_rot_inv @ J
            else:
                p_XC = pos_world
                J_XC = J

            # Store reduced Jacobian and position with hard copies to avoid aliasing
            J_XC_dict[name] = np.array(J_XC[:, self.q_a_indices], dtype=float, copy=True)  # FIX (copy)
            p_XC_dict[name] = np.array(p_XC, dtype=float, copy=True)

        P_WO = {"position": obj_pos, "rotation": obj_rot} if obj_frame else None

        return J_XC_dict, p_XC_dict, P_WO

    def _get_robot_link_positions(self, q, link_names):
        """Get robot link positions for given configuration using Mujoco."""
        return link_positions(
            self.robot_model,
            self.robot_data,
            q,
            link_names,
            allow_trailing_dynamic_object=True,
        )
