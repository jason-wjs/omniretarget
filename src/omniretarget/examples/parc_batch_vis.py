from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import threading
import time
from typing import Any

import numpy as np

from omniretarget.parc_process.batch_vis import (
    ParcVisSample,
    append_review_record,
    default_review_file,
    discover_playlist,
    first_unreviewed_index,
    load_latest_reviews,
)
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


def _load_qpos(npz_path: Path) -> tuple[np.ndarray, int]:
    data = np.load(npz_path, allow_pickle=True)
    qpos = data["qpos"]
    if not isinstance(qpos, np.ndarray):
        raise ValueError(f"qpos must be a numpy array: {npz_path}")
    if qpos.ndim != 2:
        raise ValueError(f"qpos must be 2D with shape (frames, columns): {npz_path} has shape {qpos.shape}")
    if qpos.shape[0] <= 0:
        raise ValueError(f"qpos must contain at least one frame: {npz_path} has shape {qpos.shape}")
    if qpos.shape[1] < 7:
        raise ValueError(
            f"qpos must contain at least 7 columns for base position and quaternion: "
            f"{npz_path} has shape {qpos.shape}"
        )
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
        import viser  # type: ignore[import-not-found]

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
        def _(_evt: Any) -> None:
            if self._programmatic_sample_update:
                return
            task = str(self.sample_dropdown.value)
            self._load_sample(next(i for i, sample in enumerate(self.samples) if sample.task == task))

        @prev_btn.on_click
        def _(_evt: Any) -> None:
            self._load_sample((self.current_index - 1) % len(self.samples))

        @next_btn.on_click
        def _(_evt: Any) -> None:
            self._load_sample((self.current_index + 1) % len(self.samples))

        @next_unreviewed_btn.on_click
        def _(_evt: Any) -> None:
            try:
                latest = load_latest_reviews(self.config.review_file)
                next_index = first_unreviewed_index(self.samples, latest, self.current_index)
            except Exception as exc:
                self.error_md.content = f"Review read error: `{type(exc).__name__}: {exc}`"
                return
            self._load_sample(next_index)

        @play_btn.on_click
        def _(_evt: Any) -> None:
            with self._lock:
                self.playing = not self.playing
                self.prev_robot_q = None

        @self.show_meshes_cb.on_update
        def _(_evt: Any) -> None:
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
            def _(_evt: Any, review_status: str = status) -> None:
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
        def _(_evt: Any) -> None:
            if self._programmatic_slider_update:
                return
            with self._lock:
                self.playing = False
                self.frame_f = float(self.frame_slider.value)
                self.prev_robot_q = None
                self._draw_frame(int(self.frame_slider.value))

    def _load_sample(self, index: int) -> None:
        import yourdfpy  # type: ignore[import-untyped]
        from viser.extras import ViserUrdf  # type: ignore[import-not-found]

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

            self._remove_loaded_urdfs()
            self.qpos = None
            self.robot_dof = 0
            self.frame_f = 0.0
            self.prev_robot_q = None

            try:
                self.qpos, source_fps = _load_qpos(sample.qpos_npz)
            except Exception as exc:
                self.error_md.content = f"Load error: `{type(exc).__name__}: {exc}`"
                self._replace_frame_slider(n_frames=1)
                self._refresh_review_ui()
                return

            self.source_fps = int(self.config.fps if self.config.fps is not None else source_fps)
            self.fps_input.value = self.source_fps

            try:
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
            except Exception as exc:
                self._remove_loaded_urdfs()
                self.error_md.content = f"Load error: `{type(exc).__name__}: {exc}`"
                self._replace_frame_slider(n_frames=1)
                self._refresh_review_ui()
                return

            n_frames = int(self.qpos.shape[0])
            self._replace_frame_slider(n_frames)
            self._programmatic_slider_update = True
            try:
                self.frame_slider.value = 0
            finally:
                self._programmatic_slider_update = False
            self._draw_frame(0)
            self._refresh_review_ui()

    def _draw_frame(self, frame_index: int) -> None:
        if self.qpos is None or self.robot_urdf is None:
            return
        q = self.qpos[int(np.clip(frame_index, 0, self.qpos.shape[0] - 1))]
        joints = q[7 : 7 + self.robot_dof]
        if joints.shape[0] != self.robot_dof:
            if joints.shape[0] > self.robot_dof:
                joints = joints[: self.robot_dof]
            else:
                joints = np.pad(joints, (0, self.robot_dof - joints.shape[0]))
        self.robot_urdf.update_cfg(joints)
        self.robot_root.position = q[0:3]
        self.robot_root.wxyz = self._quat_continuous(q[3:7])

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
                    try:
                        self.frame_slider.value = frame_index
                    finally:
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
        try:
            latest = load_latest_reviews(self.config.review_file)
        except Exception as exc:
            self.error_md.content = f"Review read error: `{type(exc).__name__}: {exc}`"
            latest = {}
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

    def _remove_loaded_urdfs(self) -> None:
        if self.robot_urdf is not None:
            self.robot_urdf.remove()
        if self.object_urdf is not None:
            self.object_urdf.remove()
        self.robot_urdf = None
        self.object_urdf = None


if __name__ == "__main__":
    raise SystemExit(main())
