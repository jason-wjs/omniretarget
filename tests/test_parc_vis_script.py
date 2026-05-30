from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_vis_parc_process_prefers_scaled_object_urdf(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    task = "mid_blocks_001_dm_aug004_dm_aug0"
    workspace = tmp_path / "retarget" / "workspace" / task
    workspace.mkdir(parents=True)
    (workspace / "multi_boxes.urdf").write_text("<robot />\n", encoding="utf-8")
    scaled_urdf = workspace / "multi_boxes_scaled_0.78_0.78_0.78.urdf"
    scaled_urdf.write_text("<robot />\n", encoding="utf-8")

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

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["CAPTURE_FILE"] = str(capture_file)
    env["RETARGET_SAVE_DIR"] = str(tmp_path / "retarget")
    env["PARC_TASK"] = task

    subprocess.run(
        ["bash", str(repo_root / "scripts" / "parc" / "vis_parc_process.sh"), "--loop"],
        cwd=repo_root,
        env=env,
        check=True,
    )

    args = capture_file.read_text(encoding="utf-8").splitlines()
    object_urdf_idx = args.index("--object-urdf") + 1
    assert args[object_urdf_idx] == str(scaled_urdf)
