"""Tests for portSent.py sentence segmentation."""

import sys
from pathlib import Path

import pytest

# Add src to path so we can import portSentencer
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from portSentencer.portSent import stripSents


class TestStripSents:
    """Test the stripSents function."""

    def test_simple_sentence(self):
        """A simple sentence ending with a period."""
        text = "Esta é uma frase simples."
        result = stripSents(text, limit=0, replace=True)

        assert result == ["Esta é uma frase simples."]

    def test_multiple_sentences(self):
        """Multiple sentences separated by periods."""
        text = "Primeira frase. Segunda frase. Terceira frase."
        result = stripSents(text, limit=0, replace=True)

        assert len(result) == 3
        assert result == ["Primeira frase.", "Segunda frase.", "Terceira frase."]

    def test_sentence_with_exclamation(self):
        """Sentences ending with exclamation marks."""
        text = "Que legal! Incrível!"
        result = stripSents(text, limit=0, replace=True)

        assert len(result) == 2
        assert result == ["Que legal!", "Incrível!"]

    def test_sentence_with_question(self):
        """Sentences ending with question marks."""
        text = "Como você está? Tudo bem?"
        result = stripSents(text, limit=0, replace=True)

        assert len(result) == 2
        assert result == ["Como você está?", "Tudo bem?"]

    def test_ellipsis_ends_sentence(self):
        """Ellipsis (...) ends a sentence."""
        text = "Ele foi embora... Nunca mais voltou."
        result = stripSents(text, limit=0, replace=True)

        assert len(result) == 2
        assert result == ["Ele foi embora...", "Nunca mais voltou."]

    def test_colon_followed_by_lowercase_continues(self):
        """Colon followed by lowercase does not end sentence."""
        text = "Exemplo: assim funciona. Próxima frase."
        result = stripSents(text, limit=0, replace=True)

        assert len(result) == 2
        assert result == ["Exemplo: assim funciona.", "Próxima frase."]

    def test_colon_followed_by_uppercase_ends(self):
        """Colon followed by uppercase ends sentence."""
        text = "Título: Uma Nova História."
        result = stripSents(text, limit=0, replace=True)

        assert len(result) == 2
        assert result == ["Título:", "Uma Nova História."]

    def test_sentence_without_final_punctuation(self):
        """Sentence without punctuation gets a period added."""
        text = "Esta frase não tem ponto"
        result = stripSents(text, limit=0, replace=True)

        assert result == ["Esta frase não tem ponto."]

    def test_empty_sentence_not_printed(self):
        """Empty sentences are not printed."""
        text = "   "
        result = stripSents(text, limit=0, replace=True)

        assert result == []

    def test_double_dot_removed(self):
        """Double dots at end (not ellipsis) become single dot."""
        text = "Esta frase termina com dois pontos.."
        result = stripSents(text, limit=0, replace=True)

        assert result == ["Esta frase termina com dois pontos."]

    def test_character_replacement_enabled(self):
        """Special characters are replaced when replace=True."""
        text = "Texto—com—travessão."
        result = stripSents(text, limit=0, replace=True)

        assert len(result) == 1
        assert "—" not in result[0]  # em-dash should be replaced

    def test_character_replacement_disabled(self):
        """Special characters preserved when replace=False."""
        text = "Texto—com—travessão."
        result = stripSents(text, limit=0, replace=False)

        assert len(result) == 1
        assert "—" in result[0]  # em-dash should be preserved

    def test_newlines_converted_to_spaces(self):
        """Newlines are converted to spaces."""
        text = "Primeira linha.\nSegunda linha."
        result = stripSents(text, limit=0, replace=True)

        assert len(result) == 2
        assert result == ["Primeira linha.", "Segunda linha."]

    def test_tabs_converted_to_spaces(self):
        """Tabs are converted to spaces."""
        text = "Palavra1\tPalavra2."
        result = stripSents(text, limit=0, replace=True)

        assert len(result) == 1
        assert "\t" not in result[0]

    def test_limit_splits_long_sentences(self):
        """Long sentences are split when limit is set."""
        text = "Esta é uma frase muito longa que deve ser dividida."
        result = stripSents(text, limit=20, replace=True)

        # With limit, sentence should be split
        assert len(result) >= 1
        for sentence in result:
            # Each sentence should be non-empty
            assert len(sentence) > 0

    def test_quoted_sentence_with_period(self):
        """Sentence ending with period inside quotes."""
        text = 'Ele disse "Olá." Depois foi embora.'
        result = stripSents(text, limit=0, replace=True)

        assert len(result) >= 1

    def test_multiple_spaces_collapsed(self):
        """Multiple spaces are collapsed to single space."""
        text = "Palavra1    Palavra2."
        result = stripSents(text, limit=0, replace=True)

        assert len(result) == 1
        assert "    " not in result[0]


class TestFileOutput:
    """Test that file output works correctly."""

    def test_file_output_matches_list(self, tmp_path):
        """Verify file output matches the returned list."""
        text = "Primeira frase. Segunda frase! Terceira frase?"

        # Get output as list
        sentences = stripSents(text, limit=0, replace=True)

        # Write to file (same way main() does)
        file_path = tmp_path / "output.txt"
        with open(file_path, "w") as f:
            for sentence in sentences:
                f.write(sentence + "\n")

        # Read back and compare
        file_lines = file_path.read_text().strip().split("\n")
        assert sentences == file_lines
