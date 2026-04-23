from __future__ import annotations

import tyro

from holosoma_retargeting.config_types.retargeting import ParallelRetargetingConfig
from holosoma_retargeting.pipelines.parallel import (
    PARALLEL_SAVE_DIRS,
    extract_task_name,
    find_files,
    generate_augmentation_configs,
    process_single_task,
    run_parallel_retarget,
)


def main(cfg: ParallelRetargetingConfig) -> None:
    """Compatibility entrypoint for the old parallel examples path."""
    run_parallel_retarget(cfg)


if __name__ == "__main__":
    cfg = tyro.cli(ParallelRetargetingConfig)
    main(cfg)
