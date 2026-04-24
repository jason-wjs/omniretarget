#!/usr/bin/env python3
from __future__ import annotations

import tyro

from holosoma_retargeting.cli.data_process.extract_global_positions import *  # noqa: F401,F403
from holosoma_retargeting.cli.data_process.extract_global_positions import Config, main


if __name__ == "__main__":
    cfg = tyro.cli(Config)
    main(cfg)
