# Migration Notes

OmniRetarget was extracted from Holosoma's retargeting component.

## Not Included

- Policy training
- Real-robot deployment
- Shared monorepo demo pipelines that launch non-retargeting jobs

## Current Migration Choices

- `holosoma/` stays read-only and acts as the blueprint
- `omniretarget/` is the only write target for ongoing work
- `uv` is the supported environment workflow
- The Python import path remains `holosoma_retargeting` during bootstrap stabilization
