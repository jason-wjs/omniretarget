"""Contact extraction helpers for utility-layer decomposition."""

from __future__ import annotations

import numpy as np


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
