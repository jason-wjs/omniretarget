from __future__ import annotations

import multiprocessing as mp
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path

from omniretarget.config_types.data_type import MotionDataConfig
from omniretarget.config_types.retargeting import ParallelRetargetingConfig
from omniretarget.config_types.robot import RobotConfig
from omniretarget.retargeting.augmentation import generate_augmentation_configs
from omniretarget.retargeting.initialization import initialize_robot_pose
from omniretarget.retargeting.motion_source import load_motion_data
from omniretarget.retargeting.object_setup import setup_object_data
from omniretarget.retargeting.pipeline import DEFAULT_DATA_FORMATS, build_retargeter_kwargs_from_config
from omniretarget.retargeting.preprocessing import build_foot_sticking_sequences, preprocess_retargeting_motion
from omniretarget.runtime.context import build_runtime_context
from omniretarget.src.interaction_mesh_retargeter import InteractionMeshRetargeter

PARALLEL_SAVE_DIRS = {
    "robot_only": "demo_results_parallel/{robot}/robot_only/omomo",
    "object_interaction": "demo_results_parallel/{robot}/object_interaction/omomo",
    "climbing": "demo_results_parallel/{robot}/climbing/mocap_climb",
}


def find_files(data_dir: Path, data_format: str, object_name: str | None = None):
    """Find files based on data format."""
    data_dir = Path(data_dir)

    if data_format == "lafan":
        files = [str(p) for p in data_dir.glob("*.npy")]
        return sorted(files)
    if data_format == "smplh":
        if object_name:
            files = [str(p) for p in data_dir.glob(f"*{object_name}*.pt")]
        else:
            files = [str(p) for p in data_dir.glob("*.pt")]
        return sorted(files)
    if data_format == "mocap":
        files = [str(p) for p in data_dir.glob("*/*.npy")]
        return sorted(files)
    if data_format == "smplx":
        files = [str(p) for p in data_dir.glob("*.npz")]
        return sorted(files)
    files = [str(p) for p in data_dir.glob("*.npz")]
    return sorted(files)


def extract_task_name(file_path):
    """Extract task name from file path."""
    return Path(file_path).stem


def process_single_task(args):
    """Process a single task with all augmentations."""
    (
        file_path,
        save_dir,
        task_type,
        data_format,
        robot_config,
        motion_data_config,
        task_config,
        retargeter,
        augmentation,
    ) = args

    os.makedirs(save_dir, exist_ok=True)
    if task_type == "climbing":
        file_path = "/".join(file_path.split("/")[:-1])
        task_name = extract_task_name(file_path)
    else:
        task_name = extract_task_name(file_path)
    print(f"Processing: {task_name}")

    if task_type == "climbing" and task_config.object_dir is None:
        task_config = replace(task_config, object_dir=Path(file_path))

    constants = build_runtime_context(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        task_config=task_config,
        task_type=task_type,
    ).to_legacy_namespace()

    human_joints, object_poses, smpl_scale = load_motion_data(
        task_type, data_format, Path(file_path).parent, task_name, constants, motion_data_config
    )

    human_joints_original = human_joints.copy()
    object_poses_original = object_poses.copy()

    toe_names = motion_data_config.toe_names

    augmentations = generate_augmentation_configs(task_type, augmentation)
    print("The number of augmentations: ", len(augmentations))

    for k, aug_config in enumerate(augmentations):
        human_joints = human_joints_original.copy()
        object_poses = object_poses_original.copy()
        aug_name = aug_config["name"]
        file_name = f"{save_dir}/{task_name}_{aug_name}.npz"

        print(f"  Processing augmentation: {aug_name}")

        if task_type == "climbing":
            print("obejct_dir: ", task_config.object_dir)
            object_local_pts, object_local_pts_demo, object_urdf_path = setup_object_data(
                task_type,
                constants,
                task_config.object_dir,
                smpl_scale,
                task_config,
                augmentation=(k > 0),
                object_scale_augmented=aug_config["scale"],
            )
        else:
            object_local_pts, object_local_pts_demo, object_urdf_path = setup_object_data(
                task_type,
                constants,
                task_config.object_dir,
                smpl_scale,
                task_config,
                augmentation=(k > 0),
            )

        retargeter_kwargs = build_retargeter_kwargs_from_config(retargeter, constants, object_urdf_path, task_type)
        retargeter = InteractionMeshRetargeter(**retargeter_kwargs)

        human_joints, object_poses, _ = preprocess_retargeting_motion(
            task_type=task_type,
            data_format=data_format,
            human_joints=human_joints,
            object_poses=object_poses,
            retargeter=retargeter,
            toe_names=toe_names,
            smpl_scale=smpl_scale,
        )

        foot_sticking_sequences = build_foot_sticking_sequences(
            task_type=task_type,
            human_joints=human_joints,
            demo_joints=retargeter.demo_joints,
            toe_names=toe_names,
        )

        is_augmentation_run = k > 0

        if task_type == "object_interaction":
            q_init, q_nominal, object_poses_augmented, human_joints, object_poses = initialize_robot_pose(
                task_type,
                data_format,
                human_joints,
                object_poses,
                constants,
                retargeter,
                task_config,
                is_augmentation_run,
                save_dir,
                task_name,
                augmentation_translation=aug_config["translation"],
                augmentation_rotation=aug_config["rotation"],
            )
        else:
            q_init, q_nominal, object_poses_augmented, human_joints, object_poses = initialize_robot_pose(
                task_type,
                data_format,
                human_joints,
                object_poses,
                constants,
                retargeter,
                task_config,
                is_augmentation_run,
                save_dir,
                task_name,
            )

        if Path.exists(Path(file_name)):
            continue

        retargeter.retarget_motion(
            human_joint_motions=human_joints,
            object_poses=object_poses,
            object_poses_augmented=object_poses_augmented,
            object_points_local_demo=object_local_pts_demo,
            object_points_local=object_local_pts,
            foot_sticking_sequences=foot_sticking_sequences,
            q_a_init=q_init,
            q_nominal_list=q_nominal,
            original=(k == 0),
            dest_res_path=file_name,
        )


