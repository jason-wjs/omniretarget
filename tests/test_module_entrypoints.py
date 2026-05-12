from __future__ import annotations

import importlib
import sys

import pytest


class NoInsertPath(list[str]):
    def insert(self, index: int, object: str) -> None:
        raise AssertionError(f"unexpected sys.path.insert({index}, {object!r}) during module import")


@pytest.mark.parametrize(
    ("module_name", "reset_modules"),
    [
        (
            "omniretarget.examples.robot_retarget",
            [
                "omniretarget.examples.robot_retarget",
                "omniretarget.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "omniretarget.examples.parallel_robot_retarget",
            [
                "omniretarget.examples.parallel_robot_retarget",
                "omniretarget.examples.robot_retarget",
                "omniretarget.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "omniretarget.data_conversion.convert_data_format_mj",
            ["omniretarget.data_conversion.convert_data_format_mj"],
        ),
        (
            "omniretarget.evaluation.eval_retargeting",
            ["omniretarget.evaluation.eval_retargeting"],
        ),
        (
            "omniretarget.viser_player",
            ["omniretarget.viser_player"],
        ),
        (
            "omniretarget.examples.parc_process",
            ["omniretarget.examples.parc_process"],
        ),
    ],
)
def test_entrypoint_import_does_not_mutate_sys_path(monkeypatch, module_name: str, reset_modules: list[str]) -> None:
    for name in reset_modules:
        sys.modules.pop(name, None)

    monkeypatch.setattr(sys, "path", NoInsertPath(sys.path))

    importlib.import_module(module_name)
