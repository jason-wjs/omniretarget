from pathlib import Path


def test_parallel_pipeline_does_not_import_examples_modules() -> None:
    source = Path("src/holosoma_retargeting/pipelines/parallel.py").read_text()
    assert "holosoma_retargeting.examples" not in source
