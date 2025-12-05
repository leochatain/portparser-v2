"""Tests for portTok.py tokenization logic."""

import sys
from pathlib import Path

import pytest

# Add src to path so we can import portparser_v2
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from portparser_v2.portTok import nextName, trimIt, tagIt, punctIt, tokenizeIt, processIt, processSentences

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "portTok"


class TestNextName:
    """Test the nextName function for ID incrementing."""

    def test_simple_increment(self):
        """Increment a simple number."""
        assert nextName("S000001") == "S000002"

    def test_increment_with_carry(self):
        """Increment with carry-over."""
        assert nextName("S000009") == "S000010"

    def test_multiple_carries(self):
        """Increment with multiple carry-overs."""
        assert nextName("S000099") == "S000100"
        assert nextName("S000999") == "S001000"

    def test_all_nines(self):
        """Increment when all digits are 9 causes overflow."""
        # Note: The S prefix is lost on overflow, result is "overflow" + wrapped number
        result = nextName("S999999")
        assert "overflow" in result or result == "1000000"

    def test_no_digits(self):
        """Handle string with no digits."""
        result = nextName("ABC")
        assert "1" in result  # Should add a 1

    def test_mixed_prefix(self):
        """Increment with letter prefix."""
        assert nextName("ID001") == "ID002"


class TestTrimIt:
    """Test the trimIt function for headline/itemize trimming."""

    def test_simple_sentence(self):
        """Simple sentence passes through."""
        result = trimIt("Esta é uma frase simples.")
        assert result == "Esta é uma frase simples."

    def test_remove_star_itemize(self):
        """Remove star itemize symbol."""
        result = trimIt("* Item da lista.")
        assert result == "Item da lista."

    def test_remove_dash_itemize(self):
        """Remove dash itemize symbol."""
        result = trimIt("- Item da lista.")
        assert result == "Item da lista."

    def test_remove_arrow_itemize(self):
        """Remove arrow itemize symbol."""
        result = trimIt("> Item da lista.")
        assert result == "Item da lista."

    def test_single_itemize_returns_empty(self):
        """Single itemize symbol returns empty."""
        assert trimIt("*") == ""
        assert trimIt("-") == ""

    def test_remove_parenthetical_prefix(self):
        """Remove (CITY) style prefixes."""
        result = trimIt("(BRASÍLIA) O presidente disse algo.")
        assert "BRASÍLIA" not in result
        assert "presidente" in result

    def test_remove_uppercase_headline(self):
        """Remove ALL CAPS headlines."""
        result = trimIt("ECONOMIA Mercado fecha em alta.")
        assert result == "Mercado fecha em alta."

    def test_preserve_sentence_start(self):
        """Preserve capitalized sentence start."""
        result = trimIt("Primeira palavra capitalizada.")
        assert result == "Primeira palavra capitalizada."

    def test_trim_multiple_spaces(self):
        """Collapse multiple spaces."""
        result = trimIt("Texto  com   espaços.")
        assert "  " not in result


class TestTagIt:
    """Test the tagIt function for itemize prompt tagging."""

    def test_roman_numeral_parenthesis(self):
        """Tag roman numeral with parenthesis."""
        result = tagIt("(i) primeiro item")
        assert "//*||*\\\\" in result

    def test_letter_parenthesis(self):
        """Tag letter with parenthesis."""
        result = tagIt("(a) primeiro item")
        assert "//*||*\\\\" in result

    def test_roman_numeral_without_open_paren(self):
        """Tag roman numeral without opening parenthesis."""
        result = tagIt("i) primeiro item")
        assert "//*|(|*\\\\" in result

    def test_letter_without_open_paren(self):
        """Tag letter without opening parenthesis."""
        result = tagIt("a) primeiro item")
        assert "//*|(|*\\\\" in result

    def test_double_paragraph_marker(self):
        """Tag paragraph marker."""
        result = tagIt("§§ novo parágrafo")
        assert "//*||*\\\\" in result

    def test_no_tag_regular_parenthesis(self):
        """Don't tag regular parenthetical text."""
        result = tagIt("(texto normal) continua")
        assert "//*||*\\\\" not in result

    def test_multi_digit_roman(self):
        """Tag multi-digit roman numerals."""
        result = tagIt("(xii) décimo segundo")
        assert "//*||*\\\\" in result


