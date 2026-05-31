from __future__ import annotations

import json
import os
import pickle
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from omniretarget.config_types.data_type import PARC_HUMANOID_DEMO_JOINTS, MotionDataConfig
from omniretarget.examples.parc_process import build_arg_parser, compile_sample
from omniretarget.examples.robot_retarget import (
    _compute_q_init_base,
    load_motion_data,
    validate_config,
)
from omniretarget.config_types.retargeting import RetargetingConfig
from omniretarget.parc_process.output_writer import write_paired_output
from omniretarget.parc_process.source_fk import build_source_joint_positions
from omniretarget.parc_process.source_io import load_parc_sample
from omniretarget.parc_process.terrain_scene import export_parc_scene
from omniretarget.parc_process.workspace import build_parc_workspace
from omniretarget.src.interaction_mesh_retargeter import InteractionMeshRetargeter
from omniretarget.src.utils import transform_from_human_to_world


BODY_NAMES = (
    "pelvis",
    "torso",
    "head",
    "right_upper_arm",
    "right_lower_arm",
    "right_hand",
    "left_upper_arm",
    "left_lower_arm",
    "left_hand",
    "right_thigh",
    "right_shin",
    "right_foot",
    "left_thigh",
    "left_shin",
    "left_foot",
)


def _write_humanoid_xml(path: Path) -> Path:
    body_xml = "".join(
        f'<body name="{name}" pos="0 0 0.1"><geom type="sphere" size="0.01"/></body>'
        for name in BODY_NAMES[1:]
    )
    path.write_text(
        "\n".join(
            [
                "<mujoco>",
                "  <worldbody>",
                f'    <body name="{BODY_NAMES[0]}" pos="0 0 0">',
                body_xml,
                "    </body>",
                "  </worldbody>",
                "</mujoco>",
                "",
            ]
        )
    )
    return path


def _write_parc_sample(path: Path, *, frames: int = 4) -> Path:
    root_pos = np.zeros((frames, 3), dtype=np.float32)
    root_pos[:, 2] = 0.9
    root_rot = np.tile(np.array([[0.0, 0.0, 0.0, 1.0]], dtype=np.float32), (frames, 1))
    joint_rot = np.tile(np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32), (frames, len(BODY_NAMES) - 1, 1))
    motion_payload = {
        "root_pos": root_pos,
        "root_rot": root_rot,
        "joint_rot": joint_rot,
        "body_contacts": np.zeros((frames, 2), dtype=np.float32),
        "fps": 30,
        "loop_mode": "wrap",
    }
    terrain_payload = {
        "hf": np.array([[0.0, 0.1], [0.2, 0.3]], dtype=np.float32),
        "hf_maxmin": np.array([0.3, 0.0], dtype=np.float32),
        "min_point": np.array([-0.5, -0.5, 0.0], dtype=np.float32),
        "dx": 0.25,
    }
    container = {
        "motion_data": pickle.dumps(motion_payload),
        "terrain_data": pickle.dumps(terrain_payload),
        "misc_data": pickle.dumps({"hf_mask_inds": [0, 1]}),
    }
    with path.open("wb") as f:
        pickle.dump(container, f)
    return path


def _write_negative_terrain_parc_sample(path: Path, *, frames: int = 4) -> Path:
    root_pos = np.zeros((frames, 3), dtype=np.float32)
    root_pos[:, 2] = np.linspace(-0.7, 0.2, frames, dtype=np.float32)
    root_rot = np.tile(np.array([[0.0, 0.0, 0.0, 1.0]], dtype=np.float32), (frames, 1))
    joint_rot = np.tile(np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32), (frames, len(BODY_NAMES) - 1, 1))
    motion_payload = {
        "root_pos": root_pos,
        "root_rot": root_rot,
        "joint_rot": joint_rot,
        "body_contacts": np.zeros((frames, 2), dtype=np.float32),
        "fps": 30,
        "loop_mode": "wrap",
    }
    terrain_payload = {
        "hf": np.array([[-1.2, -1.2], [-0.6, 0.0]], dtype=np.float32),
        "hf_maxmin": np.array([0.0, -1.2], dtype=np.float32),
        "min_point": np.array([-0.5, -0.5, 0.0], dtype=np.float32),
        "dx": 0.25,
    }
    container = {
        "motion_data": pickle.dumps(motion_payload),
        "terrain_data": pickle.dumps(terrain_payload),
        "misc_data": pickle.dumps({"hf_mask_inds": [0, 1]}),
    }
    with path.open("wb") as f:
        pickle.dump(container, f)
    return path


