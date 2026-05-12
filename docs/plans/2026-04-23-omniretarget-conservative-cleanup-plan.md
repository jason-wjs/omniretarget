# OmniRetarget Conservative Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Clean up repo/package boundaries in `omniretarget` without changing runtime behavior, public imports, or current shell entrypoints.

**Architecture:** Keep runtime code and assets where they are for now, but move repository-level documents out of the Python package, delete obvious residue, and narrow package-data inclusion so build artifacts contain only runtime-relevant resources. Treat this as a hygiene pass that prepares the repo for later structural refactors without introducing interface churn.

**Tech Stack:** Python 3.11, uv, setuptools, pytest, shell scripts, Markdown docs

---

### Task 1: Move repo-level docs out of the package tree

**Files:**
- Create: `docs/add-motion-format.md`
- Create: `docs/add-robot-type.md`
- Create: `docs/adam-pro-robot-only-summary.md`
- Modify: `src/omniretarget/README.md`
- Modify: `README.md`
- Delete: `src/omniretarget/ADD_MOTION_FORMAT_README.md`
- Delete: `src/omniretarget/ADD_ROBOT_TYPE_README.md`
- Delete: `src/omniretarget/ADAM_PRO_ROBOT_ONLY_SUMMARY.md`

**Step 1: Write a failing reference test**

Create `tests/test_repo_doc_boundaries.py`:

```python
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
```

**Step 2: Run the test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_repo_doc_boundaries.py -q
```

Expected: FAIL because the three markdown files still exist in `src/omniretarget/`.

**Step 3: Move the docs and update links**

- Copy the content of each package-root markdown file into its new `docs/` destination.
- Update `src/omniretarget/README.md` so it links to:
  - `../../docs/add-motion-format.md`
  - `../../docs/add-robot-type.md`
- Update root `README.md` if needed so it points to the new repo doc locations instead of package-root markdown files.
- Delete the three old package-root markdown files.

**Step 4: Re-run the test**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_repo_doc_boundaries.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add docs/add-motion-format.md docs/add-robot-type.md docs/adam-pro-robot-only-summary.md README.md src/omniretarget/README.md tests/test_repo_doc_boundaries.py
git commit -m "docs: move repo docs out of package root"
```

### Task 2: Remove obvious package residue

**Files:**
- Delete: `src/omniretarget/MUJOCO_LOG.TXT`
- Delete: `src/omniretarget/.gitignore`
- Modify: `tests/test_repo_doc_boundaries.py`

**Step 1: Extend the failing boundary test**

Add:

```python

def test_package_root_does_not_keep_residue_files() -> None:
    forbidden = [
        Path("src/omniretarget/MUJOCO_LOG.TXT"),
        Path("src/omniretarget/.gitignore"),
    ]
    for path in forbidden:
        assert not path.exists()
```

**Step 2: Run the test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_repo_doc_boundaries.py -q
```

Expected: FAIL because both files still exist.

**Step 3: Delete the residue files**

Delete:

- `src/omniretarget/MUJOCO_LOG.TXT`
- `src/omniretarget/.gitignore`

**Step 4: Re-run the test**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_repo_doc_boundaries.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_repo_doc_boundaries.py
git rm src/omniretarget/MUJOCO_LOG.TXT src/omniretarget/.gitignore
git commit -m "chore: remove package residue files"
```

### Task 3: Stop packaging repo docs in build artifacts

**Files:**
- Modify: `MANIFEST.in`
- Test: `tests/test_repo_doc_boundaries.py`

**Step 1: Write a failing packaging assertion**

Add:

```python

def test_manifest_does_not_package_markdown_docs() -> None:
    manifest = Path("MANIFEST.in").read_text()
    assert "recursive-include src/omniretarget *.md" not in manifest
```

**Step 2: Run the test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_repo_doc_boundaries.py -q
```

Expected: FAIL because `MANIFEST.in` still includes package markdown docs.

**Step 3: Tighten package data inclusion**

Update `MANIFEST.in` to keep only:

```text
recursive-include src/omniretarget/models *
recursive-include src/omniretarget/demo_data *
recursive-include src/omniretarget *.jinja
```

**Step 4: Re-run the test**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_repo_doc_boundaries.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add MANIFEST.in tests/test_repo_doc_boundaries.py
git commit -m "build: exclude repo docs from package artifacts"
```

### Task 4: Verify documentation links and builds remain healthy

**Files:**
- Review: `README.md`
- Review: `src/omniretarget/README.md`
- Review: `docs/add-motion-format.md`
- Review: `docs/add-robot-type.md`
- Review: `docs/adam-pro-robot-only-summary.md`

**Step 1: Check for broken references to the old package-root docs**

Run:

```bash
rg -n "ADD_MOTION_FORMAT_README|ADD_ROBOT_TYPE_README|ADAM_PRO_ROBOT_ONLY_SUMMARY" README.md docs src/omniretarget tests
```

Expected:
- matches only in updated link text or migration history if explicitly intended
- no stale references to deleted package-root markdown file paths

**Step 2: Run the conservative-cleanup focused test**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_repo_doc_boundaries.py -q
```

Expected: PASS

**Step 3: Run the smoke suite**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache bash scripts/test_smoke.sh
```

Expected: all checks pass

**Step 4: Run a build verification**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv build
```

Expected:
- build succeeds
- build logs no longer show package markdown docs being copied into `omniretarget/`

**Step 5: Commit**

```bash
git add README.md docs src/omniretarget/README.md tests/test_repo_doc_boundaries.py MANIFEST.in
git commit -m "test: verify conservative cleanup boundaries"
```
