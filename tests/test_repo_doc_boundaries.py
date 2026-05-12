from pathlib import Path


PACKAGE_ROOT = Path("src/holosoma_retargeting")


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
        Path("src/holosoma_retargeting/README.md"),
        Path("src/holosoma_retargeting/MUJOCO_LOG.TXT"),
        Path("src/holosoma_retargeting/.gitignore"),
    ]
    for path in forbidden:
        assert not path.exists()


def test_manifest_does_not_package_markdown_docs() -> None:
    manifest = Path("MANIFEST.in").read_text()
    assert "recursive-include src/holosoma_retargeting *.md" not in manifest


def test_root_readme_is_the_only_readme_entrypoint() -> None:
    readme = Path("README.md").read_text()
    assert "src/holosoma_retargeting/README.md" not in readme