@pytest.fixture()
def synthetic_parc_paths(tmp_path: Path) -> tuple[Path, Path]:
    return _write_parc_sample(tmp_path / "sample.pkl"), _write_humanoid_xml(tmp_path / "humanoid.xml")


def test_parc_process_cli_accepts_source_and_output_paths() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--sample",
            "/tmp/sample.pkl",
            "--source-xml",
            "/tmp/humanoid.xml",
            "--output-root",
            "/tmp/out",
        ]
    )

    assert isinstance(args.sample, Path)
    assert str(args.sample).endswith("sample.pkl")
    assert str(args.source_xml).endswith("humanoid.xml")
    assert str(args.output_root).endswith("out")


def test_parc_humanoid_format_is_registered_for_g1() -> None:
    cfg = MotionDataConfig(data_format="parc_humanoid", robot_type="g1")

    assert "pelvis" in cfg.resolved_demo_joints
    assert cfg.resolved_joints_mapping["left_foot"] == "left_ankle_intermediate_1_link"
    assert cfg.toe_names == ["left_foot", "right_foot"]
    assert cfg.default_human_height == pytest.approx(1.70)


def test_load_parc_sample_reads_pickled_payload(synthetic_parc_paths: tuple[Path, Path]) -> None:
    sample_path, _ = synthetic_parc_paths

    result = load_parc_sample(sample_path)

    assert result.motion_data.root_pos.shape == (4, 3)
    assert result.motion_data.joint_rot.shape == (4, 14, 4)
    assert result.terrain_data.hf.shape == (2, 2)
    assert "hf_mask_inds" in result.misc_data


def test_build_source_joint_positions_returns_world_joints(synthetic_parc_paths: tuple[Path, Path]) -> None:
    sample_path, xml_path = synthetic_parc_paths
    sample = load_parc_sample(sample_path)

    joint_positions, joint_names = build_source_joint_positions(sample.motion_data, xml_path)

    assert joint_positions.shape == (4, 15, 3)
    assert joint_names == BODY_NAMES


def test_parc_workspace_is_accepted_by_climbing_loader(
    tmp_path: Path,
    synthetic_parc_paths: tuple[Path, Path],
) -> None:
    sample_path, xml_path = synthetic_parc_paths
    sample = load_parc_sample(sample_path)
    workspace = build_parc_workspace(
        sample=sample,
        source_xml=xml_path,
        output_dir=tmp_path,
        task_name="sample",
    )

    cfg = RetargetingConfig(task_type="climbing", data_format="parc_humanoid", task_name="sample", data_path=tmp_path)
    validate_config(cfg)

    human_joints, object_poses, smpl_scale = load_motion_data(
        task_type="climbing",
        data_format="parc_humanoid",
        data_path=tmp_path,
        task_name="sample",
        constants=SimpleNamespace(ROBOT_HEIGHT=1.32),
        motion_data_config=MotionDataConfig(data_format="parc_humanoid", robot_type="g1"),
    )

    assert workspace.scene_xml_path.name == "g1_29dof_w_multi_boxes.xml"
    assert human_joints.shape == (4, 15, 3)
    assert object_poses.shape == (4, 7)
    assert smpl_scale > 0.0


def test_parc_workspace_normalizes_negative_terrain_with_human_joints(tmp_path: Path) -> None:
    sample_path = _write_negative_terrain_parc_sample(tmp_path / "negative.pkl")
    xml_path = _write_humanoid_xml(tmp_path / "humanoid.xml")
    sample = load_parc_sample(sample_path)

    workspace = build_parc_workspace(
        sample=sample,
        source_xml=xml_path,
        output_dir=tmp_path / "workspace",
        task_name="negative",
    )

    human_joints = np.load(workspace.joints_file)
    terrain_hf = np.load(workspace.terrain_hf_path)
    manifest = json.loads(workspace.terrain_collision_path.read_text(encoding="utf-8"))

    assert workspace.z_origin == pytest.approx(-1.2)
    assert terrain_hf.min() == pytest.approx(0.0)
    assert terrain_hf.max() == pytest.approx(1.2)
    assert human_joints[:, :, 2].min() > 0.0
    assert manifest["source"]["z_origin"] == pytest.approx(-1.2)
    assert manifest["collision"]["base_z"] == pytest.approx(-0.25)


