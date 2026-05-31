# PARC Batch Visualization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a one-server PARC batch viser player for reviewing converted `mid_climbing` samples with in-browser sample switching and pass/fail review records.

**Architecture:** Put testable playlist discovery and review-log logic in `omniretarget.parc_process.batch_vis`. Add a PARC-specific GUI entrypoint in `omniretarget.examples.parc_batch_vis` that owns mutable viser playback state and uses the pure module for paths and review status. Add a shell wrapper under `scripts/parc` while preserving the existing single-sample visualization script.

**Tech Stack:** Python 3.12, `argparse`, `dataclasses`, `jsonl`, `numpy`, `viser`, `yourdfpy`, Bash, pytest.

---

## File Structure

- Create `src/omniretarget/parc_process/batch_vis.py`
  - Owns `ParcVisSample`, `ReviewRecord`, playlist discovery, task-list parsing, default review-file resolution, JSONL append, and latest-review loading.
  - Does not import `viser`, `yourdfpy`, or any browser/runtime dependencies.
- Create `src/omniretarget/examples/parc_batch_vis.py`
  - Owns CLI parsing, preflight, one `viser.ViserServer`, mutable playback state, sample switching, review buttons, and process lifetime.
  - Imports `viser` and `yourdfpy` inside runtime code so pure tests can import parser helpers without requiring a live browser.
- Create `scripts/parc/vis_parc_batch.sh`
  - Maps `OUTPUT_ROOT`, `PARC_DATASET`, `TASK_LIST`, `REVIEW_FILE`, and `ROBOT_URDF` env vars to the Python CLI.
- Create `tests/test_parc_batch_vis.py`
  - Covers playlist discovery, scaled-terrain preference, task-list filtering, review JSONL latest-status behavior, CLI config construction, and shell wrapper forwarding with fake `uv`.

## Task 1: Pure Playlist And Review Logic

**Files:**
- Create: `src/omniretarget/parc_process/batch_vis.py`
- Create: `tests/test_parc_batch_vis.py`

- [ ] **Step 1: Write failing tests for playlist discovery and review records**

Add these tests to `tests/test_parc_batch_vis.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -q tests/test_parc_batch_vis.py
```

Expected: FAIL during import with `ModuleNotFoundError: No module named 'omniretarget.parc_process.batch_vis'`.

- [ ] **Step 3: Implement the pure batch-vis module**

