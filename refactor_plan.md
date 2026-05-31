# OmniRetarget Architecture Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deepen the repository architecture without losing any workflow behavior currently supported by `main`.

**Architecture:** Refactor one seam at a time behind compatibility wrappers. Runtime behavior must stay aligned with `main` while `Runtime Context`, `Retargeting Pipeline`, robot/motion specs, MuJoCo query logic, and trajectory solver internals move into deeper modules.

**Tech Stack:** Python 3.11, uv, pytest, tyro, NumPy, MuJoCo, CVXPY/Clarabel, Viser, trimesh, libigl.

---

## Current Baseline

Refactor branch:

```text
arch/retargeting-runtime-refactor
```

Current worktree:

```text
/home/humanoid/Projects/Junsong_WU/learning/locomotion/RETARGET/omniretarget-arch-refactor
```

Baseline after rebasing onto current `main`:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

Expected baseline:

```text
115 passed, 1 skipped
```

Phase 0 safety checkpoint already exists:

```text
9b99752 docs: record architecture refactor safety contract
```

## Non-Negotiable Rule

Every phase must preserve current `main` behavior. A structural improvement that drops a supported workflow is a failed refactor.

Do not change these without explicit review:

- CLI arguments
- output `.npz` schemas
- PARC paired-output manifest schema
- PARC terrain collision manifest schema
- asset path conventions
- height-origin conventions
- robot/data-format extension contracts
- public import paths used by current tests or README commands

## Protected Workflows

Each phase must keep these workflows aligned with current `main`:

1. Single retargeting: `src/omniretarget/examples/robot_retarget.py`
2. Parallel retargeting: `src/omniretarget/examples/parallel_robot_retarget.py`
3. PARC process: `src/omniretarget/examples/parc_process.py`
4. PARC batch to MJ: `src/omniretarget/examples/parc_batch_process_to_mj.py`
5. PARC batch visualization: `src/omniretarget/examples/parc_batch_vis.py`
6. Standard MJ conversion: `src/omniretarget/data_conversion/convert_data_format_mj.py`
7. PARC MJ conversion: `src/omniretarget/data_conversion/convert_data_format_parc_mj.py`
8. Viser replay: `src/omniretarget/viser_player.py`
9. Quantitative evaluation: `src/omniretarget/evaluation/eval_retargeting.py`
10. Robot/data-format extension docs:
    - `docs/add-robot-type.md`
    - `docs/add-motion-format.md`
11. Model and asset path behavior, especially:
    - G1 XML and STL assets
    - PARC workspace assets
    - terrain visual assets
    - terrain collision manifests
    - PARC height-origin normalization

## Global Safety Gates

Before starting any phase:

- [ ] Confirm worktree status is clean.

```bash
git status --short --branch
```

Expected:

```text
## arch/retargeting-runtime-refactor...origin/arch/retargeting-runtime-refactor
```

- [ ] Confirm branch is up to date with its remote before editing.

```bash
git fetch origin
git status --short --branch
```

Expected: no ahead/behind markers unless intentionally continuing local work.

After each small change touching protected workflows:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_module_entrypoints.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_process.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_batch_process_to_mj.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_batch_vis.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_convert_data_format_parc_mj.py
```

At the end of every phase:

```bash
git diff --check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

Expected:

```text
115 passed, 1 skipped
```

If the total test count changes, record why in the phase commit message or PR notes.

## Global Stop Conditions

Stop immediately and reassess if any of these happen:

- A supported CLI needs argument changes.
- A supported output schema changes.
- Existing tests need broad rewrites just to preserve previous behavior.
- A phase requires simultaneous edits across single retargeting, parallel retargeting, PARC processing, evaluation, and conversion.
- `InteractionMeshRetargeter` public behavior must be broken to continue.
- PARC height-origin, terrain visual, terrain collision, or MJ export behavior becomes ambiguous.
- A compatibility wrapper becomes more complex than the new module it wraps.

## Commit Strategy

Use small commits with a single reason:

```text
test: add runtime context parity coverage
refactor: add runtime context module
refactor: route retargeting constants through runtime context
refactor: route evaluation constants through runtime context
docs: update runtime context refactor notes
```

Avoid broad commits:

```text
refactor: reorganize codebase
```

