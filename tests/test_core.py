"""Integration tests for portparser_v2 core pipeline."""

import sys
from pathlib import Path
from tempfile import mkdtemp

import pytest

# Add src to path so we can import portparser_v2
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from portparser_v2.core import parse_file, download_model

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "portparser_v2"


@pytest.fixture(scope="module")
def model_path():
    """Download and cache model for tests."""
    try:
        return download_model()
    except Exception as e:
        pytest.skip(f"Could not download model: {e}")


class TestIntegrationAlienista:
    """Integration test using alienista.txt fixture (O Alienista by Machado de Assis).
    
    This test runs the full pipeline:
    1. Sentence segmentation
    2. Tokenization
    3. Parsing (ML model)
    4. Post-processing
    
    Note: This test is slow as it requires downloading the model and running inference.
    """

    @pytest.fixture
    def input_file(self) -> Path:
        """Path to input text file."""
        return FIXTURES_DIR / "alienista.txt"

    @pytest.fixture
    def expected_output(self) -> str:
        """Load expected CoNLL-U output from fixture file."""
        expected_file = FIXTURES_DIR / "alienista.conllu"
        with open(expected_file, "r", encoding="utf-8") as f:
            return f.read()

    @pytest.mark.slow
    def test_full_pipeline_produces_valid_output(
        self, input_file: Path, expected_output: str, model_path: str
    ):
        """Verify full pipeline produces output matching expected CoNLL-U file."""
        work_dir = mkdtemp()
        output_path = Path(work_dir) / "alienista_output.conllu"

        # Run the full pipeline
        result_path = parse_file(
            input_path=str(input_file),
            output_path=str(output_path),
            work_dir=work_dir,
            model_path=model_path,
            segment_sentences=True,
        )

        # Read actual output
        with open(result_path, "r", encoding="utf-8") as f:
            actual_output = f.read()

        # Parse both outputs into sentences for comparison
        actual_sentences = self._parse_conllu_sentences(actual_output)
        expected_sentences = self._parse_conllu_sentences(expected_output)

        # Compare number of sentences
        assert len(actual_sentences) == len(expected_sentences), (
            f"Sentence count mismatch: got {len(actual_sentences)}, "
            f"expected {len(expected_sentences)}"
        )

        # Compare each sentence
        for i, (actual, expected) in enumerate(zip(actual_sentences, expected_sentences)):
            # Compare sentence IDs
            assert actual["sent_id"] == expected["sent_id"], (
                f"Sentence {i+1} ID mismatch: got {actual['sent_id']}, "
                f"expected {expected['sent_id']}"
            )
            
            # Compare sentence text
            assert actual["text"] == expected["text"], (
                f"Sentence {i+1} text mismatch:\n"
                f"  Actual: {actual['text']}\n"
                f"  Expected: {expected['text']}"
            )

            # Compare number of tokens (excluding multi-word tokens)
            actual_tokens = [t for t in actual["tokens"] if "-" not in t["id"]]
            expected_tokens = [t for t in expected["tokens"] if "-" not in t["id"]]
            assert len(actual_tokens) == len(expected_tokens), (
                f"Sentence {i+1} token count mismatch: got {len(actual_tokens)}, "
                f"expected {len(expected_tokens)}"
            )

            # Compare each token's form
            for j, (act_tok, exp_tok) in enumerate(zip(actual_tokens, expected_tokens)):
                assert act_tok["form"] == exp_tok["form"], (
                    f"Sentence {i+1}, token {j+1} form mismatch: "
                    f"got {act_tok['form']!r}, expected {exp_tok['form']!r}"
                )

    @pytest.mark.slow
    def test_sentence_count(self, input_file: Path, model_path: str):
        """Verify the number of sentences extracted matches expected."""
        work_dir = mkdtemp()
        output_path = Path(work_dir) / "alienista_output.conllu"

        result_path = parse_file(
            input_path=str(input_file),
            output_path=str(output_path),
            work_dir=work_dir,
            model_path=model_path,
            segment_sentences=True,
        )

        with open(result_path, "r", encoding="utf-8") as f:
            content = f.read()

        sentence_count = content.count("# sent_id = ")
        # The alienista.txt file should produce 49 sentences
        assert sentence_count == 49, f"Expected 49 sentences, got {sentence_count}"

    @staticmethod
    def _parse_conllu_sentences(conllu_content: str) -> list[dict]:
        """Parse CoNLL-U content into structured sentence data."""
        sentences = []
        current_sentence = None

        for line in conllu_content.strip().split("\n"):
            if line.startswith("# sent_id = "):
                if current_sentence is not None:
                    sentences.append(current_sentence)
                current_sentence = {
                    "sent_id": line.split("# sent_id = ")[1],
                    "text": "",
                    "tokens": [],
                }
            elif line.startswith("# text = ") and current_sentence is not None:
                current_sentence["text"] = line.split("# text = ")[1]
            elif line.startswith("#"):
                # Skip other comment lines
                continue
            elif line.strip() and current_sentence is not None:
                parts = line.split("\t")
                if len(parts) >= 10:
                    current_sentence["tokens"].append({
                        "id": parts[0],
                        "form": parts[1],
                        "lemma": parts[2],
                        "upos": parts[3],
                        "xpos": parts[4],
                        "feats": parts[5],
                        "head": parts[6],
                        "deprel": parts[7],
                        "deps": parts[8],
                        "misc": parts[9],
                    })

        if current_sentence is not None:
            sentences.append(current_sentence)

        return sentences


class TestParseFileOptions:
    """Test various options for parse_file function."""

    @pytest.mark.slow
    def test_without_sentence_segmentation(self, model_path: str):
        """Test parsing pre-segmented text (one sentence per line)."""
        # Create a simple pre-segmented input
        work_dir = mkdtemp()
        input_path = Path(work_dir) / "presegmented.txt"
        output_path = Path(work_dir) / "output.conllu"

        # Write pre-segmented sentences
        with open(input_path, "w", encoding="utf-8") as f:
            f.write("O gato dormiu.\n")
            f.write("O cachorro correu.\n")

        result_path = parse_file(
            input_path=str(input_path),
            output_path=str(output_path),
            work_dir=work_dir,
            model_path=model_path,
            segment_sentences=False,  # Don't segment - already done
        )

        with open(result_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should have exactly 2 sentences
        sentence_count = content.count("# sent_id = ")
        assert sentence_count == 2, f"Expected 2 sentences, got {sentence_count}"
