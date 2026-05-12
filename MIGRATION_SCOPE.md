# OmniRetarget Migration Scope

Included:
- Python package from `src/omniretarget/`
- Retargeting shell entrypoints
- Required models and demo assets referenced by retargeting code/tests
- Retargeting tests
- uv-based project metadata and lockfile

Excluded:
- `src/holosoma/`
- `src/holosoma_inference/`
- conda-based `setup_retargeting.sh` / `source_retargeting_setup.sh`
- whole-body-tracking demo scripts that call training code
- monorepo Docker integration unless required to run retargeting itself