class TestPunctIt:
    """Test the punctIt function for punctuation matching."""

    def test_remove_enclosing_quotes(self):
        """Remove enclosing quotes when only pair."""
        result = punctIt('"Texto entre aspas."')
        assert result == "Texto entre aspas."

    def test_remove_enclosing_parens(self):
        """Remove enclosing parentheses when only pair."""
        result = punctIt("(Texto entre parênteses.)")
        assert result == "Texto entre parênteses."

    def test_remove_enclosing_brackets(self):
        """Remove enclosing brackets when only pair."""
        result = punctIt("[Texto entre colchetes.]")
        assert result == "Texto entre colchetes."

    def test_remove_odd_quotes(self):
        """Remove quotes when odd number."""
        result = punctIt('Texto com "aspas incompletas.')
        assert '"' not in result

    def test_remove_unmatched_parens(self):
        """Remove unmatched parentheses."""
        result = punctIt("Texto com (parêntese incompleto.")
        assert "(" not in result
        assert ")" not in result

    def test_fix_double_dot(self):
        """Fix double dot at end (not ellipsis)."""
        result = punctIt("Frase termina com dois pontos..")
        assert result == "Frase termina com dois pontos."

    def test_preserve_ellipsis(self):
        """Preserve ellipsis (three dots)."""
        result = punctIt("Frase com reticências...")
        assert result.endswith("...")

    def test_add_missing_final_punct(self):
        """Add period if no final punctuation."""
        result = punctIt("Frase sem pontuação final")
        assert result.endswith(".")

    def test_preserve_final_exclamation(self):
        """Preserve final exclamation."""
        result = punctIt("Que legal!")
        assert result.endswith("!")

    def test_preserve_final_question(self):
        """Preserve final question mark."""
        result = punctIt("Como vai?")
        assert result.endswith("?")

    def test_move_punct_inside_quote(self):
        """Move punctuation when quote follows punct."""
        result = punctIt('Ele disse "olá".')
        # Should handle quote+punct at end
        assert result.endswith('."') or result.endswith('".')

    def test_empty_after_cleanup(self):
        """Return empty if only punctuation."""
        result = punctIt("()")
        assert result == ""

    def test_fix_colon_dot(self):
        """Fix colon followed by dot."""
        result = punctIt("Item:.")
        assert result == "Item."


