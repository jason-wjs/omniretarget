from pathlib import Path


PACKAGE_ROOT = Path("src/holosoma_retargeting")
LEGACY_SRC_PACKAGE = "holosoma_retargeting.src"
LEGACY_SRC_BOUNDARY_MESSAGE = (
    "Compatibility-removal phase contract: production modules must not import "
    "holosoma_retargeting.src.*; tests may still do so temporarily until the "
    "compatibility wrappers are deleted."
)


def _python_sources_under(*parts: str) -> list[Path]:
    return sorted((PACKAGE_ROOT.joinpath(*parts)).glob("*.py"))


def test_parallel_pipeline_does_not_import_examples_modules() -> None:
    source = (PACKAGE_ROOT / "pipelines" / "parallel.py").read_text()
    assert "holosoma_retargeting.examples" not in source


def test_pipeline_modules_do_not_import_historical_src_package() -> None:
    offenders = []
    for path in _python_sources_under("pipelines"):
        source = path.read_text()
        if LEGACY_SRC_PACKAGE in source:
            offenders.append(str(path))
    assert offenders == [], f"{LEGACY_SRC_BOUNDARY_MESSAGE} Offenders: {offenders}"


def test_domain_entrypoints_do_not_import_historical_src_package() -> None:
    # This boundary is intentionally scoped to production modules. Test code may still
    # import the legacy compatibility package during the removal phase.
    checked = [
        PACKAGE_ROOT / "viser_player.py",
        PACKAGE_ROOT / "data_conversion" / "convert_data_format_mj.py",
        PACKAGE_ROOT / "evaluation" / "eval_retargeting.py",
    ]
    offenders = [str(path) for path in checked if LEGACY_SRC_PACKAGE in path.read_text()]
    assert offenders == [], f"{LEGACY_SRC_BOUNDARY_MESSAGE} Offenders: {offenders}"
