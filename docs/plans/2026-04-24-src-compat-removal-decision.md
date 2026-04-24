# Historical `src` Compatibility Removal Decision

**Date:** 2026-04-24
**Status:** Keep wrappers for one more phase

## Decision

Keep `src/holosoma_retargeting/src/` as a thin compatibility layer for one more phase.
Do not delete the wrapper package in this phase.

## Why

1. The historical package has already been reduced to a pure compatibility bridge.
   - `src/holosoma_retargeting/src/__init__.py` is empty.
   - `src/holosoma_retargeting/src/interaction_mesh_retargeter.py`
   - `src/holosoma_retargeting/src/mujoco_utils.py`
   - `src/holosoma_retargeting/src/utils.py`
   - `src/holosoma_retargeting/src/viser_utils.py`
   all re-export from `solver/` or `utils/` only.

2. In-repo semantic usage is now tightly bounded, but not yet fully gone.
   - `tests/test_src_compatibility_census.py` constrains remaining semantic
     `holosoma_retargeting.src.*` references to:
     - `tests/test_module_entrypoints.py`
     - `tests/test_solver_module_boundaries.py`
   - Those references are intentional compatibility checks for this phase.

3. The package is still part of the distributed surface.
   - `pyproject.toml` includes `holosoma_retargeting*` in setuptools package
     discovery.
   - `src/holosoma_retargeting.egg-info/SOURCES.txt` still lists the
     `src/holosoma_retargeting/src/` wrapper files.

4. Existing migration plans still treat the wrapper package as an active
   compatibility bridge.
   - `docs/plans/2026-04-24-solver-utils-boundary-design.md`
   - `docs/plans/2026-04-24-solver-utils-boundary-plan.md`
   - `docs/plans/2026-04-24-utils-first-internal-split-plan.md`
   all assume legacy imports remain available during the ongoing refactor.

5. External compatibility is not yet explicitly retired.
   Deleting the wrapper package now would turn a controlled compatibility phase
   into a silent breaking change for any downstream user still importing
   `holosoma_retargeting.src.*`.

## Effect

- Treat `holosoma_retargeting.src.*` as a deprecation bridge only.
- Keep production modules off the historical package.
- Keep only explicit compatibility tests that make the remaining bridge visible.
- Skip Task 5 deletion work in this phase.
- Proceed to Task 6 phase verification with wrappers still present.

## Exit Criteria For Deletion

Delete `src/holosoma_retargeting/src/` only after all of the following are true:

1. The compatibility census allowlist is empty.
2. No docs or active plans still rely on the wrapper package as a live migration
   surface.
3. We explicitly accept breaking external `holosoma_retargeting.src.*` imports,
   or we define a separate deprecation/removal release step.
