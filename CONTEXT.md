# OmniRetarget Context

This file records the domain vocabulary used during architecture reviews and
refactors. It is intentionally small: names here should describe stable concepts
that existing workflows already rely on.

## Domain Terms

**Retargeting Pipeline**
The workflow that turns a source human motion sequence, task settings, robot
settings, object or terrain assets, and retargeter settings into an OmniRetarget
trajectory output. Current entry points include single clip retargeting, parallel
retargeting, and PARC retargeting.

**Runtime Context**
The resolved execution facts shared by retargeting, evaluation, conversion, and
visualization workflows. It includes robot constants, motion format constants,
task object settings, asset paths, scene XML paths, joint mappings, foot contact
names, manual joint limits, and nominal tracking indices.

**Motion Source**
The source data format and loader used to produce human joint trajectories,
object poses, frame rate assumptions, and scale factors. Current motion sources
include LAFAN, SMPL-H, SMPL-X, MOCAP, OptiTrack, and PARC humanoid samples.

**Object Setup**
The workflow that prepares ground points, object mesh samples, climbing terrain
assets, scaled URDF/XML files, and scene XML files before retargeting starts.

**PARC Workflow**
The set of PARC terrain-motion workflows currently supported by the repository:
workspace generation, G1 retargeting, paired output writing, PARC to MJ
conversion, batch processing, and batch visualization.

**Height Origin**
The convention that determines how human joints, terrain heightfields, terrain
visuals, collision manifests, paired outputs, and MJ exports share the same
vertical origin. PARC height-origin behavior is a protected compatibility area.

**MuJoCo Query**
The operations that read MuJoCo model state for link positions, Jacobians,
collision candidates, geometry distances, and qpos layout decisions.

**Trajectory Solver**
The frame-by-frame optimization workflow that builds interaction meshes,
Laplacian targets, constraints, and CVXPY problems to solve robot trajectories.

**CLI Adapter**
A thin executable entry point that parses command-line configuration and calls a
deeper module. CLI adapters should not own retargeting, runtime-context, solver,
or asset-resolution behavior.

## Refactor Rule

Architecture refactors must preserve the behavior of every workflow supported by
the current `main` branch. A structural change is not complete unless it keeps
the existing workflow behavior, output schemas, asset path assumptions, and test
coverage aligned with `main`.
