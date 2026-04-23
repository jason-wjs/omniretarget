# CLI and Pipelines Refactor Design

## Goal

Restructure OmniRetarget's Python entrypoints so user-facing commands live under `holosoma_retargeting.cli`, while shared retargeting orchestration moves into a small internal `holosoma_retargeting.pipelines` layer.

## Context

The current migrated package still mirrors the original `holosoma_retargeting` layout. In that layout, `examples/` is not just illustrative example code; it is the effective Python entrypoint layer for single-clip and batch retargeting. The package also has `evaluation/`, `data_conversion/`, and `viser_player.py` modules that can be run directly as scripts.

The most confusing parts are:

- `examples/` acts as production entrypoints rather than examples.
- `examples/robot_retarget.py` mixes CLI parsing, validation, task setup, motion loading, object setup, and execution.
- `examples/parallel_robot_retarget.py` imports internal helpers from `examples/robot_retarget.py`, making single and parallel retargeting coupled through an entrypoint module.
- `holosoma_retargeting/src/` is a historical internal implementation layer, not the Python project source root. It contains the retargeter core and runtime support utilities.

## Selected Approach

Use a medium refactor:

- Add a new `cli/` package for thin Python entrypoints.
- Add a new `pipelines/` package for the minimum shared orchestration needed by retargeting entrypoints.
- Keep domain modules such as `evaluation/`, `data_conversion/`, and `data_utils/` in place.
- Keep `holosoma_retargeting/src/` in place for this phase. Rename or split it in a later phase.
- Keep `examples/` temporarily as compatibility wrappers, but remove it from the main path.

This gives a clear structure without doing a large, risky rewrite.

## Target Structure

```text
src/holosoma_retargeting/
  cli/
    __init__.py
    retarget.py
    parallel_retarget.py
    evaluate.py
    convert_mj.py
    replay.py

  pipelines/
    __init__.py
    retarget.py
    parallel.py
    motion_loading.py
    object_setup.py
    task_setup.py

  examples/
    __init__.py
    robot_retarget.py
    parallel_robot_retarget.py

  evaluation/
  data_conversion/
  data_utils/
  src/
  config_types/
  path_utils.py
  viser_player.py
```

## Layer Responsibilities

### `cli/`

`cli/` is the canonical Python entrypoint layer.

It should:

- parse CLI arguments with `tyro`
- call a small number of pipeline functions
- preserve direct execution with `python -m holosoma_retargeting.cli.<name>`
- avoid owning retargeting business logic

It should not:

- implement motion loading
- implement object setup
- construct retargeter internals directly
- be imported by lower-level modules

### `pipelines/`

`pipelines/` is an internal orchestration layer. It is deliberately small in this phase.

It should hold:

- task validation
- task constants assembly
- motion loading shared by single and parallel retargeting
- object setup shared by single and parallel retargeting
- retargeter kwargs assembly
- single-sequence retarget execution
- parallel task discovery and dispatch

It should not become a generic utility dumping ground. `data_utils/` remains data ingestion, `data_conversion/` remains export/conversion, and `evaluation/` remains evaluation.

### `examples/`

`examples/` should leave the main execution path. For safety, it remains as a compatibility layer in this phase.

The two old modules should become thin wrappers:

- `examples/robot_retarget.py` delegates to `cli/retarget.py` or `pipelines/retarget.py`.
- `examples/parallel_robot_retarget.py` delegates to `cli/parallel_retarget.py` or `pipelines/parallel.py`.

This preserves old imports while making the new architecture explicit.

### `holosoma_retargeting/src/`

`src/` currently contains the internal implementation layer:

- `interaction_mesh_retargeter.py`: core retargeting solver
- `utils.py`: runtime geometry, preprocessing, scene, and object helpers
- `mujoco_utils.py`: MuJoCo mesh bridge helpers
- `viser_utils.py`: Viser playback UI helpers

This phase does not rename it. The goal is to reduce direct entrypoint coupling to it, then address naming and splitting in a later refactor.

## Migration Strategy

1. Create `cli/` and `pipelines/` without changing behavior.
2. Move shared helper functions out of `examples/robot_retarget.py` into `pipelines/`.
3. Make `cli/retarget.py` call the single-retarget pipeline.
4. Make `cli/parallel_retarget.py` call the parallel pipeline and remove direct dependency on `examples/robot_retarget.py`.
5. Add thin `cli/evaluate.py`, `cli/convert_mj.py`, and `cli/replay.py` entrypoints that delegate to existing domain modules.
6. Convert `examples/` modules into compatibility wrappers.
7. Update shell wrappers and README references to the new `cli/` modules.

## Compatibility Rules

- Keep package name `holosoma_retargeting`.
- Keep existing shell wrapper names under `scripts/retargeting/`.
- Keep current model and demo-data locations.
- Keep `examples.*` import compatibility during this phase.
- Prefer `python -m holosoma_retargeting.cli.<entrypoint>` as the new documented path.

## Non-Goals

- No package rename to `omniretarget`.
- No `src/` rename to `core` or `engine` in this phase.
- No asset layout change.
- No `data_utils/` consolidation into a generic `utils/`.
- No algorithm changes.
- No broad `evaluation/` or `data_conversion/` internal rewrite.

## Risks

- Moving helpers can accidentally change import order or runtime defaults.
- Shell wrappers may still rely on package-directory working directory assumptions.
- Parallel execution can break if pipeline functions are not process-pickleable.
- Compatibility wrappers can hide stale imports if tests do not explicitly exercise the new `cli/` path.

## Verification Strategy

- Add import tests for all `holosoma_retargeting.cli.*` modules.
- Keep import tests for old `holosoma_retargeting.examples.*` modules during the compatibility phase.
- Add boundary tests that ensure parallel retargeting imports shared logic from `pipelines/`, not from `examples/`.
- Run the existing smoke suite.
- Run a package build to catch missing package data or invalid module paths.

## Success Criteria

- New `cli/` entrypoints exist and import cleanly.
- Retargeting shared logic lives in `pipelines/`, not in `examples/`.
- `examples/` remains only as a compatibility path.
- Shell wrappers use the new `cli/` modules.
- Existing smoke tests pass.
- `uv build` passes.