Each phase should end with a pushed checkpoint:

```bash
git push
```

## Final Target Layout

The final architecture should move toward this shape:

```text
src/omniretarget/
  config_types/
    robot.py
    data_type.py
    task.py
    retargeter.py
    retargeting.py

  specs/
    __init__.py
    robots.py
    motion_formats.py
    mappings.py

  runtime/
    __init__.py
    context.py
    assets.py
    validation.py

  retargeting/
    __init__.py
    pipeline.py
    batch.py
    motion_source.py
    object_setup.py
    preprocessing.py
    initialization.py
    augmentation.py
    results.py

  solver/
    __init__.py
    interaction_mesh.py
    trajectory.py
    frame_problem.py
    constraints.py
    optimizer.py

  mujoco/
    __init__.py
    model_state.py
    kinematics.py
    collision.py
    assets.py

  visualization/
    __init__.py
    viser_adapter.py
    player.py

  parc_process/
    ...

  examples/
    robot_retarget.py
    parallel_robot_retarget.py
    parc_process.py
    parc_batch_process_to_mj.py
    parc_batch_vis.py
```

Final dependency direction:

```text
CLI Adapter
  -> Retargeting Pipeline / PARC Workflow
    -> Runtime Context
    -> Motion Source / Object Setup / Initialization / Preprocessing
    -> Trajectory Solver
      -> MuJoCo Query
      -> Optimizer Adapter
```

`evaluation` and `data_conversion` should consume `Runtime Context` and MuJoCo query modules instead of reconstructing constants independently.

---

## Phase 0: Refactor Safety Baseline

**Status:** Complete.

**Goal:** Record shared domain vocabulary and a safety contract before moving code.

**Files:**

- Created: `CONTEXT.md`
- Created: `docs/architecture-refactor-safety.md`
- Created: `refactor_plan.md`

**Allowed changes:**

- Documentation only.
- No runtime code changes.

**Safety checks:**

```bash
git diff --check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_repo_doc_boundaries.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

**Exit criteria:**

- Domain vocabulary exists for `Runtime Context`, `Retargeting Pipeline`, `Motion Source`, `Object Setup`, `PARC Workflow`, `Height Origin`, `MuJoCo Query`, `Trajectory Solver`, and `CLI Adapter`.
- Protected workflows are listed.
- Phase plan exists and is committed.

---

## Phase 1: Runtime Context Seam

**Status:** Complete.

**Verification note:** Phase 1 adds 9 runtime-context parity tests, so the full-suite count changes from `115 passed, 1 skipped` to `124 passed, 1 skipped`.

**Goal:** Create one deep module for resolved robot, motion, task, object, scene, and asset facts while preserving every old caller interface.

**Problem being solved:** The repository currently reconstructs task constants in multiple places:

- `src/omniretarget/examples/robot_retarget.py`
- `src/omniretarget/evaluation/eval_retargeting.py`
- `src/omniretarget/data_conversion/convert_data_format_mj.py`

Those modules each know parts of `OBJECT_NAME`, `OBJECT_URDF_FILE`, `OBJECT_MESH_FILE`, `SCENE_XML_FILE`, robot constants, motion constants, and mapping rules. This is shallow because callers must know too much about runtime facts.

**Target modules:**

```text
src/omniretarget/runtime/
  __init__.py
  context.py
  assets.py
  validation.py
```

**Initial interface shape:**

```python
@dataclass
class RuntimeContext:
    robot_config: RobotConfig
    motion_data_config: MotionDataConfig
    task_config: TaskConfig
    task_type: str
    object_name: str
    object_dir: Path | None
    robot_urdf_file: str
    object_urdf_file: str | None
    object_mesh_file: str | None
    object_urdf_template: str | None
    scene_xml_file: str | None

    def to_legacy_namespace(self) -> SimpleNamespace:
        ...
