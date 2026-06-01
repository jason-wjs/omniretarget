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
