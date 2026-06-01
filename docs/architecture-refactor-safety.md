# Architecture Refactor Safety Checklist

This checklist is the safety contract for the architecture refactor on
`arch/retargeting-runtime-refactor`. It protects the current `main` behavior
while modules are deepened and moved behind clearer interfaces.

## Protected Workflows

Every refactor phase must preserve these workflows from the current `main`
branch:

1. Single retargeting via `src/omniretarget/examples/robot_retarget.py`
2. Parallel retargeting via `src/omniretarget/examples/parallel_robot_retarget.py`
3. PARC process via `src/omniretarget/examples/parc_process.py`
4. PARC batch to MJ via `src/omniretarget/examples/parc_batch_process_to_mj.py`
5. PARC batch visualization via `src/omniretarget/examples/parc_batch_vis.py`
6. Standard MJ conversion via `src/omniretarget/data_conversion/convert_data_format_mj.py`
7. PARC MJ conversion via `src/omniretarget/data_conversion/convert_data_format_parc_mj.py`
8. Viser replay via `src/omniretarget/viser_player.py`
9. Quantitative evaluation via `src/omniretarget/evaluation/eval_retargeting.py`
10. Robot and motion-format extension contracts in `docs/add-robot-type.md` and
    `docs/add-motion-format.md`
11. Model and asset path behavior, especially G1/PARC assets, scene XML files,
    terrain visual assets, terrain collision manifests, and height-origin rules

## Required Refactor Strategy

- Move one seam at a time.
- Add the new module first.
- Keep the old interface as a compatibility wrapper until parity is tested.
- Separate mechanical moves from behavior changes.
- Do not change CLI arguments, output `.npz` schema, manifest schema, or asset
  paths unless that behavior change is explicitly reviewed.
- Treat PARC height origin and batch visualization as high-risk compatibility
  areas because they are recently added main-branch behavior.
- Keep `omniretarget.src.*` imports and `src/omniretarget/viser_player.py` as
  compatibility paths unless a later reviewed phase proves external users no
  longer need them. Internal callers should prefer the deeper seams when they
  exist, such as `omniretarget.retargeter` and `omniretarget.mujoco.*`.

## Runtime Context Parity Fields

When introducing a runtime-context module, parity tests must compare the old and
new resolved values for these fields where they apply:

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

## Verification Gate

Run focused tests after each small change that touches a protected workflow:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_process.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_batch_vis.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_convert_data_format_parc_mj.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_module_entrypoints.py
```

Run the full suite at the end of each phase:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

## Stop Conditions

Stop the phase and reassess if any of these happen:

- A supported CLI needs argument changes.
- Existing output schema changes.
- Existing tests need broad rewrites to keep passing.
- A refactor requires simultaneous changes across single retargeting, parallel
  retargeting, PARC processing, evaluation, and conversion.
- `InteractionMeshRetargeter` public behavior must be broken to continue.
- PARC height-origin, terrain visual, terrain collision, or MJ export behavior
  becomes ambiguous.
