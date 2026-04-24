from __future__ import annotations

import importlib
import sys
from types import ModuleType

import pytest


class NoInsertPath(list[str]):
    def insert(self, index: int, object: str) -> None:
        raise AssertionError(f"unexpected sys.path.insert({index}, {object!r}) during module import")


def _stub_optional_entrypoint_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    human_body_prior = ModuleType("human_body_prior")
    human_body_prior.__path__ = []  # type: ignore[attr-defined]
    body_model_pkg = ModuleType("human_body_prior.body_model")
    body_model_pkg.__path__ = []  # type: ignore[attr-defined]
    body_model_mod = ModuleType("human_body_prior.body_model.body_model")
    body_model_mod.BodyModel = object  # type: ignore[attr-defined]

    lafan1 = ModuleType("lafan1")
    lafan1.__path__ = []  # type: ignore[attr-defined]
    lafan_extract = ModuleType("lafan1.extract")
    lafan_utils = ModuleType("lafan1.utils")
    lafan1.extract = lafan_extract  # type: ignore[attr-defined]
    lafan1.utils = lafan_utils  # type: ignore[attr-defined]

    for name, module in {
        "human_body_prior": human_body_prior,
        "human_body_prior.body_model": body_model_pkg,
        "human_body_prior.body_model.body_model": body_model_mod,
        "lafan1": lafan1,
        "lafan1.extract": lafan_extract,
        "lafan1.utils": lafan_utils,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)


@pytest.mark.parametrize(
    ("module_name", "reset_modules"),
    [
        (
            "holosoma_retargeting.examples.robot_retarget",
            [
                "holosoma_retargeting.examples.robot_retarget",
                "holosoma_retargeting.cli.robot_retarget",
                "holosoma_retargeting.retargeter.interaction_mesh_retargeter",
                "holosoma_retargeting.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "holosoma_retargeting.cli.robot_retarget",
            [
                "holosoma_retargeting.cli.robot_retarget",
                "holosoma_retargeting.retargeter.interaction_mesh_retargeter",
                "holosoma_retargeting.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "holosoma_retargeting.examples.parallel_robot_retarget",
            [
                "holosoma_retargeting.examples.parallel_robot_retarget",
                "holosoma_retargeting.examples.robot_retarget",
                "holosoma_retargeting.cli.parallel_robot_retarget",
                "holosoma_retargeting.cli.robot_retarget",
                "holosoma_retargeting.retargeter.interaction_mesh_retargeter",
                "holosoma_retargeting.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "holosoma_retargeting.cli.parallel_robot_retarget",
            [
                "holosoma_retargeting.cli.parallel_robot_retarget",
                "holosoma_retargeting.cli.robot_retarget",
                "holosoma_retargeting.retargeter.interaction_mesh_retargeter",
                "holosoma_retargeting.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "holosoma_retargeting.data_conversion.convert_data_format_mj",
            [
                "holosoma_retargeting.data_conversion.convert_data_format_mj",
                "holosoma_retargeting.cli.data_process.convert_data_format_mj",
            ],
        ),
        (
            "holosoma_retargeting.cli.data_process.convert_data_format_mj",
            [
                "holosoma_retargeting.cli.data_process.convert_data_format_mj",
                "holosoma_retargeting.data_conversion.convert_data_format_mj",
            ],
        ),
        (
            "holosoma_retargeting.data_utils.prep_amass_smplx_for_rt",
            [
                "holosoma_retargeting.data_utils.prep_amass_smplx_for_rt",
                "holosoma_retargeting.cli.data_process.prep_amass_smplx_for_rt",
            ],
        ),
        (
            "holosoma_retargeting.cli.data_process.prep_amass_smplx_for_rt",
            [
                "holosoma_retargeting.cli.data_process.prep_amass_smplx_for_rt",
                "holosoma_retargeting.data_utils.prep_amass_smplx_for_rt",
            ],
        ),
        (
            "holosoma_retargeting.data_utils.prep_optitrack_for_rt",
            [
                "holosoma_retargeting.data_utils.prep_optitrack_for_rt",
                "holosoma_retargeting.cli.data_process.prep_optitrack_for_rt",
            ],
        ),
        (
            "holosoma_retargeting.cli.data_process.prep_optitrack_for_rt",
            [
                "holosoma_retargeting.cli.data_process.prep_optitrack_for_rt",
                "holosoma_retargeting.data_utils.prep_optitrack_for_rt",
            ],
        ),
        (
            "holosoma_retargeting.data_utils.extract_global_positions",
            [
                "holosoma_retargeting.data_utils.extract_global_positions",
                "holosoma_retargeting.cli.data_process.extract_global_positions",
            ],
        ),
        (
            "holosoma_retargeting.cli.data_process.extract_global_positions",
            [
                "holosoma_retargeting.cli.data_process.extract_global_positions",
                "holosoma_retargeting.data_utils.extract_global_positions",
            ],
        ),
        (
            "holosoma_retargeting.evaluation.eval_retargeting",
            [
                "holosoma_retargeting.evaluation.eval_retargeting",
                "holosoma_retargeting.cli.eval_retargeting",
            ],
        ),
        (
            "holosoma_retargeting.cli.eval_retargeting",
            ["holosoma_retargeting.cli.eval_retargeting"],
        ),
        (
            "holosoma_retargeting.viser_player",
            [
                "holosoma_retargeting.viser_player",
                "holosoma_retargeting.cli.viser_player",
            ],
        ),
        (
            "holosoma_retargeting.cli.viser_player",
            ["holosoma_retargeting.cli.viser_player"],
        ),
        (
            "holosoma_retargeting.data_conversion.viser_body_vel_player",
            [
                "holosoma_retargeting.data_conversion.viser_body_vel_player",
                "holosoma_retargeting.cli.viser_body_vel_player",
            ],
        ),
        (
            "holosoma_retargeting.cli.viser_body_vel_player",
            ["holosoma_retargeting.cli.viser_body_vel_player"],
        ),
    ],
)
def test_entrypoint_import_does_not_mutate_sys_path(monkeypatch, module_name: str, reset_modules: list[str]) -> None:
    for name in reset_modules:
        sys.modules.pop(name, None)

    _stub_optional_entrypoint_dependencies(monkeypatch)
    monkeypatch.setattr(sys, "path", NoInsertPath(sys.path))

    importlib.import_module(module_name)
