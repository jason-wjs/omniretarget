"""
Unified parallel processing script for retargeting all task types:
- robot_only: Robot-only retargeting with ground interaction (LAFAN)
- object_interaction: Object manipulation retargeting (InterMimic)
- climbing: Climbing retargeting with dynamic terrain (MOCAP)
"""

from __future__ import annotations

from pathlib import Path

import tyro

from omniretarget.config_types.retargeting import ParallelRetargetingConfig  # noqa: E402
from omniretarget.retargeting.augmentation import generate_augmentation_configs as _generate_augmentation_configs
from omniretarget.retargeting.batch import (  # noqa: E402
    PARALLEL_SAVE_DIRS,
    extract_task_name as _extract_task_name,
    find_files as _find_files,
    process_single_task as _process_single_task,
    run_parallel_retargeting,
)

# ----------------------------- Constants -----------------------------

def find_files(data_dir: Path, data_format: str, object_name: str | None = None):
    """Find files based on data format.

    Args:
        data_dir: Directory to search for files
        data_format: Data format ("lafan", "smplh", "mocap")
        object_name: Optional object name to filter files (for smplh format)

    Returns:
        Sorted list of file paths
    """
    return _find_files(data_dir, data_format, object_name)


def generate_augmentation_configs(task_type: str, augmentation: bool = True):
    """Generate augmentation configurations based on task type."""
    return _generate_augmentation_configs(task_type, augmentation)


def extract_task_name(file_path):
    """Extract task name from file path."""
    return _extract_task_name(file_path)


def process_single_task(args):
    """Process a single task with all augmentations.

    This function follows the same structure as main() in robot_retarget.py,
    but handles multiple augmentations in a loop for parallel processing.
    """
    return _process_single_task(args)


def main(cfg: ParallelRetargetingConfig) -> None:
    """Main parallel retargeting pipeline.

    Args:
        cfg: Configuration arguments
    """
    run_parallel_retargeting(cfg)


if __name__ == "__main__":
    cfg = tyro.cli(ParallelRetargetingConfig)
    main(cfg)
