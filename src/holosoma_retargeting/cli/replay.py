from __future__ import annotations

import tyro

from holosoma_retargeting.config_types.viser import ViserConfig
from holosoma_retargeting.viser_player import main as run_replay


def main() -> None:
    cfg = tyro.cli(ViserConfig)
    run_replay(cfg)


if __name__ == "__main__":
    main()
