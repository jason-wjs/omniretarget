# OmniRetarget Refactor Overview Plan

## Goal

Make `omniretarget` the standalone, maintainable home for Holosoma's retargeting functionality.

This refactor should improve project boundaries, configuration clarity, runtime path handling, command-line usability, and documentation ownership while preserving the existing retargeting behavior during the early migration stages.

## Repository Policy

- `omniretarget/` is the source of truth for ongoing work.
- `holosoma/` is read-only reference material.
- `omniretarget-refactor-deprecated/` is a deprecated draft worktree and should not be used as design input.
- Active refactor work happens in the `omniretarget-refactor-next/` worktree on the `refactor-next` branch.
- Refactor phases should stay conservative: preserve behavior first, then improve structure.

## Target Repository Layout

```text
omniretarget/
  docs/
  scripts/
  src/
    holosoma_retargeting/
      cli/
        data_process/
      configs/
      demo_data/
      models/
      profiles/
      retargeter/
      utils/
      path_utils.py
  tests/
  README.md
  pyproject.toml
```

## Root-Level Responsibilities

### `README.md`

The repository has one primary README at the root.

The root README should explain what the project is, how to install it, how to run the main commands, where packaged assets live, and where deeper docs can be found. Package directories should not contain standalone README files.

### `docs/`

Project documentation root.

This directory contains migration notes, design records, usage docs, extension guides, and staged refactor plans. Architecture decisions should be written here before broad structural changes are made.

Long-form docs that are not appropriate for the root README should live under `docs/`, not under `src/holosoma_retargeting/`.

### `scripts/`

Developer and shell convenience scripts.

This directory may contain shell wrappers, smoke-test helpers, data preparation commands, or migration utilities. It should not contain the primary Python business logic for retargeting, evaluation, conversion, preprocessing, or visualization.

Over time, shell scripts should call installed Python CLI commands instead of invoking package files through ad hoc relative paths.

### `tests/`

Project test suite.

Tests should cover the behavior that must survive the refactor: package-relative paths, retained assets, robot configuration contracts, motion format compatibility, command smoke behavior, core retargeting behavior, and repository documentation boundaries.

## Documentation Policy

- Keep exactly one primary project README: root-level `README.md`.
- Do not keep standalone Markdown docs in package directories.
- Move package-level usage notes, robot extension guides, motion format guides, and migration notes into `docs/`.
- Keep package-internal documentation as Python docstrings or concise module comments.
- Add or retain tests that prevent package-root residue files such as extra README files, logs, or old migration notes from returning.

## Package-Level Responsibilities

### `cli/`

Formal Python command modules.

This module is the installed command surface for users and developers. It should contain executable workflows such as single-motion retargeting, batch retargeting, evaluation, conversion, replay, and visualization.

Unlike a thin wrapper-only CLI layer, these modules may own command-specific orchestration: parsing typed config through Tyro, resolving runtime configuration, finding input files, constructing retargeters or evaluators, calling utility helpers, writing outputs, and reporting command results.

They should not own core retargeting algorithms, reusable low-level geometry/MuJoCo/mesh utilities, robot or motion profile registries, or shared runtime config resolution.

Expected early command modules include:

- `cli/robot_retarget.py`
- `cli/parallel_robot_retarget.py`
- `cli/eval_retargeting.py`
- `cli/viser_player.py`

### `cli/data_process/`

Formal data preprocessing and conversion command modules.

This subpackage groups executable commands that prepare external datasets or convert retargeting outputs. It keeps data-processing entrypoints visible without adding a top-level `io/` or `pipelines/` layer.

Expected early command modules include:

- `cli/data_process/convert_data_format_mj.py`
- `cli/data_process/prep_amass_smplx_for_rt.py`
- `cli/data_process/prep_optitrack_for_rt.py`
- `cli/data_process/extract_global_positions.py`

These modules may contain command-specific orchestration. Reusable file loading, result writing, preprocessing, and conversion helpers can move into cohesive modules under `utils/` when that improves readability or removes real duplication.

### `configs/`

Typed configuration schema, validation, and runtime resolution.

This module should keep the conservative `dataclass` + Tyro configuration model. It should not introduce Hydra YAML configuration as part of the target architecture.

The long-term goal is to replace the current split between `config_types/` and `config_values/` with a clearer configuration layer:

- typed run configs for retargeting, batch retargeting, evaluation, conversion, replay, and preprocessing;
- validation rules for user-provided options;
- runtime config resolution that reconciles top-level selections such as `robot`, `data_format`, and `task_type` with nested config objects;
- compatibility helpers that provide legacy uppercase constants only where still needed during migration.

