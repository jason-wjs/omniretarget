from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "holosoma_retargeting.utils.motion_io",
        "holosoma_retargeting.utils.motion_preprocessing",
        "holosoma_retargeting.utils.object_mesh",
        "holosoma_retargeting.utils.scene_assets",
        "holosoma_retargeting.utils.transforms",
        "holosoma_retargeting.utils.contact",
    ],
)
def test_new_utility_modules_exist_and_import_cleanly(module_name: str) -> None:
    importlib.import_module(module_name)


def test_legacy_utils_module_still_exports_representative_functions() -> None:
    utils_module = importlib.import_module("holosoma_retargeting.utils.utils")

    for attr_name in [
        "load_intermimic_data",
        "preprocess_motion_data",
        "load_object_data",
        "create_new_scene_xml_file",
        "transform_points_world_to_local",
        "extract_foot_sticking_sequence_velocity",
    ]:
        assert hasattr(utils_module, attr_name)
