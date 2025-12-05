# Portparser v2

A parsing model for Brazilian Portuguese following the [Universal Dependencies (UD)](https://universaldependencies.org/) framework.

> **Note:** This is a fork of the original [Portparser.v2 Hugging Face Space](https://huggingface.co/spaces/NILC-ICMC-USP/Portparser.v2) by NILC-ICMC-USP. The original project includes a Streamlit web interface (`app.py`) which is still present in this repository but is not required for using the parser programmatically.

## Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

### Optional dependencies

```bash
# For the Streamlit UI (not required for API usage)
uv pip install -e ".[ui]"

# For development/testing
uv pip install -e ".[dev]"
```

## Usage

### Quick Start

The simplest way to parse text:

```python
from portparser_v2 import parse

# Parse raw text (with automatic sentence segmentation)
conllu_output = parse("O Brasil é um país tropical. Ele fica na América do Sul.")
print(conllu_output)
```

### API Reference

#### `parse(text, segment=True) -> str`

Quick parse function that returns CoNLL-U content directly.

```python
from portparser_v2 import parse

# With sentence segmentation (default)
result = parse("O Brasil é um país tropical.")

# Without segmentation (assumes one sentence per line)
result = parse("Primeira frase.\nSegunda frase.", segment=False)
```

**Parameters:**
- `text`: Input text to parse
- `segment`: Whether to automatically segment sentences (default: `True`)

**Returns:** Parsed CoNLL-U content as a string.

---

#### `parse_text(text, output_path=None, work_dir=None, model_path=None, segment_sentences=False) -> str`

Full-featured parsing function with more control over the pipeline.

```python
from portparser_v2 import parse_text

# Basic usage
output_file = parse_text("O Brasil é um país tropical.", segment_sentences=True)

# With custom output path
output_file = parse_text(
    "O Brasil é um país tropical.",
    output_path="./output.conllu",
    work_dir="./temp",
    segment_sentences=True
)
```

**Parameters:**
- `text`: Input text to parse
- `output_path`: Optional path for final CoNLL-U output (uses temp file if `None`)
- `work_dir`: Optional working directory for temp files (creates temp dir if `None`)
- `model_path`: Optional path to model weights (downloads from HuggingFace if `None`)
- `segment_sentences`: If `True`, run sentence segmentation first; if `False`, assume one sentence per line

**Returns:** Path to the final parsed CoNLL-U file.

---

#### `parse_file(input_path, output_path=None, work_dir=None, model_path=None, segment_sentences=False) -> str`

Parse text from a file.

```python
from portparser_v2 import parse_file

# Parse a text file
output_file = parse_file(
    "input.txt",
    output_path="output.conllu",
    segment_sentences=True
)
```

**Parameters:** Same as `parse_text`, but with `input_path` instead of `text`.

**Returns:** Path to the final parsed CoNLL-U file.

## Pipeline

The parser runs a 4-step pipeline:

1. **Sentence Segmentation** (optional) - splits raw text into sentences
2. **Tokenization** - converts sentences to CoNLL-U format with tokens
3. **Parsing/Prediction** - runs the LatinPipe neural model to predict POS tags, morphological features, lemmas, and dependency relations
4. **Post-processing** - applies cleanup and corrections to the output

## Model

The model weights are automatically downloaded from HuggingFace on first use:
- Repository: [`lucelene/Portparser.v2-latinpipe-core`](https://huggingface.co/lucelene/Portparser.v2-latinpipe-core)

## License

See [LICENSE](LICENSE) for details.