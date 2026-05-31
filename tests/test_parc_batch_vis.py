from __future__ import annotations

import json
from pathlib import Path

import pytest

from omniretarget.parc_process.batch_vis import (
    append_review_record,
    default_review_file,
    discover_playlist,
    load_latest_reviews,
    read_task_list,
)


def _write_npz_marker(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"npz marker")


def _make_sample(root: Path, dataset: str, task: str, *, scaled: bool = True, unscaled: bool = True) -> None:
    _write_npz_marker(root / "parc_process" / "workspace" / dataset / "retargeted" / f"{task}_original.npz")
    workspace = root / "parc_process" / "workspace" / dataset / "workspace" / task
    workspace.mkdir(parents=True, exist_ok=True)
    if unscaled:
        (workspace / "multi_boxes.urdf").write_text("<robot name='unscaled'/>\n", encoding="utf-8")
    if scaled:
        (workspace / "multi_boxes_scaled_0.78_0.78_0.78.urdf").write_text(
            "<robot name='scaled'/>\n", encoding="utf-8"
        )


def test_discover_playlist_prefers_scaled_terrain(tmp_path: Path) -> None:
    _make_sample(tmp_path, "mid_climbing", "mid_blocks_001_dm", scaled=True, unscaled=True)

    playlist = discover_playlist(output_root=tmp_path, dataset="mid_climbing")

    assert [sample.task for sample in playlist] == ["mid_blocks_001_dm"]
    assert playlist[0].index == 0
    assert playlist[0].qpos_npz.name == "mid_blocks_001_dm_original.npz"
    assert playlist[0].object_urdf is not None
    assert playlist[0].object_urdf.name == "multi_boxes_scaled_0.78_0.78_0.78.urdf"


def test_discover_playlist_falls_back_to_unscaled_terrain(tmp_path: Path) -> None:
    _make_sample(tmp_path, "mid_climbing", "mid_blocks_004_dm", scaled=False, unscaled=True)

    playlist = discover_playlist(output_root=tmp_path, dataset="mid_climbing")

    assert playlist[0].object_urdf is not None
    assert playlist[0].object_urdf.name == "multi_boxes.urdf"


def test_discover_playlist_allows_missing_terrain(tmp_path: Path) -> None:
    _make_sample(tmp_path, "mid_climbing", "unreal_beyond_001_dm", scaled=False, unscaled=False)

    playlist = discover_playlist(output_root=tmp_path, dataset="mid_climbing")

    assert playlist[0].task == "unreal_beyond_001_dm"
    assert playlist[0].object_urdf is None


def test_task_list_filters_and_preserves_order(tmp_path: Path) -> None:
    _make_sample(tmp_path, "mid_climbing", "a_task")
    _make_sample(tmp_path, "mid_climbing", "b_task")
    _make_sample(tmp_path, "mid_climbing", "c_task")
    task_list = tmp_path / "tasks.txt"
    task_list.write_text("# comment\nc_task\n\na_task\n", encoding="utf-8")

    playlist = discover_playlist(output_root=tmp_path, dataset="mid_climbing", task_list=task_list)

    assert [sample.task for sample in playlist] == ["c_task", "a_task"]
    assert [sample.index for sample in playlist] == [0, 1]


def test_task_list_reports_missing_entries(tmp_path: Path) -> None:
    _make_sample(tmp_path, "mid_climbing", "a_task")
    task_list = tmp_path / "tasks.txt"
    task_list.write_text("a_task\nmissing_task\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="missing_task"):
        discover_playlist(output_root=tmp_path, dataset="mid_climbing", task_list=task_list)


def test_empty_playlist_reports_scanned_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="retargeted"):
        discover_playlist(output_root=tmp_path, dataset="mid_climbing")


def test_read_task_list_ignores_blank_lines_and_comments(tmp_path: Path) -> None:
    path = tmp_path / "tasks.txt"
    path.write_text("\n# skip me\nmid_blocks_001_dm\n  unreal_beyond_001_dm  \n", encoding="utf-8")

    assert read_task_list(path) == ["mid_blocks_001_dm", "unreal_beyond_001_dm"]


def test_review_jsonl_append_and_latest_status(tmp_path: Path) -> None:
    _make_sample(tmp_path, "mid_climbing", "mid_blocks_001_dm")
    sample = discover_playlist(output_root=tmp_path, dataset="mid_climbing")[0]
    review_file = tmp_path / "vis_review" / "mid_climbing_review.jsonl"

    append_review_record(review_file, sample, status="fail", note="terrain mismatch")
    append_review_record(review_file, sample, status="pass", note="fixed after rerun")

    records = review_file.read_text(encoding="utf-8").splitlines()
    assert len(records) == 2
    latest = load_latest_reviews(review_file)
    assert latest["mid_blocks_001_dm"].status == "pass"
    assert latest["mid_blocks_001_dm"].note == "fixed after rerun"
    assert json.loads(records[-1])["object_urdf"].endswith("multi_boxes_scaled_0.78_0.78_0.78.urdf")


def test_default_review_file(tmp_path: Path) -> None:
    assert default_review_file(tmp_path, "mid_climbing") == tmp_path / "vis_review" / "mid_climbing_review.jsonl"


def test_invalid_review_status_is_rejected(tmp_path: Path) -> None:
    _make_sample(tmp_path, "mid_climbing", "mid_blocks_001_dm")
    sample = discover_playlist(output_root=tmp_path, dataset="mid_climbing")[0]

    with pytest.raises(ValueError, match="invalid"):
        append_review_record(tmp_path / "review.jsonl", sample, status="approved", note="")
