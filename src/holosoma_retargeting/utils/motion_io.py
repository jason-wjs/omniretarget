"""Motion-loading helpers for utility-layer decomposition."""

from __future__ import annotations

import numpy as np
import torch


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
    import smplx  # type: ignore[import-not-found]

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
