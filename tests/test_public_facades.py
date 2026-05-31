from __future__ import annotations


def test_public_retargeter_facade_preserves_legacy_class_identity() -> None:
    from omniretarget.retargeter import InteractionMeshRetargeter as PublicRetargeter
    from omniretarget.src.interaction_mesh_retargeter import InteractionMeshRetargeter as LegacyRetargeter

    assert PublicRetargeter is LegacyRetargeter