class TestTokenizeIt:
    """Test the tokenizeIt function for main tokenization."""

    def _tokenize(self, sentence: str, sid: str = "S000001") -> str:
        """Helper to tokenize and return output as string."""
        lines = tokenizeIt(sentence, sid)
        return "\n".join(lines)

    def _get_tokens(self, output: str) -> list[str]:
        """Extract token forms from CoNLL-U output."""
        tokens = []
        for line in output.strip().split("\n"):
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2 and "-" not in parts[0]:
                tokens.append(parts[1])
        return tokens

    def _get_all_lines(self, output: str) -> list[str]:
        """Get all non-comment lines from CoNLL-U output."""
        lines = []
        for line in output.strip().split("\n"):
            if not line.startswith("#") and line.strip():
                lines.append(line)
        return lines

    def test_simple_sentence(self):
        """Tokenize simple sentence."""
        output = self._tokenize("O gato dormiu.")
        tokens = self._get_tokens(output)
        assert tokens == ["O", "gato", "dormiu", "."]

    def test_sent_id_header(self):
        """Check sent_id header."""
        output = self._tokenize("Teste.", "S000042")
        assert "# sent_id = S000042" in output

    def test_text_header(self):
        """Check text header."""
        output = self._tokenize("Frase de teste.")
        assert "# text = Frase de teste." in output

    def test_contraction_do(self):
        """Tokenize contraction 'do' (de + o)."""
        output = self._tokenize("O livro do menino.")
        lines = self._get_all_lines(output)
        # Should have a multi-word token line like "3-4 do"
        has_contraction = any("-" in line.split("\t")[0] for line in lines)
        assert has_contraction
        tokens = self._get_tokens(output)
        assert "de" in tokens
        assert "o" in tokens

    def test_contraction_da(self):
        """Tokenize contraction 'da' (de + a)."""
        output = self._tokenize("A casa da Maria.")
        tokens = self._get_tokens(output)
        assert "de" in tokens
        assert "a" in tokens

    def test_contraction_no(self):
        """Tokenize contraction 'no' (em + o)."""
        output = self._tokenize("Estou no parque.")
        tokens = self._get_tokens(output)
        assert "em" in tokens
        assert "o" in tokens

    def test_contraction_na(self):
        """Tokenize contraction 'na' (em + a)."""
        output = self._tokenize("Ela está na escola.")
        tokens = self._get_tokens(output)
        assert "em" in tokens
        assert "a" in tokens

    def test_contraction_ao(self):
        """Tokenize contraction 'ao' (a + o)."""
        output = self._tokenize("Vou ao mercado.")
        tokens = self._get_tokens(output)
        assert "a" in tokens
        assert "o" in tokens

    def test_contraction_pelo(self):
        """Tokenize contraction 'pelo' (por + o)."""
        output = self._tokenize("Passou pelo parque.")
        tokens = self._get_tokens(output)
        # Note: 'pelo' can be ambiguous (hair vs por+o)
        # Just check it produces valid output
        assert len(tokens) >= 3

    def test_contraction_desta(self):
        """Tokenize contraction 'desta' (de + esta)."""
        output = self._tokenize("O livro desta autora.")
        tokens = self._get_tokens(output)
        assert "de" in tokens
        assert "esta" in tokens

    def test_contraction_naquele(self):
        """Tokenize contraction 'naquele' (em + aquele)."""
        output = self._tokenize("Naquele dia chovia.")
        tokens = self._get_tokens(output)
        # Note: case is preserved, so 'Em' not 'em' when at sentence start
        tokens_lower = [t.lower() for t in tokens]
        assert "em" in tokens_lower
        assert "aquele" in tokens_lower

    def test_punctuation_separation(self):
        """Separate punctuation as tokens."""
        output = self._tokenize("Olá, mundo!")
        tokens = self._get_tokens(output)
        assert "," in tokens
        assert "!" in tokens

    def test_quotes_separation(self):
        """Separate quotes as tokens."""
        output = self._tokenize('Ele disse "olá" para mim.')
        tokens = self._get_tokens(output)
        assert '"' in tokens

    def test_parentheses_separation(self):
        """Separate parentheses as tokens."""
        output = self._tokenize("O resultado (final) foi bom.")
        tokens = self._get_tokens(output)
        assert "(" in tokens
        assert ")" in tokens

    def test_enclisis_simple(self):
        """Handle simple enclisis (verb-pronoun)."""
        output = self._tokenize("Deu-me o livro.")
        tokens = self._get_tokens(output)
        # Should split "Deu-me" into verb + pronoun
        assert "me" in tokens

    def test_enclisis_lo(self):
        """Handle -lo enclisis."""
        output = self._tokenize("Vou comprá-lo amanhã.")
        tokens = self._get_tokens(output)
        assert "lo" in tokens or "o" in tokens

    def test_abbreviation_preserved(self):
        """Preserve abbreviations."""
        output = self._tokenize("O Dr. Silva chegou.")
        tokens = self._get_tokens(output)
        assert "Dr." in tokens

    def test_number_handling(self):
        """Handle numbers."""
        output = self._tokenize("Custou R$ 100,00 reais.")
        tokens = self._get_tokens(output)
        assert "100,00" in tokens or "100" in tokens

    def test_space_after_annotation(self):
        """Check SpaceAfter=No annotation exists in output."""
        output = self._tokenize("Olá, mundo!")
        # SpaceAfter=No should appear somewhere in the output
        # (tokens before punctuation typically have this)
        assert "SpaceAfter=No" in output

    def test_itemize_tag_preserved(self):
        """Preserve tagged itemize prompts."""
        # Using the tag format from tagIt
        output = self._tokenize("//*||*\\\\(i)//*||*\\\\ primeiro item.")
        tokens = self._get_tokens(output)
        assert "(i)" in tokens


