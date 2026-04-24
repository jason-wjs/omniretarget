# Utils-First Internal Split Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the moved `utils/` module into smaller responsibility-focused modules while keeping `solver/`, `pipelines/`, and legacy compatibility imports stable.

**Architecture:** After the `src -> solver/utils` move, the lowest-risk next step is to decompose `src/holosoma_retargeting/utils/utils.py` behind a compatibility facade. Keep `utils/utils.py` and `src/utils.py` importable during this phase, but move concrete function ownership into focused internal utility modules. Defer deletion of `holosoma_retargeting.src` and defer any deep split of `solver/interaction_mesh_retargeter.py` until the utility layer is stable.

**Tech Stack:** Python 3.11, uv, pytest, setuptools, numpy, torch, trimesh, scipy, mujoco, viser

---

### Task 1: Add failing structure and import-boundary tests for utility decomposition

**Files:**
- Create: `tests/test_utils_module_boundaries.py`
- Modify: `tests/test_module_entrypoints.py`

**Step 1: Write failing tests for the new utility modules**

Create `tests/test_utils_module_boundaries.py` with assertions that the following modules exist and import cleanly:

- `holosoma_retargeting.utils.motion_io`
- `holosoma_retargeting.utils.motion_preprocessing`
- `holosoma_retargeting.utils.object_mesh`
- `holosoma_retargeting.utils.scene_assets`
- `holosoma_retargeting.utils.transforms`
- `holosoma_retargeting.utils.contact`

Also assert that `holosoma_retargeting.utils.utils` still exports representative legacy functions such as:

- `load_intermimic_data`
- `preprocess_motion_data`
- `load_object_data`
- `create_new_scene_xml_file`
- `transform_points_world_to_local`
- `extract_foot_sticking_sequence_velocity`

**Step 2: Extend module import coverage**

Add import cases to `tests/test_module_entrypoints.py` for the six new utility modules.

**Step 3: Run tests to verify they fail**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q \
  tests/test_utils_module_boundaries.py \
  tests/test_module_entrypoints.py
```

Expected:

- `ModuleNotFoundError` for the new utility modules
- `utils.utils` compatibility assertions still pass for the existing file

### Task 2: Create focused utility modules without changing behavior

**Files:**
- Create: `src/holosoma_retargeting/utils/motion_io.py`
- Create: `src/holosoma_retargeting/utils/motion_preprocessing.py`
- Create: `src/holosoma_retargeting/utils/object_mesh.py`
- Create: `src/holosoma_retargeting/utils/scene_assets.py`
- Create: `src/holosoma_retargeting/utils/transforms.py`
- Create: `src/holosoma_retargeting/utils/contact.py`
- Modify: `src/holosoma_retargeting/utils/__init__.py`

**Step 1: Create the module skeletons**

Create the new modules with only the minimum imports and functions moved out of `utils/utils.py`.

Initial ownership should be conservative:

- `motion_io.py`
  - `load_intermimic_data`
- `motion_preprocessing.py`
  - `calculate_scale_factor`
  - `transform_y_up_to_z_up`
  - `preprocess_motion_data`
- `object_mesh.py`
  - `load_object_data`
  - sampling helpers used only by object loading
- `scene_assets.py`
  - `create_scaled_multi_boxes_urdf`
  - `create_scaled_multi_boxes_xml`
  - `create_new_scene_xml_file`
- `transforms.py`
  - `transform_points_local_to_world`
  - `transform_points_world_to_local`
  - pose/rotation conversion helpers
- `contact.py`
  - `extract_foot_sticking_sequence_velocity`

**Step 2: Keep `utils/__init__.py` minimal**

Only add a package docstring in `utils/__init__.py`. Do not turn it into a wildcard export hub.

### Task 3: Turn `utils/utils.py` into a compatibility facade

**Files:**
- Modify: `src/holosoma_retargeting/utils/utils.py`

**Step 1: Replace moved implementations with re-exports**

Edit `src/holosoma_retargeting/utils/utils.py` so it imports and re-exports the moved functions from the new focused modules.

Keep any functions that were not moved yet in place. This file remains the temporary facade for:

- existing callers in `pipelines/`, `evaluation/`, and tests
- `src/holosoma_retargeting/src/utils.py` compatibility wrapper

**Step 2: Do not rename public symbols**

Keep symbol names unchanged in this phase. No API redesign.

### Task 4: Update production imports away from the utility facade where safe

**Files:**
- Modify: `src/holosoma_retargeting/pipelines/motion_loading.py`
- Modify: `src/holosoma_retargeting/pipelines/object_setup.py`
- Modify: `src/holosoma_retargeting/pipelines/parallel.py`
- Modify: `src/holosoma_retargeting/pipelines/retarget.py`
- Modify: `src/holosoma_retargeting/evaluation/eval_retargeting.py`
- Modify: `src/holosoma_retargeting/solver/interaction_mesh_retargeter.py`

**Step 1: Move only obvious direct imports**

Change imports from `holosoma_retargeting.utils.utils` to focused modules where the ownership is unambiguous. Examples:

- motion loading code -> `motion_io`, `motion_preprocessing`
- object setup code -> `object_mesh`, `scene_assets`, `transforms`
- contact extraction -> `contact`

Do not force every import to move if it creates churn. This phase is about reducing the facade dependency, not eliminating it completely.

**Step 2: Keep runtime behavior unchanged**

No call signature changes.

### Task 5: Verify compatibility stays green

**Files:**
- Review only

**Step 1: Run focused utility tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q \
  tests/test_utils_module_boundaries.py \
  tests/test_module_entrypoints.py \
  tests/test_package_paths.py \
  tests/test_optitrack_grounding_preprocess.py \
  tests/test_foot_sticking_contact_keys.py
```

Expected: PASS

**Step 2: Run smoke suite**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache bash scripts/test_smoke.sh
```

Expected: PASS

**Step 3: Run build verification**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv build
```

Expected: PASS

### Task 6: Explicitly defer the next two risky changes

**Files:**
- No code changes

**Step 1: Defer solver decomposition**

Do not split `src/holosoma_retargeting/solver/interaction_mesh_retargeter.py` in this phase. That becomes the next phase after utility ownership is clearer.

**Step 2: Defer `src/` deletion**

Do not remove `src/holosoma_retargeting/src/` in this phase. Keep it until:

- tests stop importing `holosoma_retargeting.src.*`
- docs stop mentioning it
- solver and utility boundaries have stabilized
