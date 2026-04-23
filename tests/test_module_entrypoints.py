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
            "holosoma_retargeting.examples.robot_retarget",
            [
                "holosoma_retargeting.examples.robot_retarget",
                "holosoma_retargeting.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "holosoma_retargeting.examples.parallel_robot_retarget",
            [
                "holosoma_retargeting.examples.parallel_robot_retarget",
                "holosoma_retargeting.examples.robot_retarget",
                "holosoma_retargeting.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "holosoma_retargeting.cli.retarget",
            [
                "holosoma_retargeting.cli.retarget",
                "holosoma_retargeting.pipelines.retarget",
                "holosoma_retargeting.pipelines.task_setup",
                "holosoma_retargeting.pipelines.motion_loading",
                "holosoma_retargeting.pipelines.object_setup",
                "holosoma_retargeting.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "holosoma_retargeting.cli.parallel_retarget",
            [
                "holosoma_retargeting.cli.parallel_retarget",
                "holosoma_retargeting.pipelines.parallel",
                "holosoma_retargeting.pipelines.retarget",
                "holosoma_retargeting.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "holosoma_retargeting.cli.evaluate",
            ["holosoma_retargeting.cli.evaluate"],
        ),
        (
            "holosoma_retargeting.cli.convert_mj",
            ["holosoma_retargeting.cli.convert_mj"],
        ),
        (
            "holosoma_retargeting.cli.replay",
            ["holosoma_retargeting.cli.replay"],
        ),
        (
            "holosoma_retargeting.pipelines.task_setup",
            ["holosoma_retargeting.pipelines.task_setup"],
        ),
        (
            "holosoma_retargeting.pipelines.motion_loading",
            ["holosoma_retargeting.pipelines.motion_loading"],
        ),
        (
            "holosoma_retargeting.pipelines.object_setup",
            ["holosoma_retargeting.pipelines.object_setup"],
        ),
        (
            "holosoma_retargeting.pipelines.retarget",
            ["holosoma_retargeting.pipelines.retarget"],
        ),
        (
            "holosoma_retargeting.data_conversion.convert_data_format_mj",
            ["holosoma_retargeting.data_conversion.convert_data_format_mj"],
        ),
        (
            "holosoma_retargeting.evaluation.eval_retargeting",
            ["holosoma_retargeting.evaluation.eval_retargeting"],
        ),
        (
            "holosoma_retargeting.viser_player",
            ["holosoma_retargeting.viser_player"],
        ),
    ],
)
def test_entrypoint_import_does_not_mutate_sys_path(monkeypatch, module_name: str, reset_modules: list[str]) -> None:
    for name in reset_modules:
        sys.modules.pop(name, None)

    monkeypatch.setattr(sys, "path", NoInsertPath(sys.path))

    importlib.import_module(module_name)
