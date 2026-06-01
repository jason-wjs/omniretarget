from __future__ import annotations

import pickle

import numpy as np
import smplx  # type: ignore[import-not-found]
import torch
from scipy.spatial.transform import Rotation as R  # type: ignore[import-untyped]  # noqa: N817

from omniretarget.path_utils import package_path


def load_intermimic_data(file_path):
    """
    Load and preprocess InterMimic data.

    Args:
        file_path (str): Path to the .pt file.

    Returns:
        tuple: (human_joints, object_poses) - processed data.
    """
    intermimic_data = torch.load(file_path, map_location="cpu").detach().numpy()
    human_joints = intermimic_data[:, 162 : 162 + 52 * 3].reshape(-1, 52, 3)
    # Reorder quaternion from [qx, qy, qz, qw] to [qw, qx, qy, qz]
    object_poses = intermimic_data[:, 318:325][:, [6, 3, 4, 5, 0, 1, 2]]
    return human_joints, object_poses


def calculate_scale_factor(task_name, robot_height):
    """Calculate scale factor based on human height."""
    with package_path("demo_data/height_dict.pkl").open("rb") as f:
        height_dict = pickle.load(f)
    sub_name = task_name.split("_")[0]
    human_height = height_dict[sub_name]
    return robot_height / human_height


def preprocess_motion_data(
    human_joints,
    retargeter,
    foot_names,
    scale=0.714,
    mat_height=0.1,
    ground_height_percentile=0.0,
    normalize_height=True,
    object_poses=None,
):
    """
    Preprocess human joints and object poses for retargeting.

    Args:
        human_joints (np.ndarray): Human joint positions.
        object_poses (np.ndarray): Object poses.
        retargeter: Retargeting object with smplh_joint2idx attribute.
        scale (float): Scaling factor.
        normalize_height (bool): Whether to normalize human joint heights from toe contacts.

    Returns:
        tuple: (human_joints_scaled, object_poses_scaled, object_moving_frame_idx).
    """
    if normalize_height:
        toe_indices = [
            retargeter.demo_joints.index(foot_names[0]),
            retargeter.demo_joints.index(foot_names[1]),
        ]
        toe_heights = human_joints[:, toe_indices, 2].reshape(-1)
        if ground_height_percentile > 0:
            # Use "higher" to avoid interpolation pulling the floor down from sparse outliers.
            try:
                z_min = float(np.percentile(toe_heights, ground_height_percentile, method="higher"))
            except TypeError:
                z_min = float(np.percentile(toe_heights, ground_height_percentile, interpolation="higher"))
        else:
            z_min = float(toe_heights.min())

        if z_min >= mat_height:
            # On a mat.
            z_min -= mat_height
        human_joints[:, :, 2] -= z_min

    # Scale human joints
    human_joints = human_joints * scale

    if object_poses is not None:
        object_poses[:, -3:-1] = object_poses[:, -3:-1] * scale
        object_z0 = object_poses[0, -1]
        dz_scale = (object_poses[:, -1] - object_z0) * scale
        object_poses[:, -1] = object_z0 + dz_scale

        object_moving_frame_idx = extract_object_first_moving_frame(object_poses)

        return human_joints, object_poses, object_moving_frame_idx

    return human_joints


def extract_object_first_moving_frame(object_poses, vel_threshold=0.0025):
    """Extract the first frame where the object starts moving."""
    object_vel = np.diff(object_poses, axis=0)
    object_vel_norm = np.linalg.norm(object_vel, axis=1)
    return np.argmax(object_vel_norm > vel_threshold)


