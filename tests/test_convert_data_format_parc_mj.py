from __future__ import annotations

from pathlib import Path

import numpy as np

from omniretarget.data_conversion.convert_data_format_parc_mj import (
    DEFAULT_G1_XML_PATH,
    ParcMjConversionConfig,
    build_arg_parser,
    convert_parc_qpos_to_motion_file,
)


def _write_qpos_npz(path: Path, *, fps: int = 30, num_frames: int = 4) -> Path:
    qpos = np.zeros((num_frames, 36), dtype=np.float32)
    qpos[:, 2] = np.linspace(0.78, 0.80, num_frames, dtype=np.float32)
    qpos[:, 3] = 1.0
    qpos[:, 7] = np.linspace(0.0, 0.3, num_frames, dtype=np.float32)
    np.savez(path, qpos=qpos, fps=np.asarray(fps, dtype=np.int32))
    return path


def test_parc_mj_cli_accepts_input_output_and_robot_xml() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--input-file",
            "/tmp/input.npz",
            "--output-name",
            "/tmp/output.npz",
            "--robot-xml",
            "/tmp/g1.xml",
        ]
    )

    assert str(args.input_file).endswith("input.npz")
    assert str(args.output_name).endswith("output.npz")
    assert str(args.robot_xml).endswith("g1.xml")


def test_parc_mj_cli_defaults_to_workspace_g1_xml() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--input-file",
            "/tmp/input.npz",
            "--output-name",
            "/tmp/output.npz",
        ]
    )

    assert Path(args.robot_xml) == DEFAULT_G1_XML_PATH
    assert DEFAULT_G1_XML_PATH.name == "g1_mj.xml"
    assert DEFAULT_G1_XML_PATH.exists()


def test_convert_parc_qpos_to_motion_file_emits_mjlab_fields(tmp_path: Path) -> None:
    input_file = _write_qpos_npz(tmp_path / "input_qpos.npz")
    output_file = tmp_path / "motion.npz"

    convert_parc_qpos_to_motion_file(
        ParcMjConversionConfig(
            input_file=input_file,
            output_name=output_file,
            robot_xml=DEFAULT_G1_XML_PATH,
            output_fps=50,
        )
    )

    with np.load(output_file) as data:
        assert set(data.files) >= {
            "fps",
            "joint_pos",
            "joint_vel",
            "body_pos_w",
            "body_quat_w",
            "body_lin_vel_w",
            "body_ang_vel_w",
        }
        assert int(np.asarray(data["fps"]).item()) == 50
        assert data["joint_pos"].ndim == 2
        assert data["joint_pos"].shape[1] == 29
        assert data["joint_vel"].shape == data["joint_pos"].shape
        assert data["body_pos_w"].shape[0] == data["joint_pos"].shape[0]
        assert data["body_pos_w"].shape[1] == 30
        assert data["body_pos_w"].shape[-1] == 3
        assert data["body_quat_w"].shape[:2] == data["body_pos_w"].shape[:2]
        assert data["body_quat_w"].shape[-1] == 4
        assert data["body_lin_vel_w"].shape == data["body_pos_w"].shape
        assert data["body_ang_vel_w"].shape == data["body_pos_w"].shape
        assert np.all(data["body_pos_w"][:, 0, 2] > 0.5)
        quat_norm = np.linalg.norm(data["body_quat_w"], axis=-1)
        assert np.allclose(quat_norm, 1.0, atol=1e-4)