def run_parallel_retargeting(cfg: ParallelRetargetingConfig) -> None:
    """Run the parallel retargeting workflow."""
    robot = cfg.robot
    task_type = cfg.task_type

    data_format: str = cfg.data_format or DEFAULT_DATA_FORMATS[task_type]
    save_dir = cfg.save_dir if cfg.save_dir is not None else Path(PARALLEL_SAVE_DIRS[task_type].format(robot=robot))
    data_dir = cfg.data_dir

    os.makedirs(save_dir, exist_ok=True)
    print(f"Task type: {task_type}, Format: {data_format}")
    print(f"Data dir: {data_dir}, Save dir: {save_dir}")

    if cfg.robot_config.robot_type != robot:
        cfg.robot_config = RobotConfig(robot_type=robot)

    if cfg.motion_data_config.robot_type != robot or cfg.motion_data_config.data_format != data_format:
        cfg.motion_data_config = MotionDataConfig(data_format=data_format, robot_type=robot)

    if task_type == "robot_only":
        files = find_files(data_dir, data_format)
    else:
        files = find_files(data_dir, data_format, cfg.task_config.object_name)
    print(f"Found {len(files)} files for task type: {task_type}")

    process_args = [
        (
            file_path,
            save_dir,
            task_type,
            data_format,
            cfg.robot_config,
            cfg.motion_data_config,
            cfg.task_config,
            cfg.retargeter,
            cfg.augmentation,
        )
        for file_path in files
    ]

    max_workers = cfg.max_workers or mp.cpu_count()
    print(f"Using {max_workers} parallel workers")

    start_time = time.time()
    successful = 0
    failed = 0

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(process_single_task, arg): arg[0] for arg in process_args}

        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                future.result()
                print(f"Completed: {file_path}")
                successful += 1
            except Exception as e:
                print(f"Failed {file_path}: {e}")
                import traceback

                traceback.print_exc()
                failed += 1

    end_time = time.time()

    print("\n=== Processing Summary ===")
    print(f"Task type: {task_type}")
    print(f"Total files: {len(files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    if len(files) > 0:
        print(f"Average time per file: {(end_time - start_time) / len(files):.2f} seconds")
    print(f"Results saved to: {save_dir}")
