from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Iterable


VALID_REVIEW_STATUSES = {"pass", "fail", "needs_review", "skip"}


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
    return _normalize_path(output_root) / "parc_process" / "workspace" / dataset / "retargeted"


def workspace_dir(output_root: Path, dataset: str) -> Path:
    return _normalize_path(output_root) / "parc_process" / "workspace" / dataset / "workspace"


def default_review_file(output_root: Path, dataset: str) -> Path:
    return _normalize_path(output_root) / "vis_review" / f"{dataset}_review.jsonl"


def task_from_retargeted_npz(path: Path) -> str:
    suffix = "_original.npz"
    if not path.name.endswith(suffix):
        raise ValueError(f"Retargeted qpos file must end with {suffix!r}: {path}")
    return path.name[: -len(suffix)]


def read_task_list(path: Path) -> list[str]:
    tasks: list[str] = []
    for line in _normalize_path(path).read_text(encoding="utf-8").splitlines():
        task = line.strip()
        if not task or task.startswith("#"):
            continue
        tasks.append(task)
    return tasks


def resolve_object_urdf(output_root: Path, dataset: str, task: str) -> Path | None:
    task_workspace = workspace_dir(output_root, dataset) / task
    scaled = sorted(task_workspace.glob("multi_boxes_scaled_*.urdf"))
    if scaled:
        return scaled[0]

    unscaled = task_workspace / "multi_boxes.urdf"
    if unscaled.exists():
        return unscaled
    return None


def discover_playlist(output_root: Path, dataset: str, task_list: Path | None = None) -> list[ParcVisSample]:
    output_root = _normalize_path(output_root)
    retargeted = retargeted_dir(output_root, dataset)
    if not retargeted.is_dir():
        raise FileNotFoundError(f"Retargeted directory not found: {retargeted}")

    qpos_by_task = {
        task_from_retargeted_npz(path): path
        for path in sorted(retargeted.glob("*_original.npz"))
    }
    if not qpos_by_task:
        raise FileNotFoundError(f"No *_original.npz files found in retargeted directory: {retargeted}")

    if task_list is None:
        tasks = sorted(qpos_by_task)
    else:
        tasks = read_task_list(task_list)
        if not tasks:
            raise ValueError(f"No tasks remain after reading task list: {_normalize_path(task_list)}")
        missing = [task for task in tasks if task not in qpos_by_task]
        if missing:
            raise FileNotFoundError(f"Tasks missing from retargeted directory {retargeted}: {', '.join(missing)}")

    return [
        ParcVisSample(
            task=task,
            index=index,
            qpos_npz=qpos_by_task[task],
            object_urdf=resolve_object_urdf(output_root, dataset, task),
        )
        for index, task in enumerate(tasks)
    ]


def append_review_record(
    review_file: Path,
    sample: ParcVisSample,
    *,
    status: str,
    note: str,
    timestamp: str | None = None,
) -> ReviewRecord:
    status = _validate_review_status(status)
    if not isinstance(note, str):
        raise ValueError("note must be a string")
    if timestamp is not None and not isinstance(timestamp, str):
        raise ValueError("timestamp must be a string")
    if timestamp is None:
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

    record = ReviewRecord(
        task=sample.task,
        status=status,
        note=note,
        qpos_npz=_normalize_path(sample.qpos_npz),
        object_urdf=_normalize_path(sample.object_urdf) if sample.object_urdf is not None else None,
        timestamp=timestamp,
    )

    payload = {
        "task": record.task,
        "status": record.status,
        "note": record.note,
        "qpos_npz": str(record.qpos_npz),
        "object_urdf": str(record.object_urdf) if record.object_urdf is not None else None,
        "timestamp": record.timestamp,
    }
    review_file = _normalize_path(review_file)
    review_file.parent.mkdir(parents=True, exist_ok=True)
    with review_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, sort_keys=True) + "\n")
    return record


def load_latest_reviews(review_file: Path) -> dict[str, ReviewRecord]:
    review_file = _normalize_path(review_file)
    if not review_file.exists():
        return {}

    latest: dict[str, ReviewRecord] = {}
    for line_number, line in enumerate(review_file.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            record = _review_record_from_payload(payload)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid review record in {review_file}:{line_number}: {exc}") from exc
        latest[record.task] = record
    return latest


def first_unreviewed_index(
    samples: Iterable[ParcVisSample],
    latest_reviews: dict[str, ReviewRecord],
    start: int,
) -> int:
    """Return the next unreviewed sample after start, wrapping around.

    If every sample has a latest review, return start.
    """
    sample_list = list(samples)
    if not sample_list:
        raise ValueError("Cannot find an unreviewed sample in an empty playlist")

    count = len(sample_list)
    for offset in range(1, count + 1):
        index = (start + offset) % count
        if sample_list[index].task not in latest_reviews:
            return index
    return start


def _review_record_from_payload(payload: object) -> ReviewRecord:
    if not isinstance(payload, dict):
        raise ValueError("record must be a JSON object")

    status = _validate_review_status(payload["status"])

    object_urdf = payload["object_urdf"]
    if object_urdf is not None and not isinstance(object_urdf, str):
        raise ValueError("object_urdf must be a string or null")
    return ReviewRecord(
        task=_require_str(payload["task"], "task"),
        status=_require_str(status, "status"),
        note=_require_str(payload["note"], "note"),
        qpos_npz=_normalize_path(_require_str(payload["qpos_npz"], "qpos_npz")),
        object_urdf=_normalize_path(object_urdf) if object_urdf is not None else None,
        timestamp=_require_str(payload["timestamp"], "timestamp"),
    )


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _validate_review_status(status: object) -> str:
    if not isinstance(status, str):
        raise ValueError("status must be a string")
    if status not in VALID_REVIEW_STATUSES:
        raise ValueError(f"invalid review status {status!r}; expected one of {sorted(VALID_REVIEW_STATUSES)}")
    return status


def _normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()
