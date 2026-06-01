from __future__ import annotations

import time

import numpy as np
import trimesh
import viser  # type: ignore[import-not-found]
import yourdfpy  # type: ignore[import-untyped]
from viser.extras import ViserUrdf  # type: ignore[import-not-found]

from omniretarget.mujoco.assets import world_mesh_from_geom
from omniretarget.visualization.playback import create_motion_control_sliders


def setup_visualization(retargeter) -> None:
    """Setup legacy Viser visualization components on retargeter."""
    retargeter.server = viser.ViserServer()

    try:
        retargeter.server.scene.add_frame("/world", show_axes=False)
    except Exception:
        print("Starting viser")

    retargeter.robot_base = retargeter.server.scene.add_frame("/world/robot", show_axes=False)

    print("robot_model_path: ", retargeter.robot_model_path)

    retargeter.robot_urdf = yourdfpy.URDF.load(
        retargeter.robot_model_path,
        load_meshes=True,
        build_scene_graph=True,
    )

    print("Viser using robot URDF: ", retargeter.robot_model_path)

    retargeter.viser_robot = ViserUrdf(
        retargeter.server,
        urdf_or_path=retargeter.robot_urdf,
        root_node_name="/world/robot",
    )

    if retargeter.object_model_path:
        retargeter.object_base = retargeter.server.scene.add_frame("/world/object", show_axes=False)

        retargeter.object_urdf = yourdfpy.URDF.load(
            retargeter.object_model_path,
            load_meshes=True,
            build_scene_graph=True,
        )

        retargeter.viser_object = ViserUrdf(
            retargeter.server,
            urdf_or_path=retargeter.object_urdf,
            root_node_name="/world/object",
        )
        print("Viser using object URDF: ", retargeter.object_model_path)
    else:
        retargeter.viser_object = None

    robot_joint_limits = retargeter.viser_robot.get_actuated_joint_limits()
    print("\nRobot joints:")
    print("Number of actuated joints:", len(robot_joint_limits))
    print("Joint names:", list(robot_joint_limits.keys()))

    robot_initial_config = np.zeros(len(robot_joint_limits))
    retargeter.viser_robot.update_cfg(robot_initial_config)

    retargeter.server.scene.add_grid(
        "/world/grid",
        width=8,
        height=8,
        position=(0.0, 0.0, 0.0),
    )


def draw_mesh_from_geom(retargeter, model, data, geom_id, geom_name, name="/mesh", color=(50, 150, 255), opacity=0.5):
    """Draw a single MuJoCo mesh geom in Viser."""
    if not hasattr(retargeter, "server"):
        return
    vertices, faces = world_mesh_from_geom(model, data, geom_id, geom_name)
    retargeter.server.scene.add_mesh_simple(
        name,
        vertices=vertices.astype(np.float32),
        faces=faces.astype(np.int32),
        position=(0.0, 0.0, 0.0),
        color=tuple(int(c) for c in color),
        opacity=float(opacity),
    )