def test_export_parc_scene_writes_obj_and_xml(
    tmp_path: Path,
    synthetic_parc_paths: tuple[Path, Path],
) -> None:
    sample_path, _ = synthetic_parc_paths
    sample = load_parc_sample(sample_path)

    scene = export_parc_scene(sample.terrain_data, tmp_path, object_name="multi_boxes")

    assert scene.obj_path.exists()
    assert scene.asset_xml_path.exists()
    assert scene.scene_xml_path.exists()


def test_export_parc_scene_writes_rl_compatible_heightfield_manifest(
    tmp_path: Path,
    synthetic_parc_paths: tuple[Path, Path],
) -> None:
    sample_path, _ = synthetic_parc_paths
    sample = load_parc_sample(sample_path)

    scene = export_parc_scene(
        sample.terrain_data,
        tmp_path,
        object_name="multi_boxes",
        xy_scale=0.5,
        height_scale=0.5,
        scale_source={"rule": "test scale"},
    )

    manifest = json.loads(scene.terrain_collision_path.read_text(encoding="utf-8"))
    collision = manifest["collision"]

    assert manifest["schema_version"] == 1
    assert manifest["terrain_name"] == "multi_boxes"
    assert manifest["frame"] == {"convention": "z_up", "origin": "motion_world"}
    assert collision["type"] == "heightfield"
    assert collision["hf_file"] == "terrain_hf.npy"
    assert "heightfield_file" not in collision
    assert collision["min_point"] == pytest.approx([-0.5, -0.5])
    assert collision["dx"] == pytest.approx(0.25)
    assert collision["xy_scale"] == pytest.approx(0.5)
    assert collision["height_scale"] == pytest.approx(0.5)
    assert collision["base_z"] == pytest.approx(-0.125)
    assert manifest["visual"] == {"file": "multi_boxes.obj", "role": "visual_only"}
    assert manifest["source"]["format"] == "PARC"
    assert manifest["source"]["scale_source"]["rule"] == "test scale"


def test_compile_sample_dry_run_writes_g1_scaled_heightfield_manifest(
    tmp_path: Path,
    synthetic_parc_paths: tuple[Path, Path],
) -> None:
    sample_path, source_xml = synthetic_parc_paths

    result = compile_sample(
        sample_path=sample_path,
        source_xml=source_xml,
        output_root=tmp_path / "paired",
        retarget_save_dir=tmp_path / "workspace_root",
        robot_type="g1",
        activate_obj_non_penetration=False,
        dry_run=True,
    )

    manifest = json.loads(result.workspace.terrain_collision_path.read_text(encoding="utf-8"))
    collision = manifest["collision"]
    scale = 1.32 / 1.7

    assert collision["type"] == "heightfield"
    assert collision["hf_file"] == "terrain_hf.npy"
    assert collision["xy_scale"] == pytest.approx(scale)
    assert collision["height_scale"] == pytest.approx(scale)
    assert collision["dx"] == pytest.approx(0.25)
    assert collision["base_z"] == pytest.approx(-0.25 * scale)
    assert manifest["source"]["scale_source"]["robot_type"] == "g1"
    assert manifest["source"]["scale_source"]["rule"] == (
        "RobotConfig.ROBOT_HEIGHT / MotionDataConfig.default_human_height"
    )


def test_write_paired_output_emits_manifest_and_motion(
    tmp_path: Path,
    synthetic_parc_paths: tuple[Path, Path],
) -> None:
    sample_path, _ = synthetic_parc_paths
    sample = load_parc_sample(sample_path)
    qpos = np.zeros((4, 36), dtype=np.float32)
    qpos[:, 2] = 0.78
    qpos[:, 3] = 1.0

    result = write_paired_output(
        qpos=qpos,
        source_sample=sample,
        output_root=tmp_path,
        motion_name="sample_g1",
        scale_factor=0.91,
        workspace_path=tmp_path / "workspace",
        retarget_config={"robot": "g1", "task_type": "climbing"},
    )

    motion_data = result.load_motion_file()
    assert motion_data.motion_data.root_pos.shape == (4, 3)
    assert motion_data.motion_data.joint_rot.shape == (4, 29, 4)
    assert motion_data.misc_data["parc_process:scale_factor"] == 0.91
    assert "name: sample_g1" in result.manifest_file.read_text()


