from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from omniretarget.examples import parc_batch_process_to_mj as batch


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    return path


def test_batch_sample_plan_preserves_initial_aug_relative_layout(tmp_path: Path) -> None:
    source_root = tmp_path / "initial_aug"
    sample = _touch(source_root / "jumping" / "flipped" / "run_jump_gap.pkl")
    output_root = tmp_path / "out"

    plan = batch.build_sample_plan(source_root=source_root, sample_path=sample, output_root=output_root)

    assert plan.relative_dir == Path("jumping/flipped")
    assert plan.paired_output_root == output_root / "parc_process" / "paired" / "jumping" / "flipped"
    assert plan.retarget_save_dir == output_root / "parc_process" / "workspace" / "jumping" / "flipped"
    assert plan.retarget_npz == (
        output_root / "parc_process" / "workspace" / "jumping" / "flipped" / "retargeted" / "run_jump_gap_original.npz"
    )
    assert plan.mj_motion_file == output_root / "mj" / "jumping" / "flipped" / "run_jump_gap" / "motion.npz"


def test_batch_sample_plan_supports_symlinked_canary_sources(tmp_path: Path) -> None:
    raw_sample = _touch(tmp_path / "raw" / "mid_climbing" / "mid_blocks_001.pkl")
    source_root = tmp_path / "canary"
    symlink_sample = source_root / "mid_climbing" / raw_sample.name
    symlink_sample.parent.mkdir(parents=True, exist_ok=True)
    symlink_sample.symlink_to(raw_sample)

    samples = batch.iter_parc_samples(source_root)
    plan = batch.build_sample_plan(source_root=source_root, sample_path=samples[0], output_root=tmp_path / "out")

    assert samples == [symlink_sample]
    assert plan.sample_path == raw_sample.resolve()
    assert plan.relative_dir == Path("mid_climbing")
    assert plan.mj_motion_file == tmp_path / "out" / "mj" / "mid_climbing" / "mid_blocks_001" / "motion.npz"


def test_run_batch_processes_samples_through_parc_and_mj_conversion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "initial_aug"
    sample = _touch(source_root / "platform" / "platform_001.pkl")
    source_xml = _touch(tmp_path / "humanoid.xml")
    robot_xml = _touch(tmp_path / "g1.xml")
    output_root = tmp_path / "out"
    calls: dict[str, list] = {"compile": [], "convert": []}

    def fake_compile_sample(**kwargs):
        calls["compile"].append(kwargs)
        retarget_npz = kwargs["retarget_save_dir"] / "retargeted" / f"{kwargs['sample_path'].stem}_original.npz"
        _touch(retarget_npz)
        return SimpleNamespace(retarget_npz=retarget_npz)

    def fake_convert(config):
        calls["convert"].append(config)
        _touch(config.output_name)
        return config.output_name

    monkeypatch.setattr(batch, "compile_sample", fake_compile_sample)
    monkeypatch.setattr(batch, "convert_parc_qpos_to_motion_file", fake_convert)

    results = batch.run_batch(
        batch.ParcBatchConfig(
            source_root=source_root,
            source_xml=source_xml,
            output_root=output_root,
            robot_xml=robot_xml,
            skip_existing=False,
            continue_on_error=False,
        )
    )

    assert [result.status for result in results] == ["converted"]
    assert calls["compile"][0]["sample_path"] == sample.resolve()
    assert calls["compile"][0]["output_root"] == output_root.resolve() / "parc_process" / "paired" / "platform"
    assert calls["compile"][0]["retarget_save_dir"] == output_root.resolve() / "parc_process" / "workspace" / "platform"
    assert calls["convert"][0].input_file == (
        output_root.resolve() / "parc_process" / "workspace" / "platform" / "retargeted" / "platform_001_original.npz"
    )
    assert calls["convert"][0].output_name == output_root.resolve() / "mj" / "platform" / "platform_001" / "motion.npz"
    assert (output_root / "logs" / "succeeded.txt").read_text(encoding="utf-8").strip() == str(sample.resolve())


def test_run_batch_skips_existing_mj_motion_when_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "initial_aug"
    sample = _touch(source_root / "platform" / "platform_001.pkl")
    output_root = tmp_path / "out"
    _touch(output_root / "mj" / "platform" / "platform_001" / "motion.npz")

    def unexpected_compile_sample(**_kwargs):
        raise AssertionError("compile_sample should not run for existing output")

    monkeypatch.setattr(batch, "compile_sample", unexpected_compile_sample)

    results = batch.run_batch(
        batch.ParcBatchConfig(
            source_root=source_root,
            source_xml=_touch(tmp_path / "humanoid.xml"),
            output_root=output_root,
            robot_xml=_touch(tmp_path / "g1.xml"),
            skip_existing=True,
            continue_on_error=False,
        )
    )

    assert [result.status for result in results] == ["skipped"]
    assert (output_root / "logs" / "skipped.txt").read_text(encoding="utf-8").strip() == str(sample.resolve())


def test_run_batch_continue_on_error_records_failure_and_keeps_going(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_root = tmp_path / "initial_aug"
    bad_sample = _touch(source_root / "jumping" / "bad.pkl")
    good_sample = _touch(source_root / "platform" / "good.pkl")
    output_root = tmp_path / "out"

    def fake_compile_sample(**kwargs):
        if kwargs["sample_path"] == bad_sample.resolve():
            raise RuntimeError("retarget failed")
        retarget_npz = kwargs["retarget_save_dir"] / "retargeted" / f"{kwargs['sample_path'].stem}_original.npz"
        _touch(retarget_npz)
        return SimpleNamespace(retarget_npz=retarget_npz)

    def fake_convert(config):
        _touch(config.output_name)
        return config.output_name

    monkeypatch.setattr(batch, "compile_sample", fake_compile_sample)
    monkeypatch.setattr(batch, "convert_parc_qpos_to_motion_file", fake_convert)

    results = batch.run_batch(
        batch.ParcBatchConfig(
            source_root=source_root,
            source_xml=_touch(tmp_path / "humanoid.xml"),
            output_root=output_root,
            robot_xml=_touch(tmp_path / "g1.xml"),
            skip_existing=False,
            continue_on_error=True,
        )
    )

    assert [result.status for result in results] == ["failed", "converted"]
    assert str(bad_sample.resolve()) in (output_root / "logs" / "failed.txt").read_text(encoding="utf-8")
    assert (output_root / "mj" / "platform" / "good" / "motion.npz").exists()


def test_batch_wrapper_exposes_initial_aug_to_mj_entrypoint() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "parc" / "batch_parc_initial_aug_to_mj.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")
    assert "omniretarget.examples.parc_batch_process_to_mj" in content
    assert "--skip-existing" in content
    assert "--continue-on-error" in content


def test_parc_shell_scripts_expose_process_convert_and_vis() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    run_script = repo_root / "scripts" / "parc" / "run_parc_process.sh"
    convert_script = repo_root / "scripts" / "parc" / "convert_parc_to_mj.sh"
    vis_script = repo_root / "scripts" / "parc" / "vis_parc_process.sh"

    assert run_script.is_file()
    assert convert_script.is_file()
    assert vis_script.is_file()
    assert "examples/parc_process.py" in run_script.read_text(encoding="utf-8")
    assert "omniretarget.data_conversion.convert_data_format_parc_mj" in convert_script.read_text(
        encoding="utf-8"
    )
    assert "viser_player.py" in vis_script.read_text(encoding="utf-8")
    assert "--no-assume-object-in-qpos" in vis_script.read_text(encoding="utf-8")