```

The exact implementation can evolve, but `to_legacy_namespace()` is mandatory during this phase because existing callers and tests depend on uppercase constant fields.

**Parity fields:**

Compare old and new behavior for:

- `ROBOT_DOF`
- `ROBOT_HEIGHT`
- `ROBOT_NAME`
- `ROBOT_URDF_FILE`
- `FOOT_STICKING_LINKS`
- `MANUAL_LB`
- `MANUAL_UB`
- `MANUAL_COST`
- `NOMINAL_TRACKING_INDICES`
- `DEMO_JOINTS`
- `JOINTS_MAPPING`
- `TOE_NAMES`
- `DEFAULT_SCALE_FACTOR`
- `DEFAULT_HUMAN_HEIGHT`
- `OBJECT_NAME`
- `OBJECT_DIR`
- `OBJECT_URDF_FILE`
- `OBJECT_MESH_FILE`
- `OBJECT_URDF_TEMPLATE`
- `SCENE_XML_FILE`

**Phase tasks:**

- [x] Add tests comparing `robot_retarget.create_task_constants()` to `RuntimeContext.to_legacy_namespace()` for:
  - `robot_only` / `lafan` / `adam_pro`
  - `object_interaction` / `smplh` / `adam_pro`
  - `climbing` / `mocap` / `g1`
  - `climbing` / `parc_humanoid` / `g1`

- [x] Add tests comparing `evaluation.eval_retargeting.create_task_constants()` to the new runtime-context equivalent for:
  - `object_name="ground"`
  - `object_name="largebox"`
  - `object_name="multi_boxes"` with `object_dir`

- [x] Add tests comparing `data_conversion.convert_data_format_mj.create_task_constants()` to the new runtime-context equivalent for:
  - `object_name="ground"`
  - `object_name="largebox"`

- [x] Create `src/omniretarget/runtime/__init__.py`.

- [x] Create `src/omniretarget/runtime/assets.py` for path resolution only:
  - robot URDF path
  - robot XML path
  - object URDF path
  - object mesh path
  - object URDF template path
  - scene XML path

- [x] Create `src/omniretarget/runtime/context.py` with `RuntimeContext` and builder functions.

- [x] Create `src/omniretarget/runtime/validation.py` only for compatibility checks already present in existing code.

- [x] Change `robot_retarget.create_task_constants()` into a compatibility wrapper around `RuntimeContext`.

- [x] Change `evaluation.eval_retargeting.create_task_constants()` into a compatibility wrapper around `RuntimeContext`.

- [x] Change `data_conversion.convert_data_format_mj.create_task_constants()` into a compatibility wrapper around `RuntimeContext`.

- [x] Do not change `InteractionMeshRetargeter` constructor in this phase.

**Focused checks:**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_adam_pro_object_interaction_mapping.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_eval_contact_joint_defaults.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_convert_data_format_parc_mj.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_process.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_module_entrypoints.py
```

**Phase exit criteria:**

- Old `create_task_constants()` functions still exist.
- New runtime module owns shared context construction.
- Existing callers behave the same.
- Full tests pass.

**Phase stop conditions:**

- A parity test reveals existing caller-specific behavior that cannot be expressed by `RuntimeContext` without changing output behavior.
- `RuntimeContext` requires special cases for all callers instead of concentrating shared behavior.
- PARC height-origin fields become unclear.

---

## Phase 2: Retargeting Pipeline Seam

**Status:** Complete.

**Verification note:** Phase 2 adds retargeting seam tests and new import-coverage cases, so the full-suite count changes from `124 passed, 1 skipped` to `159 passed, 1 skipped`.

**Goal:** Move retargeting workflow logic out of `examples/` into a deeper `retargeting` module while keeping CLI adapters stable.

**Problem being solved:** `src/omniretarget/examples/robot_retarget.py` is not just an example. It owns the single-clip pipeline, and `parallel_robot_retarget.py` imports its helper functions. This makes `examples` a hidden core module.

**Target modules:**

```text
src/omniretarget/retargeting/
  __init__.py
  pipeline.py
  motion_source.py
  object_setup.py
  preprocessing.py
  initialization.py
  augmentation.py
  results.py
  batch.py
```

**Compatibility requirement:**

These existing entry points must still import and run:

- `omniretarget.examples.robot_retarget`
- `omniretarget.examples.parallel_robot_retarget`
- `omniretarget.examples.parc_process`
- `omniretarget.examples.parc_batch_process_to_mj`

**Phase tasks:**

- [x] Add tests that import new `omniretarget.retargeting` modules without mutating `sys.path`.

- [x] Move `load_motion_data()` behavior to `retargeting/motion_source.py`.

