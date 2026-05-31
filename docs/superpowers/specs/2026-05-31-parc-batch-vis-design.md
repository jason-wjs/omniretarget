# PARC Batch Visualization Design

## Context

The current PARC visualization path is single-sample oriented. `scripts/parc/vis_parc_process.sh` takes `RETARGET_SAVE_DIR` and `PARC_TASK`, resolves one retargeted qpos file and one terrain URDF, then starts `src/omniretarget/viser_player.py`.

After batch conversion, a full dataset such as `mid_climbing` can contain dozens of converted samples. Reviewing them one by one with separate shell invocations is slow and error-prone, especially when each sample needs a manual pass/fail decision.

## Goals

- Add a batch PARC visualization mode that starts one viser server and lets the reviewer switch among many samples from the browser UI.
- Preserve the existing single-sample `vis_parc_process.sh` workflow.
- Support the batch output layout produced by `omniretarget.examples.parc_batch_process_to_mj`.
- Let reviewers record per-sample decisions during playback.
- Keep the first implementation focused on `parc_process/workspace` retarget outputs and terrain URDF visualization.

## Non-Goals

- Do not build a general-purpose dataset annotation platform.
- Do not change the batch conversion output layout.
- Do not require MJ `motion.npz` playback for this feature; the primary visualization input remains retargeted qpos `.npz` plus terrain URDF.
- Do not support simultaneous multi-sample rendering in the first version.

## User Workflow

Default invocation:

```bash
OUTPUT_ROOT=/home/humanoid/Downloads/Data/parc_initial_aug_g1_v2_height_fixed_mid_climbing_full_20260531 \
PARC_DATASET=mid_climbing \
bash scripts/parc/vis_parc_batch.sh
```

The script starts one viser server. In the browser UI, the reviewer can:

- choose a sample from a dropdown,
- move to previous or next sample,
- jump to the next unreviewed sample,
- play, pause, scrub frames, and adjust FPS,
- toggle mesh visibility,
- mark the current sample as `pass`, `fail`, `needs_review`, or `skip`,
- attach a short note to the current sample.

## Architecture

Add a new Python entrypoint:

```text
src/omniretarget/examples/parc_batch_vis.py
```

Add a shell wrapper:

```text
scripts/parc/vis_parc_batch.sh
```

The new player should be PARC-specific. It should not extend `viser_player.py` with playlist behavior, because batch PARC visualization needs dataset discovery, terrain URDF matching, review records, and dynamic sample switching. Keeping those concerns out of the generic single-sample player preserves the current simple replay path.

## Data Discovery

The default scanner accepts:

- `--output-root`
- `--dataset`, for example `mid_climbing`

It discovers retargeted qpos files from:

```text
{output_root}/parc_process/workspace/{dataset}/retargeted/*_original.npz
```

For each qpos file, the task name is the filename with `_original.npz` removed. Terrain URDF lookup uses:

```text
{output_root}/parc_process/workspace/{dataset}/workspace/{task}/multi_boxes_scaled_*.urdf
```

If no scaled terrain URDF exists, it falls back to:

```text
{output_root}/parc_process/workspace/{dataset}/workspace/{task}/multi_boxes.urdf
```

The scanner returns a playlist of records with:

- task name,
- qpos `.npz` path,
- object URDF path,
- sample index.

Optional `--task-list` restricts the playlist to explicit task names, one per line, preserving file order. Empty lines and `#` comments are ignored.

## CLI

The Python entrypoint should support:

- `--output-root PATH`
- `--dataset NAME`
- `--task-list PATH`
- `--review-file PATH`
- `--robot-urdf PATH`
- `--loop / --no-loop`
- `--start-task NAME`
- `--fps INT`
- `--grid-width FLOAT`
- `--grid-height FLOAT`
- `--visual-fps-multiplier INT`

The shell wrapper maps environment variables to the Python CLI:

- `OUTPUT_ROOT`
- `PARC_DATASET`
- `TASK_LIST`
- `REVIEW_FILE`
- `ROBOT_URDF`

Additional shell arguments are forwarded to Python.

## Viser Scene Behavior

The batch player owns one server and a mutable playback state. It creates stable root frames:

- `/robot`
- `/object`
- `/grid`

On sample switch:

1. pause playback,
2. load the selected qpos `.npz`,
3. resolve FPS from the `.npz` unless overridden,
4. clear or remove old robot and object URDF handles,
5. load the G1 robot URDF,
6. load the selected terrain URDF,
7. reset frame slider bounds,
8. draw frame 0,
9. update GUI labels for index, task, qpos path, terrain path, review status, and note.

The batch player should implement its own mutable playback loop instead of reusing `create_motion_control_sliders`. The existing helper captures a fixed qpos sequence and fixed GUI controls in closures; dynamic sample switching would make that helper harder to reason about than a small batch-specific state object.

## Review Records

Default review file:

```text
{output_root}/vis_review/{dataset}_review.jsonl
```

Each status button appends one JSON object:

```json
{
  "task": "mid_blocks_004_dm_aug002_dm_aug1",
  "status": "pass",
  "note": "starts on correct platform",
  "qpos_npz": "/abs/path/to/task_original.npz",
  "object_urdf": "/abs/path/to/multi_boxes_scaled_0.78_0.78_0.78.urdf",
  "timestamp": "2026-05-31T12:34:56+08:00"
}
```

Multiple records for the same task are allowed. When displaying current status or choosing the next unreviewed sample, the last record for each task wins.

Supported statuses:

- `pass`
- `fail`
- `needs_review`
- `skip`

`Next Unreviewed` treats any task with no latest status as unreviewed.

## Error Handling

- Missing output root: fail before starting viser.
- Empty playlist: fail before starting viser with a message that includes the scanned retargeted directory.
- Missing qpos file for a task-list entry: fail before starting viser and list the missing task.
- Missing terrain URDF: keep the sample in the playlist, show a clear warning, and allow robot-only playback for that sample.
- Bad `.npz`: show the error in the GUI status area and keep the server running so the reviewer can skip or move to another sample.
- Review file write failure: show the error and keep playback active.

## Testing

Automated tests should cover logic that does not require a live browser:

- playlist scanning from a fake batch output tree,
- scaled terrain URDF preference over `multi_boxes.urdf`,
- fallback to unscaled terrain URDF,
- task-list filtering and ordering,
- detection of missing task-list entries,
- review JSONL append and latest-status loading,
- shell wrapper argument forwarding using a fake `uv` executable.

Manual validation should run the shell wrapper on a small converted dataset and confirm:

- the viewer starts,
- dropdown and next/previous change samples,
- terrain changes with each task,
- playback resets on sample switch,
- review buttons write JSONL records.

## Initial Scope Boundary

The first version should be enough to review the converted `mid_climbing` batch. More advanced features, such as thumbnail previews, side-by-side comparisons, sampled subsets, keyboard shortcuts, or automatic screenshot capture, can be added later if the manual review loop still feels slow.
