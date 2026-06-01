from __future__ import annotations


def test_public_retargeter_facade_preserves_legacy_class_identity() -> None:
    from omniretarget.retargeter import InteractionMeshRetargeter as PublicRetargeter
    from omniretarget.retargeting.interaction_mesh_retargeter import InteractionMeshRetargeter as DomainRetargeter
    from omniretarget.src.interaction_mesh_retargeter import InteractionMeshRetargeter as LegacyRetargeter

    assert PublicRetargeter is DomainRetargeter
    assert LegacyRetargeter is DomainRetargeter


def test_visualization_playback_facade_preserves_legacy_helper_identity() -> None:
    from omniretarget.src.viser_utils import create_motion_control_sliders as LegacyHelper
    from omniretarget.visualization.playback import create_motion_control_sliders as PlaybackHelper

    assert LegacyHelper is PlaybackHelper


def test_legacy_mujoco_utils_reexports_asset_helpers() -> None:
    from omniretarget.mujoco import assets
    from omniretarget.src import mujoco_utils

    assert mujoco_utils._mesh_local_vf is assets.mesh_local_vertices_and_faces
    assert mujoco_utils._to_world is assets.transform_mesh_vertices_to_world
    assert mujoco_utils._world_mesh_from_geom is assets.world_mesh_from_geom
