# OmniRetarget Conservative Cleanup Design

## Goal

Clean up repository/package boundaries in `omniretarget` without changing public imports, shell entrypoints, runtime behavior, or asset layout.

## Scope

This phase is intentionally limited to boundary hygiene:

- move repo-level markdown documents out of `src/omniretarget/`
- delete obvious migration/runtime residue from the package tree
- stop packaging repo docs into distribution artifacts
- keep current code paths, CLI paths, assets, and imports stable

## Non-Goals

- no package rename from `omniretarget`
- no refactor of `examples/`, `evaluation/`, `data_conversion/`, or `src/`
- no relocation of `models/` or `demo_data/`
- no change to `scripts/retargeting/*.sh` UX
- no change to algorithm, configuration, or task behavior

## Design Constraints

- Existing imports such as `omniretarget.examples.robot_retarget` must continue to work.
- Existing shell wrappers under `scripts/retargeting/` must continue to work.
- Package-level runtime assets (`models/`, `demo_data/`, `*.jinja`) remain packaged.
- Repo-level docs should live under `docs/`, not under `src/omniretarget/`.

## Proposed Changes

### 1. Separate repo docs from package contents

Move the following files from the package root into `docs/`:

- `src/omniretarget/ADD_MOTION_FORMAT_README.md`
- `src/omniretarget/ADD_ROBOT_TYPE_README.md`
- `src/omniretarget/ADAM_PRO_ROBOT_ONLY_SUMMARY.md`

These are not runtime assets. They describe usage, extension, and migration context at the repository level.

### 2. Keep only a package-local README in the package root

Retain `src/omniretarget/README.md`, but narrow it to package-local usage:

- direct Python entrypoints
- package-level path assumptions
- links to repo docs in `docs/`

This keeps `src/omniretarget` self-describing without treating the package directory as the repo docs home.

### 3. Remove obvious package residue

Delete:

- `src/omniretarget/MUJOCO_LOG.TXT`
- `src/omniretarget/.gitignore`

These are not source code, not runtime assets, and not useful as shipped package contents.

### 4. Narrow the package data boundary

Update `MANIFEST.in` so repo docs are no longer packaged. Keep only:

- `models/`
- `demo_data/`
- `*.jinja`

This makes build artifacts closer to runtime needs and reduces distribution noise.

## Why This Is Safe

- Python import paths are untouched.
- Runtime asset paths remain under the same package root.
- Shell wrappers keep the same command paths.
- Documentation link updates are mechanical and easy to verify.
- Build verification will confirm that markdown docs no longer ship in the wheel/sdist package payload.

## Follow-On Work Enabled By This Cleanup

This phase creates a cleaner starting point for the later medium refactor:

- splitting app-layer orchestration from library logic
- renaming `src/omniretarget/src/` to a semantic module name
- deciding whether demo assets should remain package-local

## Success Criteria

- No repo-level docs remain inside `src/omniretarget/` except the package-local README.
- No `MUJOCO_LOG.TXT` or package-local `.gitignore` remains in the package tree.
- `MANIFEST.in` no longer includes package markdown docs.
- `bash scripts/test_smoke.sh` still passes.
- `uv build` still passes.
- Built artifacts no longer package the moved markdown docs under `omniretarget/`.
