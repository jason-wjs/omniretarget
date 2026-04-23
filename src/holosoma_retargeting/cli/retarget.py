from __future__ import annotations

import tyro

from holosoma_retargeting.config_types.retargeting import RetargetingConfig
from holosoma_retargeting.pipelines.retarget import run_retarget


def main() -> None:
    cfg = tyro.cli(RetargetingConfig)
    run_retarget(cfg)


if __name__ == "__main__":
    main()
