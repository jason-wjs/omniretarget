#!/usr/bin/env python3
from __future__ import annotations

import tyro

from holosoma_retargeting.cli.viser_player import *  # noqa: F401,F403
from holosoma_retargeting.cli.viser_player import ViserConfig, main


if __name__ == "__main__":
    main(tyro.cli(ViserConfig))
