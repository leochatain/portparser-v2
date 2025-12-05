"""
Portparser v2 Core Pipeline

This module provides the core parsing pipeline for Brazilian Portuguese text.
It orchestrates: sentencing → tokenization → prediction → postprocessing.

Each step reads from and writes to temporary files.
"""

import os
import datetime
import random
from pathlib import Path
from tempfile import mkdtemp
from typing import Optional

from huggingface_hub import hf_hub_download


# Default model repository
DEFAULT_MODEL_REPO = "lucelene/Portparser.v2-latinpipe-core"

# Paths relative to project root
SCRIPT_DIR = Path(__file__).parent.parent
SENTENCER_SCRIPT = SCRIPT_DIR / "portSentencer" / "portSent.py"
TOKENIZER_SCRIPT = SCRIPT_DIR / "portTokenizer" / "portTok.py"
PARSER_SCRIPT = SCRIPT_DIR / "evalatin2024-latinpipe" / "latinpipe_evalatin24.py"
POSTPROC_SCRIPT = SCRIPT_DIR / "postproc" / "postprocess.py"


def _generate_code() -> str:
    """Generate a unique code for file naming."""
    return (
        f'{datetime.datetime.now().strftime("%d%m%Y_%H%M%S%f")}_{random.randint(0, 9)}'
    )


def download_model(repo_id: str = DEFAULT_MODEL_REPO) -> str:
    model_weights = hf_hub_download(
        repo_id=repo_id, filename="model.weights.h5", repo_type="model"
    )
    # Also download required companion files
    hf_hub_download(repo_id=repo_id, filename="options.json", repo_type="model")
    hf_hub_download(repo_id=repo_id, filename="mappings.pkl", repo_type="model")

    return model_weights


def run_sentencer(input_path: str, output_path: str, max_length: int = 2048) -> int:
    cmd = f"python {SENTENCER_SCRIPT} -o {output_path} -r -l {max_length} {input_path}"
    return os.system(cmd)


def run_tokenizer(input_path: str, output_path: str, start_id: str = "S000000") -> int:
    cmd = f"python {TOKENIZER_SCRIPT} -o {output_path} -m -s {start_id} {input_path}"
    return os.system(cmd)


def run_parser(input_path: str, output_dir: str, model_path: str) -> int:
    cmd = f"python {PARSER_SCRIPT} --load {model_path} --exp {output_dir} --test {input_path}"
    return os.system(cmd)


def run_postprocessor(input_path: str, output_path: str) -> int:
    cmd = f"python {POSTPROC_SCRIPT} -o {output_path} {input_path}"
    return os.system(cmd)


def parse_text(
    text: str,
    output_path: Optional[str] = None,
    work_dir: Optional[str] = None,
    model_path: Optional[str] = None,
    segment_sentences: bool = False,
) -> str:
    """
    Parse Brazilian Portuguese text through the full pipeline.

    Args:
        text: Input text to parse
        output_path: Optional path for final CoNLL-U output. If None, uses temp file.
        work_dir: Optional working directory for temp files. If None, creates temp dir.
        model_path: Optional path to model weights. If None, downloads from HuggingFace.
        segment_sentences: If True, run sentencer first. If False, assume one sentence per line.

    Returns:
        Path to the final parsed CoNLL-U file
    """
    # Setup directories
    if work_dir is None:
        work_dir = mkdtemp()
    else:
        os.makedirs(work_dir, exist_ok=True)

    code = _generate_code()

    # Define file paths
    path_raw_text = os.path.join(work_dir, f"{code}_raw.txt")
    path_text = os.path.join(work_dir, f"{code}_input.txt")
    path_empty_conllu = os.path.join(work_dir, f"{code}_input.conllu")
    path_predicted_conllu = os.path.join(work_dir, f"{code}_input.predicted.conllu")
    path_final_conllu = output_path or os.path.join(work_dir, f"{code}_parsed.conllu")

    # Download model if needed
    if model_path is None:
        model_path = download_model()

    # Step 1: Sentence segmentation (optional)
    if segment_sentences:
        with open(path_raw_text, "w", encoding="utf-8") as f:
            f.write(text)
        run_sentencer(path_raw_text, path_text)
    else:
        with open(path_text, "w", encoding="utf-8") as f:
            f.write(text)

    # Step 2: Tokenization
    run_tokenizer(path_text, path_empty_conllu)

    # Step 3: Parsing/Prediction
    run_parser(path_empty_conllu, work_dir, model_path)

    # Step 4: Post-processing
    run_postprocessor(path_predicted_conllu, path_final_conllu)

    return path_final_conllu


def parse_file(
    input_path: str,
    output_path: Optional[str] = None,
    work_dir: Optional[str] = None,
    model_path: Optional[str] = None,
    segment_sentences: bool = False,
) -> str:
    """
    Parse Brazilian Portuguese text from a file through the full pipeline.

    Args:
        input_path: Path to input text file
        output_path: Optional path for final CoNLL-U output. If None, uses temp file.
        work_dir: Optional working directory for temp files. If None, creates temp dir.
        model_path: Optional path to model weights. If None, downloads from HuggingFace.
        segment_sentences: If True, run sentencer first. If False, assume one sentence per line.

    Returns:
        Path to the final parsed CoNLL-U file
    """
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    return parse_text(
        text=text,
        output_path=output_path,
        work_dir=work_dir,
        model_path=model_path,
        segment_sentences=segment_sentences,
    )


# Convenience function for quick parsing
def parse(text: str, segment: bool = True) -> str:
    """
    Quick parse function - returns the CoNLL-U content directly.

    Args:
        text: Input text to parse
        segment: Whether to segment sentences (default True for raw text)

    Returns:
        Parsed CoNLL-U content as string
    """
    output_path = parse_text(text, segment_sentences=segment)
    with open(output_path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    print("Enter text to parse:")
    text = input()
    print("Parsing...")
    print(parse(text, segment=True))
    print("Done!")