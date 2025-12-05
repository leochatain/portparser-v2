"""Integration tests for portparser_v2 core pipeline."""

import sys
from pathlib import Path
from tempfile import mkdtemp

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from portparser_v2.core import parse_file, download_model

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "portparser_v2"


@pytest.fixture(scope="module")
def model_path():
    """Download and cache model for tests."""
    try:
        return download_model()
    except Exception as e:
        pytest.skip(f"Could not download model: {e}")


@pytest.mark.slow
def test_parse_alienista(model_path: str):
    """Run full pipeline on alienista.txt and compare against expected output."""
    input_file = FIXTURES_DIR / "alienista.txt"
    expected_file = FIXTURES_DIR / "alienista.conllu"

    work_dir = mkdtemp()
    output_path = Path(work_dir) / "output.conllu"

    parse_file(
        input_path=str(input_file),
        output_path=str(output_path),
        work_dir=work_dir,
        model_path=model_path,
        segment_sentences=True,
    )

    actual = output_path.read_text(encoding="utf-8")
    expected = expected_file.read_text(encoding="utf-8")

    assert actual == expected