def test_write_paired_output_can_emit_normalized_terrain_payload(
    tmp_path: Path,
    synthetic_parc_paths: tuple[Path, Path],
) -> None:
    sample_path, _ = synthetic_parc_paths
    sample = load_parc_sample(sample_path)
    qpos = np.zeros((4, 36), dtype=np.float32)
    qpos[:, 2] = 0.78
    qpos[:, 3] = 1.0
    normalized_hf = np.array([[0.0, 0.5], [0.75, 1.0]], dtype=np.float32)

    result = write_paired_output(
        qpos=qpos,
        source_sample=sample,
        output_root=tmp_path,
        motion_name="sample_g1",
        scale_factor=0.91,
        workspace_path=tmp_path / "workspace",
        terrain_collision_path=tmp_path / "workspace" / "terrain_collision.json",
        terrain_hf_path=tmp_path / "workspace" / "terrain_hf.npy",
        terrain_visual_path=tmp_path / "workspace" / "multi_boxes.obj",
        terrain_payload_override={
            "hf": normalized_hf,
            "hf_maxmin": np.array([1.0, 0.0], dtype=np.float32),
            "min_point": sample.terrain_data.min_point,
            "dx": sample.terrain_data.dx,
        },
        z_origin=-1.2,
        retarget_config={"robot": "g1", "task_type": "climbing"},
    )

    motion_data = result.load_motion_file()
    np.testing.assert_allclose(motion_data.terrain_data.hf, normalized_hf * 0.91)
    np.testing.assert_allclose(motion_data.terrain_data.hf_maxmin, np.array([0.91, 0.0], dtype=np.float32))
    np.testing.assert_allclose(motion_data.terrain_data.min_point, sample.terrain_data.min_point * 0.91)
    assert motion_data.terrain_data.dx == pytest.approx(sample.terrain_data.dx * 0.91)
    assert motion_data.misc_data["parc_process:z_origin"] == pytest.approx(-1.2)


def test_compute_q_init_base_supports_parc_humanoid_climbing() -> None:
    human_joints = np.zeros((1, len(PARC_HUMANOID_DEMO_JOINTS), 3), dtype=np.float64)
    human_joints[0, PARC_HUMANOID_DEMO_JOINTS.index("pelvis")] = np.array([0.0, 0.0, 0.95])
    human_joints[0, PARC_HUMANOID_DEMO_JOINTS.index("torso")] = np.array([0.0, 0.0, 1.18])

    q_init = _compute_q_init_base(
        task_type="climbing",
        data_format="parc_humanoid",
        human_joints=human_joints,
        object_poses=np.array([[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]], dtype=np.float64),
        constants=SimpleNamespace(ROBOT_DOF=29),
        retargeter=SimpleNamespace(demo_joints=PARC_HUMANOID_DEMO_JOINTS),
    )

    assert q_init.shape == (36,)
    np.testing.assert_allclose(q_init[:3], human_joints[0, PARC_HUMANOID_DEMO_JOINTS.index("torso")])


def test_non_penetration_gates_object_pairs_when_object_constraints_disabled() -> None:
    retargeter = SimpleNamespace(
        activate_obj_non_penetration=False,
        object_name="multi_boxes",
        _geom_names=["multi_boxes_collision", "left_foot_collision", "ground"],
    )

    assert not InteractionMeshRetargeter._should_enforce_non_penetration_pair(retargeter, (0, 1))
    assert InteractionMeshRetargeter._should_enforce_non_penetration_pair(retargeter, (1, 2))


def test_transform_from_human_to_world_handles_zero_object_offset() -> None:
    world_translation, quat = transform_from_human_to_world(
        human_initial_root=np.array([0.0, 0.0, 0.5], dtype=np.float64),
        object_initial_pose=np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64),
        local_translation=np.zeros(3, dtype=np.float64),
    )

    np.testing.assert_allclose(world_translation, np.zeros(3, dtype=np.float64))
    np.testing.assert_allclose(quat, np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64))


def test_real_parc_sample_is_optional() -> None:
    sample_path = os.environ.get("PARC_SAMPLE_PATH")
    humanoid_xml = os.environ.get("PARC_HUMANOID_XML")
    if not sample_path or not humanoid_xml:
        pytest.skip("Set PARC_SAMPLE_PATH and PARC_HUMANOID_XML to run the real PARC integration check.")

    sample = load_parc_sample(sample_path)
    joint_positions, joint_names = build_source_joint_positions(sample.motion_data, humanoid_xml)
    assert joint_positions.shape[1] == len(joint_names)