def draw_mesh_pair_with_contact(
    retargeter,
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
    """Draw two mesh geoms and optional contact/query points."""
    _ = show_segment
    if int(model.geom_dataid[geom_id1]) == -1 or int(model.geom_dataid[geom_id2]) == -1:
        return

    base = f"/{group_name}"
    draw_mesh_from_geom(retargeter, model, data, geom_id1, geom1_name, name=f"{base}/mesh1", color=color1, opacity=opacity)
    draw_mesh_from_geom(retargeter, model, data, geom_id2, geom2_name, name=f"{base}/mesh2", color=color2, opacity=opacity)

    if fromto is not None:
        q = np.asarray(fromto[:3], dtype=float)
        c = np.asarray(fromto[3:], dtype=float)
        retargeter.draw_keypoints(q, name=f"{group_name}_q", rgba=(0.0, 1.0, 0.0, 1.0))
        retargeter.draw_keypoints(c, name=f"{group_name}_c", rgba=(1.0, 0.0, 0.0, 1.0))


def draw_q(retargeter, q: np.ndarray) -> None:
    """Draw a single robot configuration."""
    robot_joint_positions = q[7 : 7 + retargeter.task_constants.ROBOT_DOF]
    retargeter.viser_robot.update_cfg(robot_joint_positions)

    retargeter.robot_base.position = q[:3]
    retargeter.robot_base.wxyz = q[3:7]

    if hasattr(retargeter, "viser_object") and retargeter.viser_object is not None:
        if retargeter.has_dynamic_object:
            object_quat = q[-4:]
            object_pos = q[-7:-4]
        else:
            object_quat = np.asarray([1, 0, 0, 0])
            object_pos = np.zeros(3)

        retargeter.object_base.position = object_pos
        retargeter.object_base.wxyz = object_quat


def draw_keypoints(retargeter, p, name="keypoint", rgba=(0, 0, 1, 1)):
    """Draw one or more keypoints in Viser."""
    if not hasattr(retargeter, "server"):
        return None

    sphere = trimesh.primitives.Sphere(radius=0.02)
    vertices = sphere.vertices
    faces = sphere.faces

    color = tuple(int(c * 255) for c in rgba[:3])
    opacity = float(rgba[3])

    kpts_handle_list = []

    if len(p.shape) == 1:
        kpts_handle = retargeter.server.scene.add_mesh_simple(
            f"/{name}",
            vertices=vertices,
            faces=faces,
            position=p,
            color=color,
            opacity=opacity,
        )
        kpts_handle_list.append(kpts_handle)
    elif len(p.shape) == 2:
        kpts_handle = retargeter.server.scene.add_batched_meshes_simple(
            f"/{name}",
            vertices=vertices,
            faces=faces,
            batched_positions=p,
            batched_wxyzs=np.tile(np.array([1, 0, 0, 0]), (p.shape[0], 1)),
            batched_colors=color,
            opacity=opacity,
        )
        kpts_handle_list.append(kpts_handle)

    return kpts_handle_list


def visualize_motion(
    retargeter,
    human_joint_motions,
    obj_pts_demo,
    obj_pts,
    retargeted_motions,
    tetrahedra,
    dt=1 / 30,
    visualize_tetrahedra=False,
) -> None:
    """Visualize a retargeted motion with the legacy debug viewer."""
    for i in range(len(human_joint_motions)):
        object_pts_demo = obj_pts_demo[i]
        object_pts = obj_pts[i]
        retargeter.draw_keypoints(human_joint_motions[i, retargeter.smplh_mapped_joint_indices], name="human")
        retargeter.draw_keypoints(object_pts_demo, name="object_demo", rgba=(1, 0, 0, 1))
        retargeter.draw_keypoints(object_pts, name="object", rgba=(0, 1, 0, 1))
        retargeter.draw_q(retargeted_motions[i])
        robot_link_positions = retargeter._get_robot_link_positions(
            retargeted_motions[i],
            retargeter.laplacian_match_links.values(),
        )
        retargeter.draw_keypoints(robot_link_positions, name="robot", rgba=(0, 1, 0, 1))
        input()
        if visualize_tetrahedra:
            retargeter.visualize_tetrahedra(
                np.vstack(
                    [
                        human_joint_motions[i, retargeter.smplh_mapped_joint_indices],
                        object_pts_demo,
                    ]
                ),
                tetrahedra[i],
                name="human_tetrahedra",
            )
            retargeter.visualize_tetrahedra(
                np.vstack([robot_link_positions, object_pts]),
                tetrahedra[i],
                name="robot_tetrahedra",
                rgba=(0, 1, 1, 1),
            )
        else:
            time.sleep(dt)


def visualize_tetrahedra(retargeter, vertices, tetrahedra, name="tetrahedra", color=(0, 0, 0, 1)) -> None:
    """Draw tetrahedra edges as line segments."""
    color_255 = np.array(color[:3]) * 255
    points = []
    colors = []

    for tet in tetrahedra:
        for i in range(4):
            for j in range(i + 1, 4):
                u, v = tet[i], tet[j]
                points.extend([vertices[u], vertices[v]])
                colors.extend([color_255, color_255])

    retargeter.server.scene.add_line_segments(
        f"/{name}",
        points=np.array(points),
        colors=np.array(colors),
        line_width=0.01,
    )


def add_motion_controls(retargeter, retargeted_motions: list[np.ndarray]) -> None:
    """Attach the legacy Viser playback controls for a retargeted trajectory."""
    robot_dof = len(retargeter.viser_robot.get_actuated_joint_limits())

    create_motion_control_sliders(
        server=retargeter.server,
        viser_robot=retargeter.viser_robot,
        robot_base_frame=retargeter.robot_base,
        motion_sequence=np.asarray(retargeted_motions)[1:],
        robot_dof=robot_dof,
        viser_object=retargeter.viser_object,
        object_base_frame=getattr(retargeter, "object_base", None) if retargeter.viser_object else None,
        contains_object_in_qpos=bool(retargeter.viser_object) and bool(retargeter.has_dynamic_object),
        initial_fps=30,
        initial_interp_mult=2,
        loop=False,
    )

    with retargeter.server.gui.add_folder("Visibility"):
        show_meshes_cb = retargeter.server.gui.add_checkbox("Show meshes", retargeter.viser_robot.show_visual)

        @show_meshes_cb.on_update
        def _(_) -> None:
            retargeter.viser_robot.show_visual = show_meshes_cb.value
            if retargeter.viser_object is not None:
                retargeter.viser_object.show_visual = show_meshes_cb.value