`config_values/` should not survive as a separate long-term layer unless it gains a real responsibility beyond thin factories and Tyro wrappers.

### `profiles/`

Built-in robot, motion, and mapping profiles.

This module should contain project-owned domain defaults that are not themselves command-line schema:

- robot defaults, DOF, heights, manual limits, foot links, and nominal tracking indices;
- motion format demo joints, toe names, scale defaults, and format-specific metadata;
- robot-motion joint mapping registries.

Keeping these profiles separate from `configs/` prevents configuration schema from becoming a dumping ground for domain constants.

### `models/`

Packaged static model assets.

This existing directory contains robot and object assets required by the package at runtime, including robot URDF/XML files, object URDF/XML/mesh files, templates, and small scene assets.

It is a data directory, not a Python module for path resolution. It should remain in place for the early refactor stages because XML/URDF files contain many relative mesh references.

### `demo_data/`

Packaged sample motion data.

This existing directory contains packaged sample motion data and small fixtures needed for examples, documentation, smoke tests, and regression tests.

Large external datasets should not be stored here. They should be referenced through typed path configuration.

### `path_utils.py`

Package-relative path utilities.

This module is responsible for eliminating current working directory assumptions. It should provide lightweight helpers for resolving packaged resources such as assets, sample motion data, and generated output locations.

At the overview stage, this remains a small path utility module rather than a broader asset resolver abstraction.

### `retargeter/`

Core retargeting algorithm layer.

This module owns interaction-mesh retargeting, retargeting constraints, solver construction, per-frame optimization, and behavior currently centered around `interaction_mesh_retargeter.py`.

Initial refactor work should preserve the existing retargeter interface. Internal decomposition can happen later after command, configuration, and utility boundaries are stable.

### `utils/`

Cohesive reusable support modules.

This module should hold reusable support logic used by CLI commands, runtime config resolution, evaluation, conversion, visualization, preprocessing, and the retargeter.

It does not have a fixed file list at the overview stage. During refactor, new utility modules may be introduced when they have a clear responsibility and improve readability or remove meaningful duplication. Good utility module names should describe responsibility, such as motion IO, pose transforms, MuJoCo model helpers, mesh sampling, object asset helpers, retarget output helpers, visualization helpers, or preprocessing helpers.

The goal is not to create a generic dumping ground. Avoid broad files such as `misc.py`, `common.py`, or catch-all modules. If logic is only used by one CLI command and is part of that command's workflow, keep it local until reuse or readability pressure justifies extraction.

## Deferred Module Decisions

### `pipelines/`

A separate `pipelines/` package is intentionally avoided at this stage.

Existing executable workflows should move into `cli/` as formal command modules. Shared low-level or reusable logic should move into `configs/`, `profiles/`, `retargeter/`, or cohesive modules under `utils/`.

A workflow layer can be reconsidered only if multiple CLI commands later share substantial orchestration logic that does not fit those modules.

### Hydra YAML configuration

Hydra is intentionally not part of the target architecture.

The project should continue with typed dataclasses and Tyro unless a later design record shows clear pressure for YAML composition that outweighs the added migration and dependency cost.

### Runtime motion adapters

A separate `adapters/` package is not part of the first overview target.

The current motion-format branching can remain inside command modules while the project architecture is stabilized. If format-specific loading logic grows across multiple commands, cohesive helpers can first be introduced under `utils/`. A dedicated adapter layer should be added only after repeated patterns justify it.

### Asset resolver abstraction

A separate Python asset resolver module is intentionally avoided at the overview stage.

Path resolution should start in `path_utils.py`. A broader resolver can be introduced later only if package-relative path helpers become insufficient.

## Legacy Module Migration Map

This section maps the current `holosoma_retargeting/` package layout to the target architecture at a module level. It is intentionally high level; each migration stage should still get its own implementation plan.

### `config_types/` and `config_values/`

These modules should eventually be replaced by `configs/` and `profiles/`.

`configs/` should hold typed dataclass schemas, validation, runtime resolution, and legacy compatibility helpers. `profiles/` should hold robot defaults, motion format metadata, and joint mapping registries.

Early refactor stages may keep `config_types/` import paths as compatibility shims. `config_values/` should be removed or collapsed once its thin factory functions no longer provide value.

### `examples/`

The current `examples/` modules are production workflow entrypoints rather than examples.

Their command logic should move into `cli/`. If example scripts remain, they should become thin demonstration wrappers around official CLI commands or documented command examples.

### `data_utils/`

This directory is best understood as offline preprocessing, not generic runtime utilities.

