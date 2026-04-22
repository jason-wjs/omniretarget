#!/usr/bin/env bash
set -euo pipefail

export PYTEST_DISABLE_PLUGIN_AUTOLOAD="${PYTEST_DISABLE_PLUGIN_AUTOLOAD:-1}"

uv run pytest tests/test_adam_pro_robot_config.py -q
uv run pytest tests/test_adam_pro_motion_mappings.py -q
uv run pytest tests/test_adam_pro_data_conversion.py -q
uv run pytest tests/test_optitrack_motion_format.py -q
uv run pytest tests/test_package_paths.py -q
uv run pytest tests/test_module_entrypoints.py -q
