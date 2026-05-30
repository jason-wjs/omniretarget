from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised only when optional dependency is absent
    yaml = None

from omniretarget.config_types.data_type import MotionDataConfig  # noqa: E402
from omniretarget.config_types.retargeter import RetargeterConfig  # noqa: E402
from omniretarget.config_types.retargeting import RetargetingConfig  # noqa: E402
from omniretarget.config_types.robot import RobotConfig  # noqa: E402
from omniretarget.config_types.task import TaskConfig  # noqa: E402
from omniretarget.examples.robot_retarget import main as run_robot_retarget  # noqa: E402
from omniretarget.parc_process.output_writer import (  # noqa: E402
    PairedOutputResult,
    write_paired_output,
)
from omniretarget.parc_process.source_io import ParcSample, load_parc_sample  # noqa: E402
from omniretarget.parc_process.workspace import (  # noqa: E402
    ParcWorkspace,
    build_parc_workspace,
)


@dataclass(frozen=True)
class ParcProcessResult:
    sample: Path
    task_name: str
    workspace: ParcWorkspace
    retarget_npz: Path | None
    paired_output: PairedOutputResult | None


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compile PARC paired samples into G1 paired dataset artifacts.")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--sample", type=Path, help="Single PARC .pkl sample to compile.")
    input_group.add_argument(
        "--manifest",
        type=Path,
        help="Manifest of PARC sample paths. Supports YAML (`samples:` or list) and plain text.",
    )
    parser.add_argument("--source-xml", type=Path, required=True, help="Path to PARC humanoid.xml.")
    parser.add_argument("--output-root", type=Path, required=True, help="Directory for compiled paired outputs.")
    parser.add_argument(
        "--retarget-save-dir",
        type=Path,
        default=Path("./parc_process_runs"),
        help="Directory for generated workspaces and intermediate retargeting outputs.",
    )
    parser.add_argument("--robot-type", default="g1", help="Robot type passed to holosoma retargeting.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only build PARC workspaces; skip retargeting and paired output emission.",
    )
    parser.add_argument(
        "--activate-object-non-penetration",
        action="store_true",
        help="Keep object non-penetration constraints enabled during bootstrap retargeting.",
    )
    return parser


