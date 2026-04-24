from __future__ import annotations

import tyro

from holosoma_retargeting.cli.robot_retarget import *  # noqa: F401,F403
from holosoma_retargeting.cli.robot_retarget import RetargetingConfig, main


if __name__ == "__main__":
    main(tyro.cli(RetargetingConfig))
