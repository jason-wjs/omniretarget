from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from omniretarget.data_conversion.convert_data_format_parc_mj import (
    DEFAULT_G1_XML_PATH,
    ParcMjConversionConfig,
    convert_parc_qpos_to_motion_file,
)
from omniretarget.examples.parc_process import compile_sample


@dataclass(frozen=True)
class ParcBatchConfig:
    source_root: Path
    source_xml: Path
    output_root: Path
    robot_xml: Path = DEFAULT_G1_XML_PATH
    output_fps: int = 50
    robot_type: str = "g1"
    skip_existing: bool = False
    continue_on_error: bool = False
    activate_obj_non_penetration: bool = False
    limit: int | None = None
    dry_run: bool = False


@dataclass(frozen=True)
class ParcBatchSamplePlan:
    sample_path: Path
    relative_dir: Path
    stem: str
    paired_output_root: Path
    retarget_save_dir: Path
    retarget_npz: Path
    mj_motion_file: Path


@dataclass(frozen=True)
class ParcBatchResult:
    sample_path: Path
    status: str
    mj_motion_file: Path
    error: str | None = None


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch compile PARC initial_aug samples into retargeted G1 and mjlab motion.npz outputs."
    )
    parser.add_argument("--source-root", type=Path, required=True, help="PARC initial_aug root directory.")
    parser.add_argument("--source-xml", type=Path, required=True, help="Path to PARC humanoid.xml.")
    parser.add_argument("--output-root", type=Path, required=True, help="Root directory for batch outputs.")
    parser.add_argument("--robot-xml", type=Path, default=DEFAULT_G1_XML_PATH, help="G1 XML used for mj conversion.")
    parser.add_argument("--output-fps", type=int, default=50, help="FPS for mjlab motion.npz outputs.")
    parser.add_argument("--robot-type", default="g1", help="Robot type passed to PARC retargeting.")
    parser.add_argument("--skip-existing", action="store_true", help="Skip samples whose mj motion.npz already exists.")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue after per-sample failures.")
    parser.add_argument(
        "--activate-object-non-penetration",
        action="store_true",
        help="Keep object non-penetration constraints enabled during PARC retargeting.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Process at most this many samples.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned paths without retargeting or converting.")
    return parser


def iter_parc_samples(source_root: Path, limit: int | None = None) -> list[Path]:
    root = source_root.expanduser().resolve()
    samples = sorted(path.resolve() for path in root.rglob("*.pkl") if path.is_file())
    if limit is not None:
        samples = samples[:limit]
    return samples


def build_sample_plan(*, source_root: Path, sample_path: Path, output_root: Path) -> ParcBatchSamplePlan:
    root = source_root.expanduser().resolve()
    sample = sample_path.expanduser().resolve()
    out = output_root.expanduser().resolve()
    relative_path = sample.relative_to(root)
    relative_dir = relative_path.parent
    stem = sample.stem

    paired_output_root = out / "parc_process" / "paired" / relative_dir
    retarget_save_dir = out / "parc_process" / "workspace" / relative_dir
    retarget_npz = retarget_save_dir / "retargeted" / f"{stem}_original.npz"
    mj_motion_file = out / "mj" / relative_dir / stem / "motion.npz"

    return ParcBatchSamplePlan(
        sample_path=sample,
        relative_dir=relative_dir,
        stem=stem,
        paired_output_root=paired_output_root,
        retarget_save_dir=retarget_save_dir,
        retarget_npz=retarget_npz,
        mj_motion_file=mj_motion_file,
    )


def _prepare_logs(output_root: Path) -> Path:
    log_dir = output_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("succeeded.txt", "failed.txt", "skipped.txt", "planned.txt"):
        (log_dir / filename).write_text("", encoding="utf-8")
    return log_dir


def _append_log(log_dir: Path, filename: str, line: str) -> None:
    with (log_dir / filename).open("a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")