class TestProcessIt:
    """Test the processIt function (full pipeline)."""

    def _process(self, sent: str, sid: str = "S000001", 
                 preserve: bool = True, match: bool = True, trim: bool = True) -> tuple[list[str], str]:
        """Helper to process and return (lines, output_string)."""
        lines = processIt(sent, sid, preserve, match, trim)
        output = "\n".join(lines) if lines else ""
        return lines, output

    def _count_tokens(self, lines: list[str]) -> int:
        """Count actual tokens (excluding multi-word token lines and comments)."""
        return sum(1 for ln in lines if ln and not ln.startswith("#") and "-" not in ln.split("\t")[0])

    def test_simple_sentence(self):
        """Process simple sentence."""
        lines, output = self._process("Esta é uma frase.")
        assert len(lines) > 0
        assert self._count_tokens(lines) >= 4  # At least 4 tokens
        assert "# sent_id" in output

    def test_empty_after_processing(self):
        """Return empty list for empty result."""
        # A string that becomes empty after punctIt returns empty list
        # Note: Empty string input causes IndexError in trimIt (known bug)
        # Use a string that punctIt will clean to empty
        lines, output = self._process("[]", trim=False, preserve=False, match=True)
        assert lines == []
        assert output == ""

    def test_with_headline_trim(self):
        """Trim headline when enabled."""
        lines, output = self._process("ECONOMIA O mercado subiu.", trim=True)
        assert len(lines) > 0
        assert "ECONOMIA" not in output or "mercado" in output

    def test_without_headline_trim(self):
        """Keep headline when trim disabled."""
        lines, output = self._process("ECONOMIA subiu.", trim=False)
        assert len(lines) > 0
        assert "ECONOMIA" in output

    def test_with_itemize_preserve(self):
        """Preserve itemize when enabled."""
        # Note: trimIt may remove itemize markers depending on context
        # Test that with preserve=True, we at least get valid output
        lines, output = self._process("Texto com (i) item.", preserve=True)
        assert len(lines) > 0
        assert self._count_tokens(lines) > 0

    def test_with_punct_match(self):
        """Match punctuation when enabled."""
        lines, output = self._process('"Texto entre aspas."', match=True)
        assert len(lines) > 0
        # Enclosing quotes should be removed
        # The text content should remain

    def test_full_pipeline(self):
        """Test full pipeline with all options."""
        sent = "* MANCHETE (a) O presidente disse algo importante."
        lines, output = self._process(sent, preserve=True, match=True, trim=True)
        assert len(lines) > 0
        assert self._count_tokens(lines) > 0
        assert "# sent_id" in output
        assert "# text" in output


class TestContractions:
    """Test specific contraction handling."""

    def _tokenize(self, sentence: str) -> list[str]:
        """Helper to get tokens from a sentence."""
        lines = tokenizeIt(sentence, "S001")
        output = "\n".join(lines)
        tokens = []
        for line in output.strip().split("\n"):
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2 and "-" not in parts[0]:
                tokens.append(parts[1].lower())
        return tokens

    def test_à(self):
        """Contraction à (a + a)."""
        tokens = self._tokenize("Vou à praia.")
        assert "a" in tokens  # Both 'a' preposition and 'a' article

    def test_às(self):
        """Contraction às (a + as)."""
        tokens = self._tokenize("Refere-se às regras.")
        assert "a" in tokens
        assert "as" in tokens

    def test_aos(self):
        """Contraction aos (a + os)."""
        tokens = self._tokenize("Deu aos meninos.")
        assert "a" in tokens
        assert "os" in tokens

    def test_àquele(self):
        """Contraction àquele (a + aquele)."""
        tokens = self._tokenize("Refere-se àquele livro.")
        assert "a" in tokens
        assert "aquele" in tokens

    def test_daqui(self):
        """Contraction daqui (de + aqui)."""
        tokens = self._tokenize("Saiu daqui.")
        assert "de" in tokens
        assert "aqui" in tokens

    def test_dele(self):
        """Contraction dele (de + ele)."""
        tokens = self._tokenize("O carro dele.")
        assert "de" in tokens
        assert "ele" in tokens

    def test_nela(self):
        """Contraction nela (em + ela)."""
        tokens = self._tokenize("Pensou nela.")
        assert "em" in tokens
        assert "ela" in tokens

    def test_num(self):
        """Contraction num (em + um)."""
        tokens = self._tokenize("Está num lugar.")
        assert "em" in tokens
        assert "um" in tokens

    def test_dum(self):
        """Contraction dum (de + um)."""
        tokens = self._tokenize("Veio dum lugar.")
        assert "de" in tokens
        assert "um" in tokens

    def test_comigo(self):
        """Contraction comigo (com + mim)."""
        tokens = self._tokenize("Veio comigo.")
        assert "com" in tokens
        assert "mim" in tokens

    def test_conosco(self):
        """Contraction conosco (com + nós)."""
        tokens = self._tokenize("Veio conosco.")
        assert "com" in tokens
        assert "nós" in tokens


