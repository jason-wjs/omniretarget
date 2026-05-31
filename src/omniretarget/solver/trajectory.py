from __future__ import annotations

from pathlib import Path

import numpy as np
from tqdm import tqdm

from omniretarget.solver.interaction_mesh import build_interaction_mesh_frame
from omniretarget.visualization.viser_adapter import add_motion_controls


def iterate_frame(
    retargeter,
    *,
    q_locked: np.ndarray,
    q_n: np.ndarray,
    q_t_last: np.ndarray,
    target_laplacian: np.ndarray,
    adj_list: list[list[int]],
    obj_pts_local: np.ndarray,
    foot_sticking,
    w_nominal_tracking: float = 0.0,
    q_a_nominal: np.ndarray | None = None,
    init_t: bool = False,
    n_iter: int = 10,
):
    """Run the per-frame SQP loop through the retargeter facade."""
    last_cost = np.inf
    cost = np.inf
    for _ in range(n_iter):
        q_a_n_last = q_n[retargeter.q_a_indices]
        q_n, cost = retargeter.solve_single_iteration(
            q_locked=q_locked,
            q_a_n_last=q_a_n_last,
            q_t_last=q_t_last,
            target_laplacian=target_laplacian,
            adj_list=adj_list,
            obj_pts_local=obj_pts_local,
            foot_sticking=foot_sticking,
            q_a_nominal=q_a_nominal,
            w_nominal_tracking=w_nominal_tracking,
            init_t=init_t,
        )
        if np.isclose(cost, last_cost):
            break
        last_cost = cost
    return q_n, cost


def solve_trajectory(
    retargeter,
    *,
    human_joint_motions,
    object_poses,
    object_poses_augmented,
    object_points_local_demo,
    object_points_local,
    foot_sticking_sequences,
    q_a_init=None,
    q_nominal_list=None,
    original=True,
    dest_res_path: str | Path | None = None,
):
    """Retarget an entire motion sequence through the InteractionMeshRetargeter facade."""
    num_frames = human_joint_motions.shape[0]
    if q_nominal_list is not None:
        q_locked_list = q_nominal_list
    else:
        q_locked_list = np.zeros((num_frames, retargeter.nq))
        q_locked_list[0, retargeter.q_a_indices] = q_a_init

    if retargeter.has_dynamic_object:
        q_locked_list[:, -7:] = object_poses_augmented
    q = np.copy(q_locked_list[0])
    retargeted_motions = [q]

    tetrahedra = []
    obj_pts_demo_list = []
    obj_pts_list = []
    human_kpts_handle_list = []
    obj_kpts_demo_handle_list = []
    obj_kpts_handle_list = []
    robot_kpts_handle_list = []
    cost = np.nan

    print(f"\nStarting motion retargeting for {num_frames} frames...")

    with tqdm(range(num_frames)) as pbar:
        for i in pbar:
            human_mapped_joints = human_joint_motions[i, retargeter.smplh_mapped_joint_indices]
            frame = build_interaction_mesh_frame(
                object_name=retargeter.object_name,
                human_mapped_joints=human_mapped_joints,
                object_pose_demo=object_poses[i],
                object_pose_augmented=object_poses_augmented[i],
                object_points_local_demo=object_points_local_demo,
                object_points_local=object_points_local,
                include_debug_points=retargeter.debug,
            )
            tetrahedra.append(frame.source_tetrahedra)

            if retargeter.debug:
                obj_pts_demo_list.append(frame.object_points_demo_world)
                obj_pts_list.append(frame.object_points_world)
                human_kpts_handle_list = retargeter.draw_keypoints(human_mapped_joints, name="human_kpts")
                obj_kpts_demo_handle_list = retargeter.draw_keypoints(
                    frame.object_points_demo_world,
                    name="object_demo_kpts",
                    rgba=(1, 0, 0, 1),
                )
                obj_kpts_handle_list = retargeter.draw_keypoints(
                    frame.object_points_world,
                    name="object_kpts",
                    rgba=(0, 1, 1, 1),
                )

            if original:
                w_nominal_tracking = retargeter.w_nominal_tracking_init
            else:
                w_nominal_tracking = retargeter.w_nominal_tracking_init * np.exp(-i / retargeter.nominal_tracking_tau)

            q, cost = retargeter.iterate(
                q_locked=q_locked_list[i],
                q_n=q,
                q_t_last=retargeted_motions[-1],
                target_laplacian=frame.target_laplacian,
                adj_list=frame.adj_list,
                obj_pts_local=object_points_local,
                foot_sticking=foot_sticking_sequences[i],
                w_nominal_tracking=w_nominal_tracking,
                q_a_nominal=(q_nominal_list[i, retargeter.q_a_indices] if q_nominal_list is not None else None),
                init_t=i == 0,
                n_iter=50 if i == 0 else 10,
            )
            if retargeter.debug:
                robot_link_positions = retargeter._get_robot_link_positions(
                    q,
                    retargeter.laplacian_match_links.values(),
                )
                robot_kpts_handle_list = retargeter.draw_keypoints(
                    robot_link_positions,
                    name="robot_kpts",
                    rgba=(0, 1, 0, 1),
                )

            retargeted_motions.append(q)
            if retargeter.visualize and retargeter.debug:
                retargeter.draw_q(q)

            pbar.set_postfix(cost=cost)

    if retargeter.debug:
        for handle_list in (
            human_kpts_handle_list,
            obj_kpts_demo_handle_list,
            obj_kpts_handle_list,
            robot_kpts_handle_list,
        ):
            for handle in handle_list:
                handle.remove()
            handle_list.clear()

    np.savez(
        dest_res_path,
        qpos=np.array(retargeted_motions)[1:],
        human_joints=human_joint_motions,
        fps=30,
        cost=cost,
    )
    print("Saving results to path:", dest_res_path)

    if retargeter.visualize:
        add_motion_controls(retargeter, retargeted_motions)

    return (
        np.array(retargeted_motions)[1:],
        obj_pts_demo_list,
        obj_pts_list,
        tetrahedra,
    )
