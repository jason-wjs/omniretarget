from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
from types import ModuleType, SimpleNamespace

import numpy as np

from tests.path_helpers import REPO_ROOT


class _FakeInteractionMeshRetargeter:
    def __init__(self, retargeter_config):
        self.demo_joints = ["Pelvis", "L_Toe", "R_Toe"]
        self.retargeter_config = retargeter_config

    def retarget_motion(
        self,
        *,
        human_joint_motions,
        object_poses,
        object_poses_augmented,
        object_points_local_demo,
        object_points_local,
        foot_sticking_sequences,
        q_a_init,
        q_nominal_list,
        original,
        dest_res_path,
    ) -> None:
        return None


@contextmanager
def _import_parallel_module_with_stubs(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO_ROOT / "src"))

    recorded = SimpleNamespace(build_retargeter_configs=[])
    original_parallel_module = sys.modules.get("holosoma_retargeting.pipelines.parallel")

    motion_loading_module = ModuleType("holosoma_retargeting.pipelines.motion_loading")

    def load_motion_data(
        task_type,
        data_format,
        data_dir,
        task_name,
        constants,
        motion_data_config,
    ):
        return np.zeros((2, 1, 3)), np.zeros((2, 7)), 1.0

    motion_loading_module.load_motion_data = load_motion_data

    object_setup_module = ModuleType("holosoma_retargeting.pipelines.object_setup")

    def build_retargeter_kwargs_from_config(
        retargeter_config,
        constants,
        object_urdf_path,
        task_type,
    ):
        recorded.build_retargeter_configs.append(retargeter_config)
        return {"retargeter_config": retargeter_config}

    def setup_object_data(
        task_type,
        constants,
        object_dir,
        smpl_scale,
        task_config,
        augmentation,
        object_scale_augmented=None,
    ):
        return np.zeros((1, 3)), np.zeros((1, 3)), "object.urdf"

    def initialize_robot_pose(
        task_type,
        data_format,
        human_joints,
        object_poses,
        constants,
        retargeter,
        task_config,
        augmentation,
        save_dir,
        task_name,
        augmentation_translation=None,
        augmentation_rotation=0.0,
    ):
        return np.zeros(1), [np.zeros(1)], object_poses, human_joints, object_poses

    object_setup_module.build_retargeter_kwargs_from_config = build_retargeter_kwargs_from_config
    object_setup_module.initialize_robot_pose = initialize_robot_pose
    object_setup_module.setup_object_data = setup_object_data

    task_setup_module = ModuleType("holosoma_retargeting.pipelines.task_setup")
    task_setup_module.DEFAULT_DATA_FORMATS = {"object_interaction": "smplh"}

    def create_task_constants(robot_config, motion_data_config, task_config, task_type):
        return SimpleNamespace()

    task_setup_module.create_task_constants = create_task_constants

    solver_module = ModuleType("holosoma_retargeting.solver.interaction_mesh_retargeter")
    solver_module.InteractionMeshRetargeter = _FakeInteractionMeshRetargeter

    contact_module = ModuleType("holosoma_retargeting.utils.contact")

    def extract_foot_sticking_sequence_velocity(human_joints, demo_joints, toe_names):
        return [{toe_name: True for toe_name in toe_names}]

    contact_module.extract_foot_sticking_sequence_velocity = extract_foot_sticking_sequence_velocity

    motion_preprocessing_module = ModuleType("holosoma_retargeting.utils.motion_preprocessing")

    def preprocess_motion_data(
        human_joints,
        retargeter,
        toe_names,
        scale=None,
        object_poses=None,
        mat_height=None,
        ground_height_percentile=None,
    ):
        if object_poses is None:
            return human_joints
        return human_joints, object_poses, None

    motion_preprocessing_module.preprocess_motion_data = preprocess_motion_data

    for module_name, module in {
        "holosoma_retargeting.pipelines.motion_loading": motion_loading_module,
        "holosoma_retargeting.pipelines.object_setup": object_setup_module,
        "holosoma_retargeting.pipelines.task_setup": task_setup_module,
        "holosoma_retargeting.solver.interaction_mesh_retargeter": solver_module,
        "holosoma_retargeting.utils.contact": contact_module,
        "holosoma_retargeting.utils.motion_preprocessing": motion_preprocessing_module,
    }.items():
        monkeypatch.setitem(sys.modules, module_name, module)

    sys.modules.pop("holosoma_retargeting.pipelines.parallel", None)

    try:
        parallel_module = importlib.import_module("holosoma_retargeting.pipelines.parallel")
        yield parallel_module, recorded
    finally:
        sys.modules.pop("holosoma_retargeting.pipelines.parallel", None)
        if original_parallel_module is not None:
            sys.modules["holosoma_retargeting.pipelines.parallel"] = original_parallel_module


def test_process_single_task_reuses_original_retargeter_config_across_augmentations(tmp_path, monkeypatch) -> None:
    with _import_parallel_module_with_stubs(monkeypatch) as (parallel_module, recorded):
        augmentations = [
            {"name": "original", "translation": np.zeros(3), "rotation": 0.0},
            {"name": "trans_0", "translation": np.array([0.2, 0.0, 0.0]), "rotation": 0.0},
            {"name": "rot_0", "translation": np.array([0.0, 0.2, 0.0]), "rotation": np.pi / 4},
        ]
        monkeypatch.setattr(
            parallel_module,
            "generate_augmentation_configs",
            lambda task_type, augmentation: augmentations,
        )

        original_retargeter_config = object()

        parallel_module.process_single_task(
            (
                str(tmp_path / "demo_input.npz"),
                tmp_path / "results",
                "object_interaction",
                "smplh",
                SimpleNamespace(),
                SimpleNamespace(toe_names=["L_Toe", "R_Toe"]),
                SimpleNamespace(object_dir=tmp_path),
                original_retargeter_config,
                True,
            )
        )

    assert len(augmentations) > 1
    assert len(recorded.build_retargeter_configs) == len(augmentations)
    assert all(
        config is original_retargeter_config for config in recorded.build_retargeter_configs
    ), "build_retargeter_kwargs_from_config() must receive the original config on every augmentation"
