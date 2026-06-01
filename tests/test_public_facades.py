from __future__ import annotations


def test_public_retargeter_facade_uses_domain_class() -> None:
    from omniretarget.retargeter import InteractionMeshRetargeter as PublicRetargeter
    from omniretarget.retargeting.interaction_mesh_retargeter import InteractionMeshRetargeter as DomainRetargeter

    assert PublicRetargeter is DomainRetargeter


def test_visualization_playback_helper_is_public() -> None:
    from omniretarget.visualization.playback import create_motion_control_sliders as PlaybackHelper

    assert callable(PlaybackHelper)