def _load_manifest_samples(manifest_path: Path) -> list[Path]:
    manifest_path = manifest_path.expanduser().resolve()
    suffix = manifest_path.suffix.lower()

    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to load YAML PARC manifests.")
        payload = yaml.safe_load(manifest_path.read_text())
        if isinstance(payload, dict):
            samples = payload.get("samples", [])
        elif isinstance(payload, list):
            samples = payload
        else:
            raise ValueError(f"Unsupported YAML manifest format: {manifest_path}")
        return [Path(sample).expanduser().resolve() for sample in samples]

    samples = [
        Path(line.strip()).expanduser().resolve()
        for line in manifest_path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return samples


def _resolve_samples(args: argparse.Namespace) -> list[Path]:
    if args.sample is not None:
        return [args.sample.expanduser().resolve()]
    if args.manifest is not None:
        return _load_manifest_samples(args.manifest)
    raise ValueError("Either --sample or --manifest must be provided.")


def _default_scale_factor(robot_type: str, data_format: str = "parc_humanoid") -> float:
    robot_cfg = RobotConfig(robot_type=robot_type)
    motion_cfg = MotionDataConfig(data_format=data_format, robot_type=robot_type)
    if motion_cfg.default_scale_factor is not None:
        return float(motion_cfg.default_scale_factor)
    if motion_cfg.default_human_height is not None:
        return float(robot_cfg.ROBOT_HEIGHT / motion_cfg.default_human_height)
    return 1.0


def _retarget_output_path(retarget_dir: Path, task_name: str) -> Path:
    return retarget_dir / f"{task_name}_original.npz"


def _workspace_terrain_payload(workspace: ParcWorkspace, source_sample: ParcSample) -> dict[str, Any]:
    terrain_hf = np.load(workspace.terrain_hf_path)
    return {
        "hf": terrain_hf,
        "hf_maxmin": np.array([float(np.max(terrain_hf)), float(np.min(terrain_hf))], dtype=np.float32),
        "min_point": source_sample.terrain_data.min_point,
        "dx": source_sample.terrain_data.dx,
    }


def _build_retarget_config(
    *,
    workspace_root: Path,
    retarget_dir: Path,
    task_name: str,
    robot_type: str,
    activate_obj_non_penetration: bool,
) -> RetargetingConfig:
    return RetargetingConfig(
        task_type="climbing",
        robot=robot_type,
        data_format="parc_humanoid",
        task_name=task_name,
        data_path=workspace_root,
        save_dir=retarget_dir,
        robot_config=RobotConfig(robot_type=robot_type),
        motion_data_config=MotionDataConfig(data_format="parc_humanoid", robot_type=robot_type),
        task_config=TaskConfig(object_name="multi_boxes", object_dir=workspace_root / task_name),
        retargeter=RetargeterConfig(activate_obj_non_penetration=activate_obj_non_penetration),
    )


def compile_sample(
    *,
    sample_path: Path,
    source_xml: Path,
    output_root: Path,
    retarget_save_dir: Path,
    robot_type: str,
    activate_obj_non_penetration: bool,
    dry_run: bool = False,
) -> ParcProcessResult:
    source_sample = load_parc_sample(sample_path)
    task_name = sample_path.stem

    workspace_root = retarget_save_dir / "workspace"
    retarget_dir = retarget_save_dir / "retargeted"
    workspace = build_parc_workspace(
        sample=source_sample,
        source_xml=source_xml,
        output_dir=workspace_root,
        task_name=task_name,
    )

    if dry_run:
        return ParcProcessResult(
            sample=sample_path,
            task_name=task_name,
            workspace=workspace,
            retarget_npz=None,
            paired_output=None,
        )

    retarget_dir.mkdir(parents=True, exist_ok=True)
    cfg = _build_retarget_config(
        workspace_root=workspace_root,
        retarget_dir=retarget_dir,
        task_name=task_name,
        robot_type=robot_type,
        activate_obj_non_penetration=activate_obj_non_penetration,
    )
    run_robot_retarget(cfg)

    retarget_npz = _retarget_output_path(retarget_dir, task_name)
    qpos = np.load(retarget_npz)["qpos"]
    normalized_terrain_payload = _workspace_terrain_payload(workspace, source_sample)
    paired_output = write_paired_output(
        qpos=qpos,
        source_sample=source_sample,
        output_root=output_root,
        motion_name=f"{task_name}_{robot_type}",
        scale_factor=_default_scale_factor(robot_type),
        workspace_path=workspace.task_dir,
        terrain_collision_path=workspace.terrain_collision_path,
        terrain_hf_path=workspace.terrain_hf_path,
        terrain_visual_path=workspace.obj_path,
        terrain_payload_override=normalized_terrain_payload,
        z_origin=workspace.z_origin,
        retarget_config={
            "robot": robot_type,
            "task_type": "climbing",
            "data_format": "parc_humanoid",
            "retarget_npz": str(retarget_npz),
        },
    )
    return ParcProcessResult(
        sample=sample_path,
        task_name=task_name,
        workspace=workspace,
        retarget_npz=retarget_npz,
        paired_output=paired_output,
    )


def run_parc_process(args: argparse.Namespace) -> list[ParcProcessResult]:
    source_xml = args.source_xml.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    retarget_save_dir = args.retarget_save_dir.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    retarget_save_dir.mkdir(parents=True, exist_ok=True)

    results = [
        compile_sample(
            sample_path=sample_path,
            source_xml=source_xml,
            output_root=output_root,
            retarget_save_dir=retarget_save_dir,
            robot_type=args.robot_type,
            activate_obj_non_penetration=args.activate_object_non_penetration,
            dry_run=args.dry_run,
        )
        for sample_path in _resolve_samples(args)
    ]
    return results


def _result_to_dict(result: ParcProcessResult) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "sample": str(result.sample),
        "task_name": result.task_name,
        "workspace": str(result.workspace.task_dir),
    }
    if result.retarget_npz is not None:
        payload["retarget_npz"] = str(result.retarget_npz)
    if result.paired_output is not None:
        payload["paired_output"] = str(result.paired_output.motion_file)
        payload["manifest"] = str(result.paired_output.manifest_file)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    results = run_parc_process(args)
    print(json.dumps([_result_to_dict(result) for result in results], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
