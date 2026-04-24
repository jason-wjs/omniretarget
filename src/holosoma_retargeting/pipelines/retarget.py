from __future__ import annotations

import logging
import os
from dataclasses import replace
from pathlib import Path

from holosoma_retargeting.config_types.data_type import MotionDataConfig
from holosoma_retargeting.config_types.retargeting import RetargetingConfig
from holosoma_retargeting.config_types.robot import RobotConfig
from holosoma_retargeting.pipelines.motion_loading import load_motion_data
from holosoma_retargeting.pipelines.object_setup import (
    _AUGMENTATION_TRANSLATION,
    _OBJECT_SCALE_AUGMENTED,
    build_retargeter_kwargs_from_config,
    determine_output_path,
    initialize_robot_pose,
    setup_object_data,
)
from holosoma_retargeting.pipelines.task_setup import (
    DEFAULT_DATA_FORMATS,
    DEFAULT_SAVE_DIRS,
    create_task_constants,
    validate_config,
)
from holosoma_retargeting.solver.interaction_mesh_retargeter import InteractionMeshRetargeter
from holosoma_retargeting.utils.contact import extract_foot_sticking_sequence_velocity
from holosoma_retargeting.utils.motion_preprocessing import preprocess_motion_data


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_retarget(cfg: RetargetingConfig) -> None:
    """Run the single-sequence retargeting pipeline."""
    validate_config(cfg)

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

    constants = create_task_constants(
        robot_config=cfg.robot_config,
        motion_data_config=cfg.motion_data_config,
        task_config=cfg.task_config,
        task_type=task_type,
    )

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

    if task_type == "robot_only":
        ground_height_percentile = 5.0 if data_format == "optitrack" else 0.0
        mat_height = 0.0 if data_format == "optitrack" else 0.1
        human_joints = preprocess_motion_data(
            human_joints,
            retargeter,
            toe_names,
            smpl_scale,
            mat_height=mat_height,
            ground_height_percentile=ground_height_percentile,
        )
    elif task_type in {"object_interaction", "climbing"}:
        human_joints, object_poses, _ = preprocess_motion_data(
            human_joints,
            retargeter,
            toe_names,
            scale=smpl_scale,
            object_poses=object_poses,
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

    foot_sticking_sequences = extract_foot_sticking_sequence_velocity(human_joints, retargeter.demo_joints, toe_names)

    if task_type == "object_interaction":
        foot_sticking_sequences[0][toe_names[0]] = False
        foot_sticking_sequences[0][toe_names[1]] = False

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