def _process_one_sample(config: ParcBatchConfig, plan: ParcBatchSamplePlan) -> ParcBatchResult:
    if config.dry_run:
        return ParcBatchResult(sample_path=plan.sample_path, status="planned", mj_motion_file=plan.mj_motion_file)

    result = compile_sample(
        sample_path=plan.sample_path,
        source_xml=config.source_xml,
        output_root=plan.paired_output_root,
        retarget_save_dir=plan.retarget_save_dir,
        robot_type=config.robot_type,
        activate_obj_non_penetration=config.activate_obj_non_penetration,
        dry_run=False,
    )
    retarget_npz = result.retarget_npz or plan.retarget_npz
    convert_parc_qpos_to_motion_file(
        ParcMjConversionConfig(
            input_file=retarget_npz,
            output_name=plan.mj_motion_file,
            robot_xml=config.robot_xml,
            output_fps=config.output_fps,
        )
    )
    return ParcBatchResult(sample_path=plan.sample_path, status="converted", mj_motion_file=plan.mj_motion_file)


def run_batch(config: ParcBatchConfig) -> list[ParcBatchResult]:
    source_root = config.source_root.expanduser().resolve()
    output_root = config.output_root.expanduser().resolve()
    source_xml = config.source_xml.expanduser().resolve()
    robot_xml = config.robot_xml.expanduser().resolve()
    resolved_config = ParcBatchConfig(
        source_root=source_root,
        source_xml=source_xml,
        output_root=output_root,
        robot_xml=robot_xml,
        output_fps=config.output_fps,
        robot_type=config.robot_type,
        skip_existing=config.skip_existing,
        continue_on_error=config.continue_on_error,
        activate_obj_non_penetration=config.activate_obj_non_penetration,
        limit=config.limit,
        dry_run=config.dry_run,
    )

    if not source_root.is_dir():
        raise NotADirectoryError(source_root)

    output_root.mkdir(parents=True, exist_ok=True)
    log_dir = _prepare_logs(output_root)
    results: list[ParcBatchResult] = []

    for sample_path in iter_parc_samples(source_root, limit=config.limit):
        plan = build_sample_plan(source_root=source_root, sample_path=sample_path, output_root=output_root)

        if config.skip_existing and plan.mj_motion_file.exists():
            result = ParcBatchResult(sample_path=plan.sample_path, status="skipped", mj_motion_file=plan.mj_motion_file)
            results.append(result)
            _append_log(log_dir, "skipped.txt", str(plan.sample_path))
            continue

        if config.dry_run:
            result = ParcBatchResult(sample_path=plan.sample_path, status="planned", mj_motion_file=plan.mj_motion_file)
            results.append(result)
            _append_log(log_dir, "planned.txt", f"{plan.sample_path}\t{plan.mj_motion_file}")
            continue

        try:
            result = _process_one_sample(resolved_config, plan)
        except Exception as exc:
            result = ParcBatchResult(
                sample_path=plan.sample_path,
                status="failed",
                mj_motion_file=plan.mj_motion_file,
                error=f"{type(exc).__name__}: {exc}",
            )
            results.append(result)
            _append_log(log_dir, "failed.txt", f"{plan.sample_path}\t{result.error}")
            if not config.continue_on_error:
                raise
            continue

        results.append(result)
        _append_log(log_dir, "succeeded.txt", str(plan.sample_path))

    return results


def _summary(results: list[ParcBatchResult], output_root: Path) -> dict[str, object]:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return {
        "total": len(results),
        "counts": counts,
        "output_root": str(output_root.expanduser().resolve()),
        "logs": str(output_root.expanduser().resolve() / "logs"),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    config = ParcBatchConfig(
        source_root=args.source_root,
        source_xml=args.source_xml,
        output_root=args.output_root,
        robot_xml=args.robot_xml,
        output_fps=args.output_fps,
        robot_type=args.robot_type,
        skip_existing=args.skip_existing,
        continue_on_error=args.continue_on_error,
        activate_obj_non_penetration=args.activate_object_non_penetration,
        limit=args.limit,
        dry_run=args.dry_run,
    )
    results = run_batch(config)
    print(json.dumps(_summary(results, config.output_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
