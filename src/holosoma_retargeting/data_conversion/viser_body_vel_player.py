#!/usr/bin/env python3
from __future__ import annotations

import tyro

from holosoma_retargeting.cli.viser_body_vel_player import *  # noqa: F401,F403
from holosoma_retargeting.cli.viser_body_vel_player import Config, main


if __name__ == "__main__":
    main(tyro.cli(Config))