Create `src/omniretarget/parc_process/batch_vis.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

VALID_REVIEW_STATUSES = frozenset({"pass", "fail", "needs_review", "skip"})


@dataclass(frozen=True)
class ParcVisSample:
    task: str
    index: int
    qpos_npz: Path
    object_urdf: Path | None


@dataclass(frozen=True)
class ReviewRecord:
    task: str
    status: str
    note: str
    qpos_npz: Path
    object_urdf: Path | None
    timestamp: str


def retargeted_dir(output_root: Path, dataset: str) -> Path:
    return output_root.expanduser().resolve() / "parc_process" / "workspace" / dataset / "retargeted"


def workspace_dir(output_root: Path, dataset: str) -> Path:
    return output_root.expanduser().resolve() / "parc_process" / "workspace" / dataset / "workspace"


def default_review_file(output_root: Path, dataset: str) -> Path:
    return output_root.expanduser().resolve() / "vis_review" / f"{dataset}_review.jsonl"


def task_from_retargeted_npz(path: Path) -> str:
    suffix = "_original.npz"
    if not path.name.endswith(suffix):
        raise ValueError(f"retargeted qpos file must end with {suffix!r}: {path}")
    return path.name[: -len(suffix)]


def read_task_list(path: Path) -> list[str]:
    tasks: list[str] = []
    for raw_line in path.expanduser().read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        tasks.append(line)
    return tasks


def resolve_object_urdf(output_root: Path, dataset: str, task: str) -> Path | None:
    task_workspace = workspace_dir(output_root, dataset) / task
    scaled = sorted(task_workspace.glob("multi_boxes_scaled_*.urdf"))
    if scaled:
        return scaled[0].resolve()
    unscaled = task_workspace / "multi_boxes.urdf"
    if unscaled.exists():
        return unscaled.resolve()
    return None


def _samples_by_task(output_root: Path, dataset: str) -> dict[str, ParcVisSample]:
    root = output_root.expanduser().resolve()
    qpos_root = retargeted_dir(root, dataset)
    if not qpos_root.is_dir():
        raise FileNotFoundError(f"retargeted directory does not exist: {qpos_root}")

    samples: dict[str, ParcVisSample] = {}
    for qpos_npz in sorted(qpos_root.glob("*_original.npz")):
        task = task_from_retargeted_npz(qpos_npz)
        samples[task] = ParcVisSample(
            task=task,
            index=-1,
            qpos_npz=qpos_npz.resolve(),
            object_urdf=resolve_object_urdf(root, dataset, task),
        )
    if not samples:
        raise FileNotFoundError(f"no retargeted qpos files found in: {qpos_root}")
    return samples


def discover_playlist(output_root: Path, dataset: str, task_list: Path | None = None) -> list[ParcVisSample]:
    samples = _samples_by_task(output_root, dataset)
    if task_list is None:
        ordered = [samples[task] for task in sorted(samples)]
    else:
        tasks = read_task_list(task_list)
        missing = [task for task in tasks if task not in samples]
        if missing:
            raise FileNotFoundError(f"task-list entries missing retargeted qpos files: {', '.join(missing)}")
        ordered = [samples[task] for task in tasks]
    return [
        ParcVisSample(task=sample.task, index=index, qpos_npz=sample.qpos_npz, object_urdf=sample.object_urdf)
        for index, sample in enumerate(ordered)
    ]


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def append_review_record(
    review_file: Path,
    sample: ParcVisSample,
    *,
    status: str,
    note: str,
    timestamp: str | None = None,
) -> ReviewRecord:
    if status not in VALID_REVIEW_STATUSES:
        raise ValueError(f"invalid review status {status!r}; expected one of {sorted(VALID_REVIEW_STATUSES)}")
    record = ReviewRecord(
        task=sample.task,
        status=status,
        note=note,
        qpos_npz=sample.qpos_npz,
        object_urdf=sample.object_urdf,
        timestamp=timestamp or _now_timestamp(),
    )
    review_file = review_file.expanduser().resolve()
    review_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "task": record.task,
        "status": record.status,
        "note": record.note,
        "qpos_npz": str(record.qpos_npz),
        "object_urdf": str(record.object_urdf) if record.object_urdf is not None else None,
        "timestamp": record.timestamp,
    }
    with review_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")
    return record


def _record_from_payload(payload: dict[str, object]) -> ReviewRecord:
    task = str(payload["task"])
    status = str(payload["status"])
    if status not in VALID_REVIEW_STATUSES:
        raise ValueError(f"invalid review status {status!r} for task {task!r}")
    object_urdf_raw = payload.get("object_urdf")
    return ReviewRecord(
        task=task,
        status=status,
        note=str(payload.get("note", "")),
        qpos_npz=Path(str(payload["qpos_npz"])),
        object_urdf=Path(str(object_urdf_raw)) if object_urdf_raw else None,
        timestamp=str(payload.get("timestamp", "")),
    )


def load_latest_reviews(review_file: Path) -> dict[str, ReviewRecord]:
    review_file = review_file.expanduser()
    if not review_file.exists():
        return {}
    latest: dict[str, ReviewRecord] = {}
    for line_number, line in enumerate(review_file.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
            record = _record_from_payload(payload)
        except Exception as exc:
            raise ValueError(f"invalid review record at {review_file}:{line_number}: {exc}") from exc
        latest[record.task] = record
    return latest


def first_unreviewed_index(samples: Iterable[ParcVisSample], latest_reviews: dict[str, ReviewRecord], start: int) -> int:
    sample_list = list(samples)
    if not sample_list:
        raise ValueError("sample list is empty")
    for offset in range(1, len(sample_list) + 1):
        index = (start + offset) % len(sample_list)
        if sample_list[index].task not in latest_reviews:
            return index
    return start
```

