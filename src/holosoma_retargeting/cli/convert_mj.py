from __future__ import annotations

import tyro

from holosoma_retargeting.config_types.data_conversion import DataConversionConfig
from holosoma_retargeting.data_conversion.convert_data_format_mj import main as run_conversion


def main() -> None:
    cfg = tyro.cli(DataConversionConfig)
    run_conversion(cfg)


if __name__ == "__main__":
    main()
