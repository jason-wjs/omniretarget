from holosoma_retargeting.retargeter import InteractionMeshRetargeter
from holosoma_retargeting.retargeter.retargeter import InteractionMeshRetargeter as CanonicalRetargeter


def test_retargeter_imports_from_canonical_package() -> None:
    assert InteractionMeshRetargeter is CanonicalRetargeter
