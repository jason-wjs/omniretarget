# Solver Internal Split Design

## Goal

Split `src/holosoma_retargeting/solver/interaction_mesh_retargeter.py` into smaller solver-local modules while preserving the public `InteractionMeshRetargeter` entrypoint and current pipeline behavior.

## Context

After the `src -> solver/utils` move and the `utils/` internal split, the largest remaining architectural hotspot is `solver/interaction_mesh_retargeter.py`.

The file is currently about 1100 lines and mixes five different responsibilities:

- solver/runtime initialization and model loading
- visualization setup and debug drawing
- frame-by-frame motion retargeting orchestration
- SQP-style optimization and iteration control
- MuJoCo geometry, contact, and Jacobian helpers

That makes the file hard to review and risky to change. A bug in any one area forces readers to load the whole class into context.

The recent `parallel.py` regression also showed that this refactor branch now benefits more from tightening behavioral tests around orchestration boundaries before doing deeper decomposition.

## Selected Approach

Use a conservative extraction strategy:

1. Keep `InteractionMeshRetargeter` as the only public solver entrypoint.
2. Extract internal helper groups into solver-local modules with module functions.
3. Update the class to delegate to those helpers without changing pipeline call sites.
4. Leave the optimization core and sequence driver in the class until the helper boundaries are proven stable.

This is deliberately not a "split everything at once" rewrite. The class remains the facade; the extracted modules become implementation detail.

## Why This Approach

There are three plausible ways to split the file:

### Option A: Extract helper modules, keep the class facade

Create small solver-local modules such as:

- `solver/visualization.py`
- `solver/kinematics.py`
- `solver/collision.py`

Then make `InteractionMeshRetargeter` delegate to them.

Pros:

- low import-path churn
- public API stays unchanged
- easiest to verify incrementally
- avoids touching optimization flow and pipelines at the same time

Cons:

- the class still owns substantial state
- some helpers must still accept the retargeter instance or several state fields

### Option B: Split the class into multiple collaborating classes

Introduce classes such as `RetargetingVisualizer`, `CollisionBackend`, and `OptimizationKernel`.

Pros:

- cleaner OO boundaries on paper
- clearer ownership if the split is fully completed

Cons:

- much higher state-migration risk
- constructor churn
- more likely to introduce subtle behavioral regressions

### Option C: Rewrite around typed solver context first

Introduce dedicated solver state/config dataclasses before extracting code.

Pros:

- strongest long-term shape
- reduces reliance on mutable class state

Cons:

- too large for the next safe phase
- overlaps with later runtime-spec work

## Recommendation

Choose Option A now.

The file already has a natural internal shape:

- visualization block: `_setup_visualization`, `draw_*`, `visualize_*`
- geometry/Jacobian/contact block: `_compute_jacobian_for_contact_relative`, `_prefilter_pairs_with_mj_collision`, `_update_jacobians_and_phis_from_q`, `_build_transform_qdot_to_qvel_fast`, `_calc_contact_jacobian_from_point`, `_calc_manipulator_jacobians`, `_get_robot_link_positions`
- orchestration/optimization block: `retarget_motion`, `solve_single_iteration`, `iterate`

Option A lets us extract the first two groups and stop there if the branch needs to stay stable.

## Target Structure

```text
src/holosoma_retargeting/solver/
  __init__.py
  interaction_mesh_retargeter.py   # facade + optimization/orchestration core
  visualization.py                 # viser setup and drawing helpers
  kinematics.py                    # qdot/qvel transforms, jacobians, link positions
  collision.py                     # candidate filtering, contact Jacobians, phi/J assembly
```

## Responsibility Boundaries

### `interaction_mesh_retargeter.py`

Keeps:

- `InteractionMeshRetargeter`
- `__init__`
- `retarget_motion`
- `solve_single_iteration`
- `iterate`

Owns:

- public solver API
- state initialization
- optimization loop and sequence loop
- coordination across helper modules

Does not newly absorb:

- extra pipeline logic
- CLI concerns
- asset/path resolution work

### `visualization.py`

Owns:

- viser server setup
- mesh drawing
- keypoint drawing
- motion playback helpers

Functions should be stateless where practical and operate on explicit inputs or the retargeter facade.

This block is the lowest-risk first extraction because it is isolated behind `visualize` / `debug` modes and not on the strict optimization path.

### `kinematics.py`

Owns:

- qdot-to-qvel mapping
- point Jacobians
- manipulator Jacobians
- robot link world positions
- small frame transforms used by these helpers

This block is computationally central but conceptually cohesive.

### `collision.py`

Owns:

- candidate pair prefiltering
- relative contact Jacobian assembly
- signed distance / `phi` update helpers

It depends on MuJoCo model/data state and should stay solver-local rather than being pushed into generic `utils/`.

## Explicit Non-Goals For The Next Phase

- No public API rename for `InteractionMeshRetargeter`
- No pipeline call-signature changes
- No attempt to remove the class facade
- No optimization algorithm rewrite
- No migration to typed runtime specs inside the solver yet
- No deletion of compatibility wrappers under `holosoma_retargeting.src`

## Extraction Order

### Step 1: Lock orchestration behavior

Before touching solver code, add a regression test around the multi-augmentation `parallel.py` path so the recently fixed config/instance shadowing bug stays covered.

### Step 2: Extract visualization helpers

Move only the visualization/drawing methods into `solver/visualization.py` as helper functions. Update the class methods to delegate.

Reason:

- mostly orthogonal to optimization
- smallest blast radius
- easy to review by source movement

### Step 3: Extract kinematics helpers

Move Jacobian and link-position helpers into `solver/kinematics.py`.

### Step 4: Extract collision helpers

Move pair prefiltering and contact-distance/Jacobian update helpers into `solver/collision.py`.

### Step 5: Stop and verify

Leave `retarget_motion`, `solve_single_iteration`, and `iterate` in the main class after the first extraction pass.

That gives a meaningful size reduction without turning the optimization core into a moving target.

## Risks

- The helper functions still depend on mutable solver state (`robot_model`, `robot_data`, `q_a_indices`, flags), so careless extraction could produce opaque parameter lists or hidden circular dependencies.
- Visualization code touches optional dependencies (`viser`, `yourdfpy`), so import placement must stay compatible with current module entrypoint tests.
- MuJoCo helpers are tightly coupled to current qpos/qvel conventions; splitting them without targeted tests could create silent Jacobian errors.

## Verification Strategy

- Add a regression test for `parallel.process_single_task()` multi-augmentation behavior before solver edits.
- Add import-boundary tests for the new solver helper modules.
- Keep `InteractionMeshRetargeter` importable from the existing solver entrypoint.
- Run focused tests covering:
  - solver module imports
  - pipeline boundaries
  - the new parallel regression
- Run the smoke suite and package build.

## Success Criteria

- `interaction_mesh_retargeter.py` is materially smaller and more readable.
- solver-local helper modules own visualization, kinematics, and collision support logic.
- `InteractionMeshRetargeter` remains the stable public entrypoint.
- existing pipelines and compatibility layers do not need API changes.
- focused tests, smoke, and build all stay green.