def extract_foot_sticking_sequence(smpl_joints, demo_joints, foot_names, smpl_contact_threshold_relative=0.01):
    """
    Extract contact sequence from SMPL joint data.

    Args:
        smpl_joints (np.ndarray): SMPL joint positions.
        smplh_joint2idx (dict): Mapping from joint names to indices.
        smpl_contact_threshold_relative (float): The foot is in the air if z is
        larger than z_min + smpl_contact_threshold_relative.

    Returns:
        list: List of contact dictionaries for each frame.
    """
    z_L_min = smpl_joints[:, demo_joints.index(foot_names[0]), 2].min()
    z_R_min = smpl_joints[:, demo_joints.index(foot_names[1]), 2].min()

    return [
        {
            foot_names[0]: smpl_joints_i[demo_joints.index(foot_names[0]), 2]
            <= z_L_min + smpl_contact_threshold_relative,
            foot_names[1]: smpl_joints_i[demo_joints.index(foot_names[1]), 2]
            <= z_R_min + smpl_contact_threshold_relative,
        }
        for smpl_joints_i in smpl_joints
    ]


def find_standing_pose(q: np.ndarray):
    """Find standing pose from current configuration q."""
    q_standing = np.copy(q)
    # rpy_vector = RollPitchYaw(Quaternion(q[:4])).vector()
    # standing_quat = RollPitchYaw(0, 0, rpy_vector[2]).ToQuaternion()
    # quat = standing_quat.wxyz()
    # if np.dot(quat, q[:4]) < 0:
    #     quat = -quat
    # q_standing[:4] = quat
    # q_standing[6] = 0.76  # slightly shorter than the height of G1 pelvis due to bending
    # q_standing[7 : 7 + 29] = Q_A_STANDING
    q_standing[19:22] = 0.0
    return q_standing


def load_smpl_motion(model_path, motion_file):
    """
    Loads SMPL model and motion data, then computes joint positions.

    Args:
        model_path (str): Path to the SMPL model directory.
        motion_file (str): Path to the .npz motion file (AMASS format).

    Returns:
        numpy.ndarray: A (num_frames, num_joints, 3) array of 3D joint positions.
        smplx.SMPL: The loaded SMPL model object.
    """
    print("Loading SMPL model and motion...")
    model = smplx.SMPL(model_path=model_path, gender="neutral", ext="pkl").to("cpu")
    motion_data = np.load(motion_file)

    num_frames = motion_data["poses"].shape[0]
    body_pose = torch.from_numpy(motion_data["poses"][:, 3:]).float()
    global_orient = torch.from_numpy(motion_data["poses"][:, :3]).float()
    betas = torch.from_numpy(motion_data["betas"][:1, :]).float().repeat(num_frames, 1)
    trans = torch.from_numpy(motion_data["trans"]).float()

    output = model(betas=betas, body_pose=body_pose, global_orient=global_orient, transl=trans)
    return output.joints.detach().numpy(), model


def extract_foot_sticking_sequence_velocity(smpl_joints, demo_joints, foot_names, velocity_threshold=0.01):
    """
    Extract contact sequence from SMPL joint data based on x,y velocity of toe joints.

    Args:
        smpl_joints (np.ndarray): SMPL joint positions of shape (T, N, 3).
        demo_joints (list): List of joint names.
        foot_names (list): List of foot joint names [left_foot, right_foot].
        velocity_threshold (float): Threshold for xy velocity to determine contact.

    Returns:
        list: List of contact dictionaries for each frame.
    """

    left_toe_idx = demo_joints.index(foot_names[0])
    right_toe_idx = demo_joints.index(foot_names[1])

    # Check xy velocities
    left_toe_positions = smpl_joints[:, left_toe_idx, :2]
    right_toe_positions = smpl_joints[:, right_toe_idx, :2]

    left_toe_velocity = np.linalg.norm(np.diff(left_toe_positions, axis=0), axis=1)
    right_toe_velocity = np.linalg.norm(np.diff(right_toe_positions, axis=0), axis=1)

    left_toe_velocity = np.concatenate([[velocity_threshold + 1], left_toe_velocity])
    right_toe_velocity = np.concatenate([[velocity_threshold + 1], right_toe_velocity])

    return [
        {
            foot_names[0]: left_toe_velocity[i] <= velocity_threshold,
            foot_names[1]: right_toe_velocity[i] <= velocity_threshold,
        }
        for i in range(len(smpl_joints))
    ]