- [x] Keep `examples.robot_retarget.load_motion_data()` as a wrapper.

- [x] Move `create_ground_points()` and `setup_object_data()` behavior to `retargeting/object_setup.py`.

- [x] Keep old functions in `examples.robot_retarget` as wrappers.

- [x] Move object pose order conversion and q initialization to `retargeting/initialization.py`.

- [x] Keep old initialization functions as wrappers.

- [x] Move foot-sticking preprocessing orchestration to `retargeting/preprocessing.py` only after wrappers pass parity tests.

- [x] Move augmentation plan generation from `parallel_robot_retarget.py` to `retargeting/augmentation.py`.

- [x] Create `retargeting/results.py` for output path naming and `.npz` result conventions.

- [x] Create `retargeting/pipeline.py` with a single-clip workflow function.

- [x] Change `examples/robot_retarget.py` into a CLI adapter that calls `retargeting.pipeline`.

- [x] Create `retargeting/batch.py` for batch orchestration.

- [x] Change `examples/parallel_robot_retarget.py` into a CLI adapter that calls `retargeting.batch`.

- [x] Do not move PARC batch visualization in this phase.

**Focused checks:**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_module_entrypoints.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_process.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_batch_process_to_mj.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_batch_retarget_script_optitrack.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_optitrack_grounding_preprocess.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_foot_sticking_contact_keys.py
```

**Phase exit criteria:**

- `examples/robot_retarget.py` and `examples/parallel_robot_retarget.py` are thin CLI adapters.
- Old helper function names remain available through wrappers.
- No output naming or `.npz` schema changes.
- Full tests pass.

**Phase stop conditions:**

- The pipeline move requires changing solver behavior.
- Parallel retargeting cannot call the same pipeline without changing augmentation outputs.
- PARC process behavior diverges from single-clip retargeting.

---

## Phase 3: Robot and Motion Spec Registries

**Status:** Complete.

**Verification note:** Phase 3 adds 9 specs registry parity tests, so the full-suite count changes from `159 passed, 1 skipped` to `168 passed, 1 skipped`.

**Goal:** Move robot and motion-format facts into deeper spec modules while keeping `config_types` as the public configuration interface.

**Problem being solved:** `config_types/robot.py` and `config_types/data_type.py` mix CLI-facing dataclasses, validation, defaults, robot-specific profiles, motion-format joint names, and mapping registries.

**Target modules:**

```text
src/omniretarget/specs/
  __init__.py
  robots.py
  motion_formats.py
  mappings.py
```

**Compatibility requirement:**

Existing imports from these modules must continue to work:

- `omniretarget.config_types.robot`
- `omniretarget.config_types.data_type`

**Phase tasks:**

- [x] Add parity tests for every current `RobotConfig` robot type:
  - `g1`
  - `t1`
  - `adam_pro`

- [x] Add parity tests for every current motion format:
  - `lafan`
  - `smplh`
  - `smplx`
  - `mocap`
  - `optitrack`
  - `parc_humanoid`

- [x] Create `specs/robots.py` and move robot defaults and robot-specific profiles there.

- [x] Keep `RobotConfig` properties in `config_types/robot.py` as the caller-facing interface.

- [x] Create `specs/motion_formats.py` and move demo joint lists, toe names, and format constants there.

- [x] Create `specs/mappings.py` and move human-joint-to-robot-link mappings there.

- [x] Keep constants re-exported or otherwise available from `config_types/data_type.py` until all internal callers are migrated.

- [x] Update `docs/add-robot-type.md` and `docs/add-motion-format.md` to describe the new spec files.

**Focused checks:**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_adam_pro_robot_config.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_adam_pro_motion_mappings.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_foot_sticking_contact_keys.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_process.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_repo_doc_boundaries.py
```

**Phase exit criteria:**

- Extension docs point to the new spec registry files.
- Public config dataclasses still behave the same.
- Full tests pass.

**Phase stop conditions:**

- Moving specs forces CLI dataclass behavior changes.
- A spec registry cannot express an existing override without duplicating old logic.

---

## Phase 4: MuJoCo Query Seam

**Goal:** Concentrate MuJoCo model-state, qpos layout, link-position, Jacobian, and collision-query behavior in deeper modules.

