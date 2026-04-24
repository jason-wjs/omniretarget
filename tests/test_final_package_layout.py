from __future__ import annotations

import importlib

import pytest

from tests.path_helpers import PACKAGE_ROOT

PACKAGE_NAME = "holosoma_retargeting"
LEGACY_CONFIG_TYPES = PACKAGE_NAME + ".config" + "_types"
LEGACY_CONFIG_VALUES = PACKAGE_NAME + ".config" + "_values"
LEGACY_SRC = PACKAGE_NAME + "." + "src"


def test_final_overview_package_directories() -> None:
    expected = {
        "__pycache__",
        "cli",
        "configs",
        "demo_data",
        "models",
        "profiles",
        "retargeter",
        "utils",
    }
    actual = {path.name for path in PACKAGE_ROOT.iterdir() if path.is_dir()}

    assert actual <= expected


@pytest.mark.parametrize(
    "module_name",
    [
        LEGACY_CONFIG_TYPES,
        LEGACY_CONFIG_VALUES,
        LEGACY_SRC,
        LEGACY_SRC + ".utils",
        LEGACY_SRC + ".mujoco_utils",
        LEGACY_SRC + ".viser_utils",
        LEGACY_SRC + "." + "interaction_mesh" + "_retargeter",
    ],
)
def test_legacy_architecture_modules_are_removed(module_name: str) -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module_name)
