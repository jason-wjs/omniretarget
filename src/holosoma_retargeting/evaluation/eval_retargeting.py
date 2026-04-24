from __future__ import annotations

import tyro

from holosoma_retargeting.cli.eval_retargeting import *  # noqa: F401,F403
from holosoma_retargeting.cli.eval_retargeting import Args, main


if __name__ == "__main__":
    main(tyro.cli(Args))