- [ ] **Step 4: Run tests to verify Task 1 passes**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -q tests/test_parc_batch_vis.py
```

Expected: PASS for the tests added in Task 1.

- [ ] **Step 5: Commit Task 1**

```bash
git add src/omniretarget/parc_process/batch_vis.py tests/test_parc_batch_vis.py
git commit -m "feat: add PARC batch vis playlist logic"
```

## Task 2: CLI Configuration And Shell Wrapper

**Files:**
- Create: `src/omniretarget/examples/parc_batch_vis.py`
- Create: `scripts/parc/vis_parc_batch.sh`
- Modify: `tests/test_parc_batch_vis.py`

- [ ] **Step 1: Add failing tests for CLI defaults and shell forwarding**

Append to `tests/test_parc_batch_vis.py`:

```python
import os
import subprocess

from omniretarget.examples.parc_batch_vis import build_arg_parser, config_from_args


def test_parc_batch_vis_cli_defaults_review_file(tmp_path: Path) -> None:
    args = build_arg_parser().parse_args(["--output-root", str(tmp_path), "--dataset", "mid_climbing"])
    config = config_from_args(args)

    assert config.output_root == tmp_path.resolve()
    assert config.dataset == "mid_climbing"
    assert config.review_file == tmp_path.resolve() / "vis_review" / "mid_climbing_review.jsonl"
    assert config.task_list is None
    assert config.loop is True


def test_parc_batch_vis_cli_accepts_task_list_and_no_loop(tmp_path: Path) -> None:
    task_list = tmp_path / "tasks.txt"
    task_list.write_text("mid_blocks_001_dm\n", encoding="utf-8")

    args = build_arg_parser().parse_args(
        [
            "--output-root",
            str(tmp_path),
            "--dataset",
            "mid_climbing",
            "--task-list",
            str(task_list),
            "--review-file",
            str(tmp_path / "custom.jsonl"),
            "--start-task",
            "mid_blocks_001_dm",
            "--no-loop",
        ]
    )
    config = config_from_args(args)

    assert config.task_list == task_list.resolve()
    assert config.review_file == (tmp_path / "custom.jsonl").resolve()
    assert config.start_task == "mid_blocks_001_dm"
    assert config.loop is False