It prepares external raw datasets such as AMASS SMPL-X, LAFAN BVH, and OptiTrack data into formats that retargeting can consume. Executable preprocessing entrypoints should move into `cli/data_process/`.

Reusable low-level helpers can move into `utils/` if they are genuinely shared or make the command modules easier to read.

### `data_conversion/`

This directory is a post-retargeting conversion workflow.

Its main role is converting retargeted robot trajectories into downstream formats such as RL whole-body tracking data, including interpolation, MuJoCo replay, velocity computation, and body-state export.

Executable conversion entrypoints should move into `cli/data_process/` or another command module under `cli/` if the command is primarily replay or visualization. Reusable low-level helpers can move into `utils/`.

### `evaluation/`

This directory is a post-retargeting evaluation workflow.

The executable evaluation command should move into `cli/`. Reusable geometry or MuJoCo helpers can move into `utils/`, but evaluation-specific workflow code can remain in the CLI command until real reuse pressure appears.

### Current package `src/`

The current package-internal `src/` directory should disappear as a semantic module name.

Its contents should be redistributed by responsibility:

- `interaction_mesh_retargeter.py` moves into `retargeter/`.
- Runtime support utilities move into cohesive modules under `utils/`.
- MuJoCo-specific helpers move into `utils/` unless they are tightly coupled to the retargeter solver.
- Viser-specific helpers move into `utils/` or command-specific visualization support under `cli/`.

### `models/`

This directory remains in place during early refactor stages.

It is runtime package data containing robot and object assets. It should not be renamed or reorganized until XML/URDF relative mesh references are fully accounted for.

### `demo_data/`

This directory remains in place during early refactor stages.

It is package-local sample and fixture data. Large external datasets should remain outside the package and be referenced through typed path configuration.

### `path_utils.py`

This module should remain the first place to improve package-relative path handling.

It can grow modestly to cover path helpers required by the refactor, but it should not become a heavyweight asset abstraction unless repeated path patterns justify that later.

### Package-level Markdown files

Markdown files under `src/holosoma_retargeting/` should not remain part of the target package layout.

Useful package README content should move to the root README or to focused docs under `docs/`. Obsolete package-level notes should be deleted during cleanup phases.

## Design Principles

- Preserve current retargeting behavior before changing algorithm internals.
- Prefer staged migration over broad rewrites.
- Keep executable workflows in formal `cli/` command modules.
- Avoid a `pipelines/` layer until repeated orchestration pressure justifies it.
- Keep core optimization and retargeting logic in `retargeter/`.
- Keep configuration as typed dataclasses parsed by Tyro.
- Separate user-facing config schema from built-in robot and motion profiles.
- Keep shared support code in cohesive utility modules, not broad catch-all files.
- Keep existing packaged `models/` and `demo_data/` layouts stable during early refactor stages.
- Keep large datasets outside the package and reference them through configuration.
- Keep one project README at the repository root.
- Avoid premature abstractions such as plugin-style adapters, heavyweight asset resolvers, or generic workflow bases until real pressure appears.

## Refactor Direction

The refactor should proceed from the outside inward:

1. Stabilize repository boundaries, documentation boundaries, and baseline tests.
2. Introduce the target documentation, command, configuration, and profile structure.
3. Improve package-relative path handling through `path_utils.py` while preserving the current `models/` and `demo_data/` layouts.
4. Move executable Python entrypoints into `cli/` and data-processing entrypoints into `cli/data_process/`.
5. Consolidate typed configuration schemas and runtime resolution under `configs/`.
6. Move robot defaults, motion format defaults, and joint mappings under `profiles/`.
7. Move retargeting algorithm code into `retargeter/`.
8. Split broad utility code into cohesive modules under `utils/` as readability and reuse justify it.
9. Remove or convert legacy compatibility shims after command and import users have migrated.

Each stage should define its own implementation plan before code changes begin.

## Success Criteria

- The project can be understood as a standalone retargeting package without referring to unrelated Holosoma modules.
- The repository has exactly one primary README at the root.
- Package-level Markdown docs and residue files are removed or moved under `docs/`.
- Runtime assets and sample motion data remain in stable package-local locations.
- Formal Python command modules are separated from shell convenience scripts.
- Data preprocessing and conversion commands are grouped under `cli/data_process/`.
- Core retargeting algorithms are separated from executable command modules.
- Configuration remains typed dataclass + Tyro based, with validation and runtime resolution centralized in Python.
- Built-in robot, motion format, and mapping defaults are separated from command-line config schema.
- Shared support logic is organized into cohesive `utils/` modules only when extraction improves readability or removes real duplication.
- Existing behavior remains covered by tests throughout the migration.