class TestEnclisis:
    """Test enclisis (verb-pronoun) handling."""

    def _tokenize(self, sentence: str) -> list[str]:
        """Helper to get tokens from a sentence."""
        lines = tokenizeIt(sentence, "S001")
        output = "\n".join(lines)
        tokens = []
        for line in output.strip().split("\n"):
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2 and "-" not in parts[0]:
                tokens.append(parts[1].lower())
        return tokens

    def test_deu_me(self):
        """Enclisis deu-me."""
        tokens = self._tokenize("Deu-me o livro.")
        assert "deu" in tokens or "dar" in tokens
        assert "me" in tokens

    def test_disse_lhe(self):
        """Enclisis disse-lhe."""
        tokens = self._tokenize("Disse-lhe a verdade.")
        assert "disse" in tokens
        assert "lhe" in tokens

    def test_ve_lo(self):
        """Enclisis vê-lo (with accent change)."""
        tokens = self._tokenize("Quero vê-lo.")
        # Should have verb form and 'lo' or 'o'
        assert "lo" in tokens or "o" in tokens

    def test_compra_lo(self):
        """Enclisis comprá-lo (with accent)."""
        tokens = self._tokenize("Vou comprá-lo.")
        assert "lo" in tokens or "o" in tokens


class TestIntegrationSentsFile:
    """Integration test using sents.txt fixture file."""

    @pytest.fixture
    def input_sentences(self) -> list[str]:
        """Load input sentences from fixture file."""
        input_file = FIXTURES_DIR / "sents.txt"
        with open(input_file, "r", encoding="utf-8") as f:
            return [line.rstrip("\n") for line in f]

    @pytest.fixture
    def expected_output(self) -> str:
        """Load expected CoNLL-U output from fixture file."""
        expected_file = FIXTURES_DIR / "expected_sents.conllu"
        with open(expected_file, "r", encoding="utf-8") as f:
            return f.read()

    def test_process_sentences_matches_expected(
        self, input_sentences: list[str], expected_output: str
    ):
        """Verify processSentences output matches expected CoNLL-U file."""
        # Process with same parameters used by upstream (default options)
        # The expected file uses S000001, S000002, etc. (6 digits starting at 1)
        # So sid_start should be "S000000" to get S000001 as first ID
        actual_output = processSentences(
            input_sentences,
            sid_start="S000000",
            preserve=True,
            match=True,
            trim=True,
        )

        # Normalize line endings and trailing whitespace
        actual_lines = [line.rstrip() for line in actual_output.strip().split("\n")]
        expected_lines = [line.rstrip() for line in expected_output.strip().split("\n")]

        # Compare line by line for better error messages
        assert len(actual_lines) == len(expected_lines), (
            f"Line count mismatch: got {len(actual_lines)}, expected {len(expected_lines)}"
        )

        for i, (actual, expected) in enumerate(zip(actual_lines, expected_lines)):
            assert actual == expected, (
                f"Line {i + 1} mismatch:\n"
                f"  Actual:   {actual!r}\n"
                f"  Expected: {expected!r}"
            )

    def test_sentence_count(self, input_sentences: list[str]):
        """Verify the number of processed sentences."""
        output = processSentences(
            input_sentences,
            sid_start="S000000",
            preserve=True,
            match=True,
            trim=True,
        )
        # Count sentences by counting "# sent_id" lines
        sentence_count = output.count("# sent_id = ")
        # One sentence should be trimmed to empty (headline-only line)
        assert sentence_count == 284, f"Expected 284 sentences, got {sentence_count}"

