# Asset Pruning Notes

## Current Size Snapshot

### Models

- `models/g1`: 135M
- `models/h1`: 121M
- `models/adam_pro`: 54M
- `models/t1`: 27M
- `models/largebox`: 2.0M
- `models/templates`: 8.0K

### Demo Data

- `demo_data/climb`: 8.3M
- `demo_data/custom_optitrack_npz`: 5.5M
- `demo_data/lafan1_npy`: 4.0M
- `demo_data/OMOMO_new`: 976K
- `demo_data/amass_npz`: 176K
- `demo_data/height_dict.pkl`: 4.0K

## Current Retention Decision

Decision: keep all bundled robot assets and demo datasets during bootstrap stabilization.

## Rationale

- The public config layer still exposes `g1`, `t1`, `adam_pro`, and `h1`
- Current tests and scripts actively exercise `adam_pro` and `g1`
- Removing `t1` or `h1` now would change the advertised compatibility surface before the standalone repository has stabilized
- Demo datasets are relatively small compared with robot mesh assets, so the main size pressure is in `models/`, not `demo_data/`

## First Pruning Candidates Later

If we choose to reduce repository size in a later approved pass, the first candidates should be:

- `models/h1`
- `models/t1`

That follow-up should only happen after:

- confirming no supported workflows depend on those assets
- narrowing the officially supported robot list
- rerunning the smoke suite after any deletion

## Status

No assets were deleted in this step.
