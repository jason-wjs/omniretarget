from __future__ import annotations

import tyro

from holosoma_retargeting.config_types.retargeting import ParallelRetargetingConfig
from holosoma_retargeting.examples.parallel_robot_retarget import main as run_parallel_retarget


def main() -> None:
    cfg = tyro.cli(ParallelRetargetingConfig)
    run_parallel_retarget(cfg)


if __name__ == "__main__":
    main()