**Problem being solved:** Retargeting and evaluation both know MuJoCo link lookup, dynamic object qpos layout, geometry filtering, and collision candidate rules. This duplicates sensitive behavior.

**Target modules:**

```text
src/omniretarget/mujoco/
  __init__.py
  model_state.py
  kinematics.py
  collision.py
  assets.py
```

**Compatibility requirement:**

`InteractionMeshRetargeter` and `RetargetingEvaluator` behavior must remain unchanged. Private methods may become wrappers during migration.

**Phase tasks:**

- [x] Add tests for qpos layout detection using existing small fixtures or model files.

- [x] Add tests for robot link position lookup with known link names.

- [x] Add tests for ground/object pair filtering rules used by non-penetration and evaluation.

- [x] Create `mujoco/assets.py` for robot XML selection:
  - ground
  - dynamic object
  - `multi_boxes`
  - PARC generated scene XML

- [x] Create `mujoco/model_state.py` to own MuJoCo model/data and dynamic-object detection.

- [x] Create `mujoco/kinematics.py` for link positions and point Jacobians.

- [x] Create `mujoco/collision.py` for collision candidate filtering and geometry distance queries.

- [x] First migrate `evaluation/eval_retargeting.py` to use the new query modules.

- [x] Then migrate `src/interaction_mesh_retargeter.py` private methods to wrappers around the new query modules.

- [x] Keep old private method names temporarily if tests or nearby code still call them.

**Focused checks:**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_eval_contact_joint_defaults.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_process.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_convert_data_format_parc_mj.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_adam_pro_largebox_scene_xml.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_adam_pro_xml_urdf_consistency.py
```

**Phase exit criteria:**

- MuJoCo qpos and geometry query knowledge is concentrated.
- Solver and evaluator no longer duplicate the same query rules.
- Full tests pass.

**Phase stop conditions:**

- Query extraction changes numerical outputs without an explicit reason.
- Dynamic object qpos layout becomes ambiguous.
- MuJoCo model ownership becomes shared in a way that introduces stale state.

**Verification note:** Phase 4 adds 7 MuJoCo seam tests. Focused Phase 4 gate:
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_mujoco_query_seam.py tests/test_eval_contact_joint_defaults.py tests/test_parc_process.py tests/test_convert_data_format_parc_mj.py tests/test_adam_pro_largebox_scene_xml.py tests/test_adam_pro_xml_urdf_consistency.py -q`
passed with 32 passed, 1 skipped. Full-suite count changes from 168 passed, 1 skipped to
180 passed, 1 skipped.

---

## Phase 5: Trajectory Solver Decomposition

**Goal:** Split `InteractionMeshRetargeter` into deeper solver modules while preserving its public behavior through a facade.

**Problem being solved:** `InteractionMeshRetargeter` currently combines model loading, visualization, interaction mesh construction, trajectory loop, one-frame problem assembly, constraints, optimizer invocation, and result writing.

**Target modules:**

```text
src/omniretarget/solver/
  __init__.py
  interaction_mesh.py
  trajectory.py
  frame_problem.py
  constraints.py
  optimizer.py

src/omniretarget/visualization/
  __init__.py
  viser_adapter.py
```

**Compatibility requirement:**

This import must keep working:

```python
from omniretarget.src.interaction_mesh_retargeter import InteractionMeshRetargeter
```

`InteractionMeshRetargeter` may become a facade, but it must continue to accept the same constructor arguments and expose the same methods used by current workflows.

**Phase tasks:**

- [ ] Add facade tests for `InteractionMeshRetargeter` public constructor and public methods currently used by workflows.

- [ ] Extract visualization-only code into `visualization/viser_adapter.py`.

- [ ] Keep visualization behavior behind the existing `visualize` and `debug` flags.

- [ ] Extract interaction mesh and Laplacian target construction into `solver/interaction_mesh.py`.

- [ ] Extract per-frame optimization input and output types into `solver/frame_problem.py`.

- [ ] Extract foot sticking, foot lock, non-penetration, self-collision, joint-limit, trust-region, nominal-tracking, and smoothness construction into `solver/constraints.py` only after query behavior is already behind Phase 4 modules.

