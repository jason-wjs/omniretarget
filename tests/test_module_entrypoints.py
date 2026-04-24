from __future__ import annotations

import importlib
import sys

import pytest


SOLVER_HELPER_MODULES = (
    "holosoma_retargeting.solver.visualization",
    "holosoma_retargeting.solver.kinematics",
    "holosoma_retargeting.solver.collision",
)

ENTRYPOINT_MODULES = (
    "holosoma_retargeting.examples.robot_retarget",
    "holosoma_retargeting.examples.parallel_robot_retarget",
    "holosoma_retargeting.cli.retarget",
    "holosoma_retargeting.cli.parallel_retarget",
    "holosoma_retargeting.cli.evaluate",
    "holosoma_retargeting.cli.convert_mj",
    "holosoma_retargeting.cli.replay",
    "holosoma_retargeting.pipelines.task_setup",
    "holosoma_retargeting.pipelines.motion_loading",
    "holosoma_retargeting.pipelines.object_setup",
    "holosoma_retargeting.pipelines.retarget",
    "holosoma_retargeting.utils.motion_io",
    "holosoma_retargeting.utils.motion_preprocessing",
    "holosoma_retargeting.utils.object_mesh",
    "holosoma_retargeting.utils.scene_assets",
    "holosoma_retargeting.utils.transforms",
    "holosoma_retargeting.utils.contact",
    "holosoma_retargeting.solver.interaction_mesh_retargeter",
    *SOLVER_HELPER_MODULES,
    "holosoma_retargeting.data_conversion.convert_data_format_mj",
    "holosoma_retargeting.evaluation.eval_retargeting",
    "holosoma_retargeting.viser_player",
)
LEGACY_ENTRYPOINT_MODULE = "holosoma_retargeting.src.interaction_mesh_retargeter"


class NoMutatingSysPath(list[str]):
    def _raise(self, operation: str, *details: object) -> None:
        detail_suffix = "".join(f", {detail!r}" for detail in details)
        raise AssertionError(f"unexpected sys.path.{operation}({detail_suffix.lstrip(', ')}) during module import")

    def append(self, object: str) -> None:
        self._raise("append", object)

    def extend(self, iterable) -> None:
        self._raise("extend", list(iterable))

    def insert(self, index: int, object: str) -> None:
        self._raise("insert", index, object)

    def pop(self, index: int = -1) -> str:
        self._raise("pop", index)

    def remove(self, object: str) -> None:
        self._raise("remove", object)

    def clear(self) -> None:
        self._raise("clear")

    def sort(self, *, key=None, reverse: bool = False) -> None:
        self._raise("sort", key, reverse)

    def reverse(self) -> None:
        self._raise("reverse")

    def __setitem__(self, index, value) -> None:
        self._raise("__setitem__", index, value)

    def __delitem__(self, index) -> None:
        self._raise("__delitem__", index)

    def __iadd__(self, other):
        self._raise("__iadd__", list(other))

    def __imul__(self, other):
        self._raise("__imul__", other)


def _reset_import_state() -> None:
    for loaded_module_name in list(sys.modules):
        if loaded_module_name == "holosoma_retargeting" or loaded_module_name.startswith(
            "holosoma_retargeting."
        ):
            sys.modules.pop(loaded_module_name, None)


@pytest.mark.parametrize(
    "module_name",
    ENTRYPOINT_MODULES,
)
def test_entrypoint_import_does_not_mutate_sys_path(monkeypatch, module_name: str) -> None:
    _reset_import_state()

    guarded_sys_path = NoMutatingSysPath(sys.path)
    monkeypatch.setattr(sys, "path", guarded_sys_path)

    importlib.import_module(module_name)

    assert sys.path is guarded_sys_path


def test_legacy_src_entrypoint_import_does_not_mutate_sys_path(monkeypatch) -> None:
    # Temporary explicit coverage for the compatibility wrapper package during the
    # src-compatibility removal phase. Delete this test deliberately with that package.
    _reset_import_state()

    guarded_sys_path = NoMutatingSysPath(sys.path)
    monkeypatch.setattr(sys, "path", guarded_sys_path)

    importlib.import_module(LEGACY_ENTRYPOINT_MODULE)

    assert sys.path is guarded_sys_path
