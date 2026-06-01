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
                "omniretarget.retargeter",
                "omniretarget.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "omniretarget.examples.parallel_robot_retarget",
            [
                "omniretarget.examples.parallel_robot_retarget",
                "omniretarget.examples.robot_retarget",
                "omniretarget.retargeter",
                "omniretarget.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "omniretarget.data_conversion.convert_data_format_mj",
            ["omniretarget.data_conversion.convert_data_format_mj"],
        ),
        (
            "omniretarget.data_conversion.convert_data_format_parc_mj",
            ["omniretarget.data_conversion.convert_data_format_parc_mj"],
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
        (
            "omniretarget.examples.parc_batch_process_to_mj",
            ["omniretarget.examples.parc_batch_process_to_mj"],
        ),
        (
            "omniretarget.retargeting",
            ["omniretarget.retargeting"],
        ),
        (
            "omniretarget.retargeting.interaction_mesh_retargeter",
            ["omniretarget.retargeting.interaction_mesh_retargeter"],
        ),
        (
            "omniretarget.retargeter",
            [
                "omniretarget.retargeter",
                "omniretarget.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "omniretarget.retargeting.pipeline",
            ["omniretarget.retargeting.pipeline"],
        ),
        (
            "omniretarget.retargeting.motion_source",
            ["omniretarget.retargeting.motion_source"],
        ),
        (
            "omniretarget.retargeting.object_setup",
            ["omniretarget.retargeting.object_setup"],
        ),
        (
            "omniretarget.retargeting.preprocessing",
            ["omniretarget.retargeting.preprocessing"],
        ),
        (
            "omniretarget.retargeting.initialization",
            ["omniretarget.retargeting.initialization"],
        ),
        (
            "omniretarget.retargeting.augmentation",
            ["omniretarget.retargeting.augmentation"],
        ),
        (
            "omniretarget.retargeting.results",
            ["omniretarget.retargeting.results"],
        ),
        (
            "omniretarget.retargeting.batch",
            ["omniretarget.retargeting.batch"],
        ),
        (
            "omniretarget.mujoco",
            ["omniretarget.mujoco"],
        ),
        (
            "omniretarget.mujoco.assets",
            ["omniretarget.mujoco.assets"],
        ),
        (
            "omniretarget.mujoco.model_state",
            ["omniretarget.mujoco.model_state"],
        ),
        (
            "omniretarget.mujoco.kinematics",
            ["omniretarget.mujoco.kinematics"],
        ),
        (
            "omniretarget.mujoco.collision",
            ["omniretarget.mujoco.collision"],
        ),
        (
            "omniretarget.solver",
            ["omniretarget.solver"],
        ),
        (
            "omniretarget.solver.interaction_mesh",
            ["omniretarget.solver.interaction_mesh"],
        ),
        (
            "omniretarget.solver.frame_problem",
            ["omniretarget.solver.frame_problem"],
        ),
        (
            "omniretarget.solver.constraints",
            ["omniretarget.solver.constraints"],
        ),
        (
            "omniretarget.solver.optimizer",
            ["omniretarget.solver.optimizer"],
        ),
        (
            "omniretarget.solver.trajectory",
            ["omniretarget.solver.trajectory"],
        ),
        (
            "omniretarget.visualization",
            ["omniretarget.visualization"],
        ),
        (
            "omniretarget.visualization.playback",
            ["omniretarget.visualization.playback"],
        ),
        (
            "omniretarget.visualization.viser_adapter",
            ["omniretarget.visualization.viser_adapter"],
        ),
    ],
)
def test_entrypoint_import_does_not_mutate_sys_path(monkeypatch, module_name: str, reset_modules: list[str]) -> None:
    for name in reset_modules:
        sys.modules.pop(name, None)

    monkeypatch.setattr(sys, "path", NoInsertPath(sys.path))

    importlib.import_module(module_name)
