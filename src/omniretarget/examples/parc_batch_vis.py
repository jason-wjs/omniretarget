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
