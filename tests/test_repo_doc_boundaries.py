from pathlib import Path


PACKAGE_ROOT = Path("src/omniretarget")


def test_repo_level_markdown_docs_are_not_stored_in_package_root() -> None:
    forbidden = [
        PACKAGE_ROOT / "ADD_MOTION_FORMAT_README.md",
        PACKAGE_ROOT / "ADD_ROBOT_TYPE_README.md",
        PACKAGE_ROOT / "ADAM_PRO_ROBOT_ONLY_SUMMARY.md",
    ]
    for path in forbidden:
        assert not path.exists()


def test_package_root_does_not_keep_residue_files() -> None:
    forbidden = [
        Path("src/omniretarget/README.md"),
        Path("src/omniretarget/MUJOCO_LOG.TXT"),
        Path("src/omniretarget/.gitignore"),
        Path("src/holosoma_retargeting"),
    ]
    for path in forbidden:
        assert not path.exists()


def test_manifest_does_not_package_markdown_docs() -> None:
    manifest = Path("MANIFEST.in").read_text()
    assert "recursive-include src/omniretarget *.md" not in manifest


def test_root_readme_is_the_only_readme_entrypoint() -> None:
    readme = Path("README.md").read_text()
    assert "src/omniretarget/README.md" not in readme


def test_production_code_does_not_import_legacy_utils_module() -> None:
    allowed_paths = {
        Path("src/omniretarget/src/utils.py"),
    }
    offenders = []
    for path in PACKAGE_ROOT.rglob("*.py"):
        if path in allowed_paths:
            continue
        text = path.read_text()
        if "omniretarget.src.utils" in text:
            offenders.append(path)

    assert offenders == []


def test_production_code_does_not_import_legacy_src_namespace() -> None:
    allowed_prefix = Path("src/omniretarget/src")
    offenders = []
    for path in PACKAGE_ROOT.rglob("*.py"):
        if path.is_relative_to(allowed_prefix):
            continue
        text = path.read_text()
        if "omniretarget.src." in text or "from omniretarget.src" in text:
            offenders.append(path)

    assert offenders == []
