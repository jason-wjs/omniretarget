from __future__ import annotations

import logging
import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from omniretarget.config_types.retargeter import RetargeterConfig
from omniretarget.config_types.retargeting import RetargetingConfig
from omniretarget.config_types.robot import RobotConfig
from omniretarget.config_types.data_type import MotionDataConfig
from omniretarget.retargeting.initialization import initialize_robot_pose
from omniretarget.retargeting.motion_source import load_motion_data
from omniretarget.retargeting.object_setup import setup_object_data
from omniretarget.retargeting.preprocessing import build_foot_sticking_sequences, preprocess_retargeting_motion
from omniretarget.retargeting.results import determine_output_path
from omniretarget.retargeter import InteractionMeshRetargeter
from omniretarget.runtime.context import build_runtime_context
from omniretarget.runtime.validation import validate_retargeting_config

logger = logging.getLogger(__name__)

DEFAULT_DATA_FORMATS = {
    "robot_only": "smplh",
    "object_interaction": "smplh",
    "climbing": "mocap",
}

DEFAULT_SAVE_DIRS = {
    "robot_only": "demo_results/{robot}/robot_only/omomo",
    "object_interaction": "demo_results/{robot}/object_interaction/omomo",
    "climbing": "demo_results/{robot}/climbing/mocap_climb",
}

_OBJECT_SCALE_AUGMENTED = np.array([1.0, 1.0, 1.2])
_AUGMENTATION_TRANSLATION = np.array([0.2, 0.0, 0.0])


def build_retargeter_kwargs_from_config(
    retargeter_config: RetargeterConfig,
    constants: SimpleNamespace,
    object_urdf_path: str | None,
    task_type: str,
) -> dict:
    """Build kwargs for InteractionMeshRetargeter from a RetargeterConfig."""
    kwargs = {
        "task_constants": constants,
        "object_urdf_path": object_urdf_path,
        "q_a_init_idx": retargeter_config.q_a_init_idx,
        "activate_joint_limits": retargeter_config.activate_joint_limits,
        "activate_obj_non_penetration": retargeter_config.activate_obj_non_penetration,
        "activate_foot_sticking": retargeter_config.activate_foot_sticking,
        "penetration_tolerance": retargeter_config.penetration_tolerance,
        "foot_sticking_tolerance": retargeter_config.foot_sticking_tolerance,
        "step_size": retargeter_config.step_size,
        "visualize": retargeter_config.visualize,
        "debug": retargeter_config.debug,
        "w_nominal_tracking_init": retargeter_config.w_nominal_tracking_init,
    }
    if task_type == "climbing":
        kwargs["nominal_tracking_tau"] = retargeter_config.nominal_tracking_tau
    return kwargs


def run_single_retargeting(cfg: RetargetingConfig) -> None:
    """Run the single-clip retargeting workflow."""
    validate_retargeting_config(cfg)

    robot = cfg.robot
    task_name = cfg.task_name
    task_type = cfg.task_type

    data_format: str = cfg.data_format or DEFAULT_DATA_FORMATS[task_type]
    save_dir = cfg.save_dir if cfg.save_dir is not None else Path(DEFAULT_SAVE_DIRS[task_type].format(robot=robot))
    data_path = cfg.data_path

    os.makedirs(save_dir, exist_ok=True)
    logger.info("Task: %s, Type: %s, Format: %s", task_name, task_type, data_format)
    logger.info("Data path: %s, Save dir: %s", data_path, save_dir)

    if cfg.robot_config.robot_type != robot:
        cfg.robot_config = RobotConfig(robot_type=robot)

    if cfg.motion_data_config.robot_type != robot or cfg.motion_data_config.data_format != data_format:
        cfg.motion_data_config = MotionDataConfig(data_format=data_format, robot_type=robot)

    if task_type == "climbing" and cfg.task_config.object_dir is None:
        cfg.task_config = replace(cfg.task_config, object_dir=data_path / task_name)

    constants = build_runtime_context(
        robot_config=cfg.robot_config,
        motion_data_config=cfg.motion_data_config,
        task_config=cfg.task_config,
        task_type=task_type,
    ).to_legacy_namespace()

    human_joints, object_poses, smpl_scale = load_motion_data(
        task_type, data_format, data_path, task_name, constants, cfg.motion_data_config
    )

    toe_names = cfg.motion_data_config.toe_names

    object_local_pts, object_local_pts_demo, object_urdf_path = setup_object_data(
        task_type,
        constants,
        cfg.task_config.object_dir,
        smpl_scale,
        cfg.task_config,
        cfg.augmentation,
        object_scale_augmented=_OBJECT_SCALE_AUGMENTED,
    )

    retargeter_kwargs = build_retargeter_kwargs_from_config(cfg.retargeter, constants, object_urdf_path, task_type)
    retargeter = InteractionMeshRetargeter(**retargeter_kwargs)
    logger.info("Retargeter created")

    human_joints, object_poses, _ = preprocess_retargeting_motion(
        task_type=task_type,
        data_format=data_format,
        human_joints=human_joints,
        object_poses=object_poses,
        retargeter=retargeter,
        toe_names=toe_names,
        smpl_scale=smpl_scale,
    )

    q_init, q_nominal, object_poses_augmented, human_joints, object_poses = initialize_robot_pose(
        task_type,
        data_format,
        human_joints,
        object_poses,
        constants,
        retargeter,
        cfg.task_config,
        cfg.augmentation,
        save_dir,
        task_name,
        augmentation_translation=_AUGMENTATION_TRANSLATION,
    )

    foot_sticking_sequences = build_foot_sticking_sequences(
        task_type=task_type,
        human_joints=human_joints,
        demo_joints=retargeter.demo_joints,
        toe_names=toe_names,
    )

    dest_res_path = determine_output_path(task_type, save_dir, task_name, cfg.augmentation)

    logger.info("Starting retargeting...")
    retargeter.retarget_motion(
        human_joint_motions=human_joints,
        object_poses=object_poses,
        object_poses_augmented=object_poses_augmented,
        object_points_local_demo=object_local_pts_demo,
        object_points_local=object_local_pts,
        foot_sticking_sequences=foot_sticking_sequences,
        q_a_init=q_init,
        q_nominal_list=q_nominal,
        original=not cfg.augmentation,
        dest_res_path=dest_res_path,
    )
    logger.info("Retargeting complete. Results saved to: %s", dest_res_path)

    if cfg.retargeter.debug:
        input("Press Enter to exit ...")
