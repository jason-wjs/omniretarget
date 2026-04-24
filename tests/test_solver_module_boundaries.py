from __future__ import annotations

import importlib

import pytest


SOLVER_HELPER_MODULES = (
    "holosoma_retargeting.solver.visualization",
    "holosoma_retargeting.solver.kinematics",
    "holosoma_retargeting.solver.collision",
)


@pytest.mark.parametrize(
    "module_name",
    SOLVER_HELPER_MODULES,
)
def test_new_solver_helper_modules_exist_and_import_cleanly(module_name: str) -> None:
    importlib.import_module(module_name)


def test_interaction_mesh_retargeter_remains_importable_from_solver_module() -> None:
    solver_module = importlib.import_module("holosoma_retargeting.solver.interaction_mesh_retargeter")

    assert hasattr(solver_module, "InteractionMeshRetargeter")


def test_historical_interaction_mesh_retargeter_wrapper_still_reexports_solver_class() -> None:
    solver_module = importlib.import_module("holosoma_retargeting.solver.interaction_mesh_retargeter")
    legacy_module = importlib.import_module("holosoma_retargeting.src.interaction_mesh_retargeter")

    assert hasattr(legacy_module, "InteractionMeshRetargeter")
    assert legacy_module.InteractionMeshRetargeter is solver_module.InteractionMeshRetargeter
