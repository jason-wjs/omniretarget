from __future__ import annotations

import tyro

from holosoma_retargeting.config_types.retargeting import RetargetingConfig
from holosoma_retargeting.pipelines.motion_loading import create_ground_points, load_motion_data
from holosoma_retargeting.pipelines.object_setup import (
    build_retargeter_kwargs_from_config,
    convert_object_poses_to_mujoco_order,
    determine_output_path,
    initialize_robot_pose,
    setup_object_data,
)
from holosoma_retargeting.pipelines.retarget import run_retarget
from holosoma_retargeting.pipelines.task_setup import (
    DEFAULT_DATA_FORMATS,
    DEFAULT_SAVE_DIRS,
    TaskType,
    create_task_constants,
    validate_config,
)


def main(cfg: RetargetingConfig) -> None:
    """Compatibility entrypoint for the old examples path."""
    run_retarget(cfg)


if __name__ == "__main__":
    cfg = tyro.cli(RetargetingConfig)
    main(cfg)
