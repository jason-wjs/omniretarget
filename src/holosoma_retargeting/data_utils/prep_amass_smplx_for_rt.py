from __future__ import annotations

import tyro

from holosoma_retargeting.cli.data_process.prep_amass_smplx_for_rt import *  # noqa: F401,F403
from holosoma_retargeting.cli.data_process.prep_amass_smplx_for_rt import Config, main


if __name__ == "__main__":
    cfg = tyro.cli(Config)
    main(cfg)