def test_vis_parc_batch_shell_forwards_env_and_args(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    capture_file = tmp_path / "uv_args.txt"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                'printf "%s\\n" "$@" > "${CAPTURE_FILE}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)

    task_list = tmp_path / "tasks.txt"
    task_list.write_text("mid_blocks_001_dm\n", encoding="utf-8")
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["CAPTURE_FILE"] = str(capture_file)
    env["OUTPUT_ROOT"] = str(tmp_path / "out")
    env["PARC_DATASET"] = "mid_climbing"
    env["TASK_LIST"] = str(task_list)
    env["REVIEW_FILE"] = str(tmp_path / "review.jsonl")
    env["ROBOT_URDF"] = "models/g1/g1_29dof_spherehand.urdf"

    subprocess.run(
        ["bash", str(repo_root / "scripts" / "parc" / "vis_parc_batch.sh"), "--start-task", "mid_blocks_001_dm"],
        cwd=repo_root,
        env=env,
        check=True,
    )

    args = capture_file.read_text(encoding="utf-8").splitlines()
    assert args[:3] == ["run", "python", "-m"]
    assert args[3] == "omniretarget.examples.parc_batch_vis"
    assert args[args.index("--output-root") + 1] == str(tmp_path / "out")
    assert args[args.index("--dataset") + 1] == "mid_climbing"
    assert args[args.index("--task-list") + 1] == str(task_list)
    assert args[args.index("--review-file") + 1] == str(tmp_path / "review.jsonl")
    assert args[args.index("--robot-urdf") + 1] == "models/g1/g1_29dof_spherehand.urdf"
    assert args[-2:] == ["--start-task", "mid_blocks_001_dm"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -q tests/test_parc_batch_vis.py
```

Expected: FAIL because `omniretarget.examples.parc_batch_vis` and `scripts/parc/vis_parc_batch.sh` do not exist.

- [ ] **Step 3: Implement CLI config and shell wrapper**

Create `src/omniretarget/examples/parc_batch_vis.py` with the CLI/config portion first:

```python
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from omniretarget.parc_process.batch_vis import default_review_file
from omniretarget.path_utils import package_path


@dataclass(frozen=True)
class ParcBatchVisConfig:
    output_root: Path
    dataset: str
    task_list: Path | None
    review_file: Path
    robot_urdf: Path
    loop: bool
    start_task: str | None
    fps: int | None
    grid_width: float
    grid_height: float
    visual_fps_multiplier: int
    show_meshes: bool


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch visualize PARC retargeted samples in one viser server.")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--task-list", type=Path, default=None)
    parser.add_argument("--review-file", type=Path, default=None)
    parser.add_argument("--robot-urdf", type=Path, default=package_path("models/g1/g1_29dof_spherehand.urdf"))
    parser.add_argument("--loop", dest="loop", action="store_true", default=True)
    parser.add_argument("--no-loop", dest="loop", action="store_false")
    parser.add_argument("--start-task", default=None)
    parser.add_argument("--fps", type=int, default=None)
    parser.add_argument("--grid-width", type=float, default=8.0)
    parser.add_argument("--grid-height", type=float, default=8.0)
    parser.add_argument("--visual-fps-multiplier", type=int, default=2)
    parser.add_argument("--show-meshes", dest="show_meshes", action="store_true", default=True)
    parser.add_argument("--no-show-meshes", dest="show_meshes", action="store_false")
    return parser


def config_from_args(args: argparse.Namespace) -> ParcBatchVisConfig:
    output_root = args.output_root.expanduser().resolve()
    task_list = args.task_list.expanduser().resolve() if args.task_list is not None else None
    review_file = (
        args.review_file.expanduser().resolve()
        if args.review_file is not None
        else default_review_file(output_root, args.dataset)
    )
    return ParcBatchVisConfig(
        output_root=output_root,
        dataset=args.dataset,
        task_list=task_list,
        review_file=review_file,
        robot_urdf=args.robot_urdf.expanduser().resolve(),
        loop=bool(args.loop),
        start_task=args.start_task,
        fps=args.fps,
        grid_width=float(args.grid_width),
        grid_height=float(args.grid_height),
        visual_fps_multiplier=int(args.visual_fps_multiplier),
        show_meshes=bool(args.show_meshes),
    )
```

Create `scripts/parc/vis_parc_batch.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

cd "${REPO_ROOT}"

OUTPUT_ROOT="${OUTPUT_ROOT:-/home/humanoid/Downloads/Data/parc_initial_aug_g1_v2_height_fixed_mid_climbing_full_20260531}"
PARC_DATASET="${PARC_DATASET:-mid_climbing}"
ROBOT_URDF="${ROBOT_URDF:-src/omniretarget/models/g1/g1_29dof_spherehand.urdf}"

args=(
  python -m omniretarget.examples.parc_batch_vis
  --output-root "${OUTPUT_ROOT}"
  --dataset "${PARC_DATASET}"
  --robot-urdf "${ROBOT_URDF}"
)

if [[ -n "${TASK_LIST:-}" ]]; then
  args+=(--task-list "${TASK_LIST}")
fi

if [[ -n "${REVIEW_FILE:-}" ]]; then
  args+=(--review-file "${REVIEW_FILE}")
fi

uv run "${args[@]}" "$@"
```

Make the script executable:

```bash
chmod +x scripts/parc/vis_parc_batch.sh
```

- [ ] **Step 4: Run tests to verify Task 2 passes**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -q tests/test_parc_batch_vis.py
```

Expected: PASS for Task 1 and Task 2 tests. At this point the module exposes config helpers only; the runnable viewer entrypoint is added in Task 3.

- [ ] **Step 5: Commit Task 2**

```bash
git add src/omniretarget/examples/parc_batch_vis.py scripts/parc/vis_parc_batch.sh tests/test_parc_batch_vis.py
git commit -m "feat: add PARC batch vis CLI"
```

## Task 3: Mutable Batch Viser Runtime

**Files:**
- Modify: `src/omniretarget/examples/parc_batch_vis.py`
- Modify: `tests/test_parc_batch_vis.py`

- [ ] **Step 1: Add focused tests for start-task validation and next-unreviewed helper**

Append to `tests/test_parc_batch_vis.py`:

```python
from omniretarget.parc_process.batch_vis import first_unreviewed_index


def test_first_unreviewed_index_wraps_from_current_position(tmp_path: Path) -> None:
    _make_sample(tmp_path, "mid_climbing", "a_task")
    _make_sample(tmp_path, "mid_climbing", "b_task")
    _make_sample(tmp_path, "mid_climbing", "c_task")
    samples = discover_playlist(output_root=tmp_path, dataset="mid_climbing")
    review_file = tmp_path / "review.jsonl"
    append_review_record(review_file, samples[1], status="pass", note="")
    latest = load_latest_reviews(review_file)

    assert first_unreviewed_index(samples, latest, start=0) == 2
    assert first_unreviewed_index(samples, latest, start=2) == 0


def test_first_unreviewed_returns_current_when_all_reviewed(tmp_path: Path) -> None:
    _make_sample(tmp_path, "mid_climbing", "a_task")
    _make_sample(tmp_path, "mid_climbing", "b_task")
    samples = discover_playlist(output_root=tmp_path, dataset="mid_climbing")
    review_file = tmp_path / "review.jsonl"
    for sample in samples:
        append_review_record(review_file, sample, status="pass", note="")

    assert first_unreviewed_index(samples, load_latest_reviews(review_file), start=1) == 1
```

- [ ] **Step 2: Run tests to verify helper coverage**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -q tests/test_parc_batch_vis.py
```

Expected: PASS if Task 1 already implemented `first_unreviewed_index`; otherwise FAIL and add the function exactly as shown in Task 1.

- [ ] **Step 3: Add the runtime entrypoint and `ParcBatchViserPlayer` implementation**

In `src/omniretarget/examples/parc_batch_vis.py`, add runtime imports inside the methods and implement the player with this structure:

```python
import threading
import time
from typing import Any

import numpy as np

from omniretarget.parc_process.batch_vis import (
    ParcVisSample,
    append_review_record,
    discover_playlist,
    first_unreviewed_index,
    load_latest_reviews,
)


def _load_qpos(npz_path: Path) -> tuple[np.ndarray, int]:
    data = np.load(npz_path, allow_pickle=True)
    qpos = data["qpos"]
    fps = int(data["fps"]) if "fps" in data else 30
    return qpos, fps


def run_batch_viewer(config: ParcBatchVisConfig) -> None:
    samples = discover_playlist(config.output_root, config.dataset, config.task_list)
    player = ParcBatchViserPlayer(config, samples)
    player.start()
    while True:
        time.sleep(1.0)


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    config = config_from_args(args)
    run_batch_viewer(config)
    return 0


class ParcBatchViserPlayer:
    def __init__(self, config: ParcBatchVisConfig, samples: list[ParcVisSample]):
        if not samples:
            raise ValueError("samples must not be empty")
        self.config = config
        self.samples = samples
        self.current_index = self._initial_index()
        self.qpos: np.ndarray | None = None
        self.source_fps = int(config.fps) if config.fps is not None else 30
        self.robot_dof = 0
        self.playing = False
        self.frame_f = 0.0
        self.prev_robot_q: np.ndarray | None = None
        self.server: Any = None
        self.robot_root: Any = None
        self.object_root: Any = None
        self.robot_urdf: Any = None
        self.object_urdf: Any = None
        self.sample_dropdown: Any = None
        self.frame_slider: Any = None
        self.playback_folder: Any = None
        self.fps_input: Any = None
        self.interp_mult_input: Any = None
        self.note_input: Any = None
        self.status_md: Any = None
        self.path_md: Any = None
        self.error_md: Any = None
        self.show_meshes_cb: Any = None
        self._programmatic_slider_update = False
        self._programmatic_sample_update = False
        self._lock = threading.RLock()

    def _initial_index(self) -> int:
        if self.config.start_task is None:
            return 0
        for index, sample in enumerate(self.samples):
            if sample.task == self.config.start_task:
                return index
        raise ValueError(f"--start-task not found in playlist: {self.config.start_task}")

    def start(self) -> None:
        import viser

        self.server = viser.ViserServer()
        self.robot_root = self.server.scene.add_frame("/robot", show_axes=False)
        self.object_root = self.server.scene.add_frame("/object", show_axes=False)
        self.server.scene.add_grid(
            "/grid",
            width=self.config.grid_width,
            height=self.config.grid_height,
            position=(0.0, 0.0, 0.0),
        )
        self._build_gui()
        self._load_sample(self.current_index)
        threading.Thread(target=self._player_loop, daemon=True).start()
        print(f"[parc_batch_vis] Loaded {len(self.samples)} samples. Open the viser URL printed above.")
```

Then add these methods in the same class:

```python
    def _build_gui(self) -> None:
        task_options = [sample.task for sample in self.samples]
        with self.server.gui.add_folder("Dataset"):
            self.sample_dropdown = self.server.gui.add_dropdown(
                "Sample",
                options=task_options,
                initial_value=task_options[self.current_index],
            )
            prev_btn = self.server.gui.add_button("Prev")
            next_btn = self.server.gui.add_button("Next")
            next_unreviewed_btn = self.server.gui.add_button("Next Unreviewed")
            self.status_md = self.server.gui.add_markdown("")
            self.path_md = self.server.gui.add_markdown("")
            self.error_md = self.server.gui.add_markdown("")

        self.playback_folder = self.server.gui.add_folder("Playback")
        with self.playback_folder:
            self._replace_frame_slider(n_frames=1)
            play_btn = self.server.gui.add_button("Play / Pause")
            self.fps_input = self.server.gui.add_number(
                "FPS",
                initial_value=int(self.config.fps or 30),
                min=1,
                max=240,
                step=1,
            )
            self.interp_mult_input = self.server.gui.add_number(
                "Visual FPS multiplier",
                initial_value=int(self.config.visual_fps_multiplier),
                min=1,
                max=8,
                step=1,
            )

        with self.server.gui.add_folder("Display"):
            self.show_meshes_cb = self.server.gui.add_checkbox("Show meshes", initial_value=self.config.show_meshes)

        with self.server.gui.add_folder("Review"):
            self.note_input = self.server.gui.add_text("Note", initial_value="")
            pass_btn = self.server.gui.add_button("Pass")
            fail_btn = self.server.gui.add_button("Fail")
            needs_review_btn = self.server.gui.add_button("Needs Review")
            skip_btn = self.server.gui.add_button("Skip")

        @self.sample_dropdown.on_update
        def _(_evt) -> None:
            if self._programmatic_sample_update:
                return
            task = str(self.sample_dropdown.value)
            self._load_sample(next(i for i, sample in enumerate(self.samples) if sample.task == task))

        @prev_btn.on_click
        def _(_evt) -> None:
            self._load_sample((self.current_index - 1) % len(self.samples))

        @next_btn.on_click
        def _(_evt) -> None:
            self._load_sample((self.current_index + 1) % len(self.samples))

        @next_unreviewed_btn.on_click
        def _(_evt) -> None:
            latest = load_latest_reviews(self.config.review_file)
            self._load_sample(first_unreviewed_index(self.samples, latest, self.current_index))

        @play_btn.on_click
        def _(_evt) -> None:
            with self._lock:
                self.playing = not self.playing
                self.prev_robot_q = None

        @self.show_meshes_cb.on_update
        def _(_evt) -> None:
            if self.robot_urdf is not None:
                self.robot_urdf.show_visual = bool(self.show_meshes_cb.value)
            if self.object_urdf is not None:
                self.object_urdf.show_visual = bool(self.show_meshes_cb.value)

        for button, status in (
            (pass_btn, "pass"),
            (fail_btn, "fail"),
            (needs_review_btn, "needs_review"),
            (skip_btn, "skip"),
        ):
            @button.on_click
            def _(_evt, review_status=status) -> None:
                self._record_review(review_status)

    def _replace_frame_slider(self, n_frames: int) -> None:
        if self.frame_slider is not None:
            self.frame_slider.remove()
        with self.playback_folder:
            self.frame_slider = self.server.gui.add_slider(
                "Frame",
                min=0,
                max=max(0, int(n_frames) - 1),
                step=1,
                initial_value=0,
            )

        @self.frame_slider.on_update
        def _(_evt) -> None:
            if self._programmatic_slider_update:
                return
            with self._lock:
                self.playing = False
                self.frame_f = float(self.frame_slider.value)
                self.prev_robot_q = None
                self._draw_frame(int(self.frame_slider.value))
```

Implement loading, drawing, interpolation, and review:

```python
    def _load_sample(self, index: int) -> None:
        import yourdfpy
        from viser.extras import ViserUrdf

        with self._lock:
            self.playing = False
            self.current_index = int(index)
            sample = self.samples[self.current_index]
            self.error_md.content = ""
            if self.sample_dropdown is not None and self.sample_dropdown.value != sample.task:
                self._programmatic_sample_update = True
                try:
                    self.sample_dropdown.value = sample.task
                finally:
                    self._programmatic_sample_update = False

            try:
                self.qpos, source_fps = _load_qpos(sample.qpos_npz)
                self.source_fps = int(self.config.fps or source_fps)
            except Exception as exc:
                self.qpos = None
                self.error_md.content = f"Load error: `{type(exc).__name__}: {exc}`"
                return

            if self.robot_urdf is not None:
                self.robot_urdf.remove()
            if self.object_urdf is not None:
                self.object_urdf.remove()
            self.robot_urdf = None
            self.object_urdf = None

            robot_urdf_y = yourdfpy.URDF.load(self.config.robot_urdf, load_meshes=True, build_scene_graph=True)
            self.robot_urdf = ViserUrdf(self.server, urdf_or_path=robot_urdf_y, root_node_name="/robot")
            self.robot_urdf.show_visual = bool(self.show_meshes_cb.value)
            self.robot_dof = len(self.robot_urdf.get_actuated_joint_limits())

            if sample.object_urdf is not None:
                object_urdf_y = yourdfpy.URDF.load(sample.object_urdf, load_meshes=True, build_scene_graph=True)
                self.object_urdf = ViserUrdf(self.server, urdf_or_path=object_urdf_y, root_node_name="/object")
                self.object_urdf.show_visual = bool(self.show_meshes_cb.value)
            else:
                self.object_root.position = np.zeros(3)
                self.object_root.wxyz = np.array([1.0, 0.0, 0.0, 0.0])

            self.frame_f = 0.0
            self.prev_robot_q = None
            n_frames = int(self.qpos.shape[0])
            self._replace_frame_slider(n_frames)
            self._programmatic_slider_update = True
            self.frame_slider.value = 0
            self._programmatic_slider_update = False
            self.fps_input.value = self.source_fps
            self._draw_frame(0)
            self._refresh_review_ui()

    def _draw_frame(self, frame_index: int) -> None:
        if self.qpos is None or self.robot_urdf is None:
            return
        q = self.qpos[int(np.clip(frame_index, 0, self.qpos.shape[0] - 1))]
        joints = q[7 : 7 + self.robot_dof]
        if joints.shape[0] != self.robot_dof:
            joints = joints[: self.robot_dof] if joints.shape[0] > self.robot_dof else np.pad(joints, (0, self.robot_dof - joints.shape[0]))
        self.robot_urdf.update_cfg(joints)
        self.robot_root.position = q[0:3]
        robot_q = self._quat_continuous(q[3:7])
        self.robot_root.wxyz = robot_q

    def _quat_continuous(self, curr_q: np.ndarray) -> np.ndarray:
        q = np.asarray(curr_q, dtype=float)
        norm = float(np.linalg.norm(q))
        if norm > 0.0:
            q = q / norm
        if self.prev_robot_q is not None and float(np.dot(self.prev_robot_q, q)) < 0.0:
            q = -q
        self.prev_robot_q = q
        return q

    def _player_loop(self) -> None:
        while True:
            with self._lock:
                if self.playing and self.qpos is not None and self.qpos.shape[0] > 1:
                    mult = max(1, int(self.interp_mult_input.value))
                    self.frame_f += 1.0 / mult
                    n_frames = int(self.qpos.shape[0])
                    if self.config.loop:
                        self.frame_f = self.frame_f % n_frames
                    else:
                        self.frame_f = min(self.frame_f, float(n_frames - 1))
                        if self.frame_f >= n_frames - 1:
                            self.playing = False
                    frame_index = int(self.frame_f)
                    self._draw_frame(frame_index)
                    self._programmatic_slider_update = True
                    self.frame_slider.value = frame_index
                    self._programmatic_slider_update = False
                    fps = max(1, int(self.fps_input.value))
                    sleep_s = 1.0 / max(1, fps * mult)
                else:
                    sleep_s = 0.02
            time.sleep(sleep_s)

    def _record_review(self, status: str) -> None:
        sample = self.samples[self.current_index]
        try:
            append_review_record(self.config.review_file, sample, status=status, note=str(self.note_input.value))
        except Exception as exc:
            self.error_md.content = f"Review write error: `{type(exc).__name__}: {exc}`"
            return
        self._refresh_review_ui()

    def _refresh_review_ui(self) -> None:
        sample = self.samples[self.current_index]
        latest = load_latest_reviews(self.config.review_file)
        record = latest.get(sample.task)
        self.status_md.content = (
            f"Sample `{self.current_index + 1} / {len(self.samples)}`: `{sample.task}`  \n"
            f"Review: `{record.status if record else 'unreviewed'}`"
        )
        self.path_md.content = (
            f"QPOS: `{sample.qpos_npz}`  \n"
            f"Terrain: `{sample.object_urdf if sample.object_urdf is not None else 'missing'}`"
        )
        self.note_input.value = record.note if record is not None else ""


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run automated tests**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -q tests/test_parc_batch_vis.py
```

Expected: PASS.

- [ ] **Step 5: Run import smoke test**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python -m omniretarget.examples.parc_batch_vis --help
```

Expected: exits 0 and prints flags including `--output-root`, `--dataset`, and `--task-list`.

- [ ] **Step 6: Commit Task 3**

```bash
git add src/omniretarget/examples/parc_batch_vis.py tests/test_parc_batch_vis.py
git commit -m "feat: add PARC batch viser runtime"
```

## Task 4: Integration Verification On Converted Mid-Climbing Output

**Files:**
- No new source files expected.
- Modify source only if verification exposes a bug.

- [ ] **Step 1: Run the focused automated test suite**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -q tests/test_parc_batch_vis.py tests/test_parc_vis_script.py tests/test_module_entrypoints.py
```

Expected: PASS.

- [ ] **Step 2: Run full repository tests**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -q
```

Expected: PASS, preserving the existing skipped tests count.

- [ ] **Step 3: Launch batch viewer manually on the converted `mid_climbing` batch**

Run:

```bash
OUTPUT_ROOT=/home/humanoid/Downloads/Data/parc_initial_aug_g1_v2_height_fixed_mid_climbing_full_20260531 \
PARC_DATASET=mid_climbing \
bash scripts/parc/vis_parc_batch.sh --start-task mid_blocks_001_dm
```

Expected:

- one viser server starts,
- the browser UI shows 78 samples,
- `mid_blocks_001_dm` loads first,
- terrain and robot are visible,
- frame slider range matches the loaded qpos length.

- [ ] **Step 4: Verify sample switching and review writes**

In the viewer:

1. Click `Next`.
2. Confirm the task label changes.
3. Confirm terrain changes or reloads without retaining the old terrain.
4. Click `Pass`.
5. Click `Next Unreviewed`.

Then inspect the review file:

```bash
tail -n 5 /home/humanoid/Downloads/Data/parc_initial_aug_g1_v2_height_fixed_mid_climbing_full_20260531/vis_review/mid_climbing_review.jsonl
```

Expected: the latest lines include JSON records with `task`, `status`, `note`, `qpos_npz`, `object_urdf`, and `timestamp`.

- [ ] **Step 5: Commit verification fixes if any were needed**

If no source change was needed, do not create an empty commit. If fixes were needed:

```bash
git add src/omniretarget/examples/parc_batch_vis.py src/omniretarget/parc_process/batch_vis.py tests/test_parc_batch_vis.py scripts/parc/vis_parc_batch.sh
git commit -m "fix: stabilize PARC batch visualization"
```

## Self-Review Notes

- Spec coverage:
  - Batch output scanning is covered by Task 1.
  - Scaled terrain preference and fallback are covered by Task 1.
  - Task-list filtering is covered by Task 1.
  - Review JSONL append and latest-status behavior are covered by Task 1 and Task 3.
  - One-server viser sample switching is covered by Task 3 and manually verified in Task 4.
  - Shell wrapper is covered by Task 2.
- Scope:
  - The plan does not implement thumbnails, screenshots, keyboard shortcuts, or MJ `motion.npz` playback because those are outside the first-version boundary.
- Risk:
  - Viser runtime behavior cannot be fully covered in headless pytest; Task 4 requires manual browser verification on the converted `mid_climbing` output.
