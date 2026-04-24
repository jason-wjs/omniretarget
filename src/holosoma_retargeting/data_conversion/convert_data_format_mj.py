from __future__ import annotations

import tyro

from holosoma_retargeting.cli.data_process.convert_data_format_mj import *  # noqa: F401,F403
from holosoma_retargeting.cli.data_process.convert_data_format_mj import DataConversionConfig, main


if __name__ == "__main__":
    tyro_config = tyro.cli(DataConversionConfig)
    main(tyro_config)