def transform_y_up_to_z_up(points):
    """
    Transform points from y-up to z-up coordinate system.

    Transformation:
    - Y-axis (up) becomes Z-axis (up)
    - Z-axis (forward) becomes Y-axis (forward)
    - X-axis (right) stays X-axis (right)

    Args:
        points (np.ndarray): Points with shape (..., 3) where last dimension is [x, y, z]

    Returns:
        np.ndarray: Transformed points with shape (..., 3) where last dimension is [x, y, z]
    """
    # Create transformation matrix
    # [x, y, z] -> [x, z, y]
    transform_matrix = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]])

    # Apply transformation
    if points.ndim == 1:
        return transform_matrix @ points
    if points.ndim == 2:
        return (transform_matrix @ points.T).T
    if points.ndim == 3:
        original_shape = points.shape
        points_reshaped = points.reshape(-1, 3)
        transformed = (transform_matrix @ points_reshaped.T).T
        return transformed.reshape(original_shape)
    raise ValueError(f"Unsupported number of dimensions: {points.ndim}")


def estimate_human_orientation(human_joints, joint_names, frame_idx=0):
    """
    Estimate the human's global orientation quaternion based on joint positions.

    This function estimates the human's orientation by looking at the direction
    from the pelvis (Hips) to the spine/chest, and the direction from left to right hip.

    Args:
        human_joints (np.ndarray): Human joint positions with shape (frames, joints, 3)
        joint_names (list): List of joint names corresponding to the joint positions
        frame_idx (int): Frame index to estimate orientation from (default: 0)

    Returns:
        np.ndarray: Quaternion [w, x, y, z] representing the human's global orientation
    """
    # For LAFAN
    if "Hips" in joint_names:
        hips_idx = joint_names.index("Hips")
        spine_idx = joint_names.index("Spine")
        left_hip_idx = joint_names.index("LeftUpLeg")
        right_hip_idx = joint_names.index("RightUpLeg")
    else:
        # For SMPLH (OMOMO_new)
        hips_idx = joint_names.index("Pelvis")
        spine_idx = joint_names.index("Spine")
        left_hip_idx = joint_names.index("L_Hip")
        right_hip_idx = joint_names.index("R_Hip")

    hips_pos = human_joints[frame_idx, hips_idx]
    spine_pos = human_joints[frame_idx, spine_idx]
    left_hip_pos = human_joints[frame_idx, left_hip_idx]
    right_hip_pos = human_joints[frame_idx, right_hip_idx]

    # Calculate forward direction (from hips to spine)
    forward_vec = hips_pos - spine_pos
    forward_vec[2] = 0  # Project to horizontal plane (ignore vertical component)
    if np.linalg.norm(forward_vec) > 1e-6:
        forward_vec = forward_vec / np.linalg.norm(forward_vec)
    else:
        # If spine is directly above hips, use a default forward direction
        forward_vec = np.array([0, 1, 0])

    # Calculate right direction (from left hip to right hip)
    left_vec = left_hip_pos - right_hip_pos
    left_vec[2] = 0  # Project to horizontal plane
    if np.linalg.norm(left_vec) > 1e-6:
        left_vec = left_vec / np.linalg.norm(left_vec)
    else:
        # If hips are aligned vertically, use a default right direction
        left_vec = np.array([1, 0, 0])

    # Ensure left_vec is perpendicular to forward_vec
    left_vec = left_vec - np.dot(left_vec, forward_vec) * forward_vec
    if np.linalg.norm(left_vec) > 1e-6:
        left_vec = left_vec / np.linalg.norm(left_vec)
    else:
        # Fallback if vectors are parallel
        left_vec = np.array([1, 0, 0])

    # Calculate up direction (cross product to ensure orthogonality)
    up_vec = np.cross(forward_vec, left_vec)
    up_vec = up_vec / np.linalg.norm(up_vec)
    forward_vec = np.cross(left_vec, up_vec)
    forward_vec = forward_vec / np.linalg.norm(forward_vec)

    rotation_matrix = np.column_stack([forward_vec, left_vec, up_vec])
    assert np.linalg.det(rotation_matrix) > 0
    rotation = R.from_matrix(rotation_matrix)
    return rotation.as_quat(scalar_first=True)