- [ ] Extract CVXPY/Clarabel invocation into `solver/optimizer.py`.

- [ ] Extract the frame-by-frame loop into `solver/trajectory.py`.

- [ ] Keep `InteractionMeshRetargeter.retarget_motion()` as the facade method until all CLI and PARC workflows are verified.

**Focused checks:**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_process.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_adam_pro_object_interaction_mapping.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_foot_sticking_contact_keys.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_module_entrypoints.py
```

If a short demo input is available locally, also run one smoke workflow and verify output fields:

```bash
uv run python src/omniretarget/examples/robot_retarget.py \
  --robot adam_pro \
  --task-type robot_only \
  --task-name dance1_subject1 \
  --data-path src/omniretarget/demo_data/lafan1_npy \
  --data-format lafan \
  --save-dir /tmp/omniretarget_solver_smoke \
  --task-config.ground-range -15 15 \
  --retargeter.foot-sticking-tolerance 0.02
```

Expected output file:

```text
/tmp/omniretarget_solver_smoke/dance1_subject1.npz
```

Expected fields:

```text
qpos
human_joints
fps
cost
```

**Phase exit criteria:**

- `InteractionMeshRetargeter` is no longer a 1000+ line all-purpose implementation.
- Current public behavior remains available through the facade.
- Full tests pass.

**Phase stop conditions:**

- Decomposition requires changing solver math.
- Visualization extraction changes replay behavior.
- Retargeting outputs lose required fields.

---

## Phase 6: Cleanup and Import Migration

**Goal:** Remove compatibility wrappers that are no longer needed, update docs, and make the final module layout navigable.

**Allowed only after:**

- Phase 1 through Phase 5 are merged or stable on the refactor branch.
- Full tests pass.
- Public workflow behavior has been verified.

**Phase tasks:**

- [ ] Search for old compatibility wrapper usages.

```bash
rg "create_task_constants|omniretarget\\.src|examples\\.robot_retarget|examples\\.parallel_robot_retarget" src tests docs scripts
```

- [ ] Keep public import wrappers where external users may rely on them.

- [ ] Remove only internal wrappers that have no callers.

- [ ] Update README commands only if paths remain identical or wrappers are explicitly documented.

- [ ] Update `docs/add-robot-type.md` and `docs/add-motion-format.md` if Phase 3 changed extension paths.

- [ ] Update `CONTEXT.md` with any refined terms discovered during implementation.

- [ ] Update `docs/architecture-refactor-safety.md` if any safety gate changed during implementation.

**Focused checks:**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_module_entrypoints.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_repo_doc_boundaries.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

**Phase exit criteria:**

- Repository layout matches the final target or has documented deviations.
- Public entry points still work.
- Old internal pass-through wrappers are removed where safe.
- Full tests pass.

**Phase stop conditions:**

- Wrapper removal breaks an entry point or documented import path.
- Docs require users to change commands for no functional reason.

---

## Phase Dependency Graph

Run phases in this order:

```text
Phase 0 -> Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 -> Phase 5 -> Phase 6
```

Recommended first implementation round:

```text
Phase 1 only
```

Do not start Phase 2 until Phase 1 is reviewed, pushed, and stable.

Phase 4 must precede Phase 5 because solver decomposition depends on a stable MuJoCo query seam.

## Review Checklist for Every Phase

Before asking for review:

- [ ] Show changed files.

```bash
git diff --stat origin/main...HEAD
```

- [ ] Show phase-local commits.

```bash
git log --oneline origin/main..HEAD
```

- [ ] Run focused tests named in the phase.

- [ ] Run full tests.

- [ ] Confirm protected workflows were not intentionally changed.

- [ ] Record any known residual risk.

## Final Acceptance Criteria

The refactor is complete only when all are true:

- Protected workflows from current `main` still pass tests.
- CLI adapters remain stable.
- Runtime context behavior is centralized.
- Retargeting pipeline behavior is no longer owned by `examples`.
- Robot and motion specs have a deeper registry seam.
- MuJoCo query behavior is no longer duplicated between solver and evaluator.
- `InteractionMeshRetargeter` is reduced to a facade or a focused module.
- Documentation tells future contributors where to add robots, motion formats, and workflow-specific behavior.
- Full test suite passes from a clean worktree.
