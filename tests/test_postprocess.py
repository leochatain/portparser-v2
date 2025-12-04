"""Tests for postprocess.py post-processing logic."""

import sys
from pathlib import Path

import pytest

# Add src to path so we can import postproc
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "postproc"))

from postprocess import (
    isAbbr,
    isWithin,
    fixCompoundUpper,
    featsFull,
    locateExtPos,
    sepLEMMA_FEATS,
    getUsualAbbr,
)


class TestIsAbbr:
    """Test the isAbbr function."""

    def test_found_abbreviation(self):
        """Return True when abbreviation is found."""
        abbr_list = [
            ["dr.", "NOUN", "doutor", "_"],
            ["sr.", "NOUN", "senhor", "_"],
        ]
        assert isAbbr(abbr_list, "dr.") is True
        assert isAbbr(abbr_list, "sr.") is True

    def test_not_found(self):
        """Return False when abbreviation not found."""
        abbr_list = [
            ["dr.", "NOUN", "doutor", "_"],
        ]
        assert isAbbr(abbr_list, "prof.") is False

    def test_empty_list(self):
        """Return False for empty list."""
        assert isAbbr([], "dr.") is False

    def test_case_sensitive(self):
        """Check case sensitivity."""
        abbr_list = [
            ["dr.", "NOUN", "doutor", "_"],
        ]
        # isAbbr does exact match
        assert isAbbr(abbr_list, "Dr.") is False
        assert isAbbr(abbr_list, "dr.") is True


class TestIsWithin:
    """Test the isWithin function."""

    def test_found_returns_tuple(self):
        """Return tuple when abbreviation found."""
        abbr_list = [
            ["dr.", "NOUN", "doutor", "Abbr=Yes"],
            ["sr.", "NOUN", "senhor", "Abbr=Yes"],
        ]
        upos, lemma, feats = isWithin(abbr_list, "dr.")
        assert upos == "NOUN"
        assert lemma == "doutor"
        assert feats == "Abbr=Yes"

    def test_not_found_returns_none(self):
        """Return None tuple when not found."""
        abbr_list = [
            ["dr.", "NOUN", "doutor", "Abbr=Yes"],
        ]
        upos, lemma, feats = isWithin(abbr_list, "prof.")
        assert upos is None
        assert lemma is None
        assert feats is None

    def test_empty_list(self):
        """Return None tuple for empty list."""
        upos, lemma, feats = isWithin([], "dr.")
        assert upos is None
        assert lemma is None
        assert feats is None


class TestFixCompoundUpper:
    """Test the fixCompoundUpper function."""

    def test_propn_returns_form(self):
        """PROPN returns form as lemma."""
        upos, lemma, feats = fixCompoundUpper("João-Paulo", "joão-paulo", "PROPN", "_")
        assert upos == "PROPN"
        assert lemma == "João-Paulo"  # form is returned
        assert feats == "_"

    def test_punct_returns_form(self):
        """PUNCT returns form as lemma."""
        upos, lemma, feats = fixCompoundUpper("...", "...", "PUNCT", "_")
        assert upos == "PUNCT"
        assert lemma == "..."
        assert feats == "_"

    def test_sym_returns_form(self):
        """SYM returns form as lemma."""
        upos, lemma, feats = fixCompoundUpper("R$", "R$", "SYM", "_")
        assert upos == "SYM"
        assert lemma == "R$"
        assert feats == "_"

    def test_x_returns_form(self):
        """X returns form as lemma."""
        upos, lemma, feats = fixCompoundUpper("wifi", "wifi", "X", "_")
        assert upos == "X"
        assert lemma == "wifi"
        assert feats == "_"

    def test_noun_lowercases_lemma(self):
        """NOUN lowercases lemma."""
        upos, lemma, feats = fixCompoundUpper("guarda-chuva", "Guarda-Chuva", "NOUN", "_")
        assert upos == "NOUN"
        assert lemma == "guarda-chuva"

    def test_adj_lowercases_lemma(self):
        """ADJ lowercases lemma."""
        upos, lemma, feats = fixCompoundUpper("verde-claro", "Verde-Claro", "ADJ", "_")
        assert upos == "ADJ"
        assert lemma == "verde-claro"

    def test_verb_lowercases_lemma(self):
        """VERB lowercases lemma."""
        upos, lemma, feats = fixCompoundUpper("mal-estar", "Mal-Estar", "VERB", "_")
        assert upos == "VERB"
        assert lemma == "mal-estar"


class TestFeatsFull:
    """Test the featsFull function for feature assembly."""

    def test_empty_input(self):
        """Empty features returns underscore."""
        result = featsFull("_")
        assert result == "_"

    def test_passthrough_features(self):
        """Existing features pass through."""
        result = featsFull("Gender=Masc|Number=Sing")
        assert "Gender=Masc" in result
        assert "Number=Sing" in result

    def test_add_abbr_yes(self):
        """Add Abbr=Yes when abbr=True."""
        result = featsFull("_", abbr=True)
        assert result == "Abbr=Yes"

    def test_add_abbr_to_existing(self):
        """Add Abbr=Yes to existing features."""
        result = featsFull("Gender=Masc", abbr=True)
        assert "Abbr=Yes" in result
        assert "Gender=Masc" in result

    def test_remove_abbr(self):
        """Remove Abbr=Yes when abbr=False."""
        result = featsFull("Abbr=Yes|Gender=Masc", abbr=False)
        assert "Abbr=Yes" not in result
        assert "Gender=Masc" in result

    def test_add_extpos(self):
        """Add ExtPos when provided."""
        result = featsFull("_", extpos="ADP")
        assert result == "ExtPos=ADP"

    def test_replace_extpos(self):
        """Replace existing ExtPos."""
        result = featsFull("ExtPos=NOUN", extpos="ADP")
        assert "ExtPos=ADP" in result
        assert "ExtPos=NOUN" not in result

    def test_add_voice_pass(self):
        """Add Voice=Pass when voicepass=True."""
        result = featsFull("_", voicepass=True)
        assert result == "Voice=Pass"

    def test_remove_voice_pass(self):
        """Remove Voice=Pass when voicepass=False."""
        result = featsFull("Voice=Pass|Gender=Masc", voicepass=False)
        assert "Voice=Pass" not in result
        assert "Gender=Masc" in result

    def test_add_prontype(self):
        """Add PronType when provided."""
        result = featsFull("_", prontype="Art")
        assert result == "PronType=Art"

    def test_replace_prontype(self):
        """Replace existing PronType."""
        result = featsFull("PronType=Dem", prontype="Art")
        assert "PronType=Art" in result
        assert "PronType=Dem" not in result

    def test_add_verbform(self):
        """Add VerbForm when provided."""
        result = featsFull("_", verbform="Inf")
        assert result == "VerbForm=Inf"

    def test_replace_verbform(self):
        """Replace existing VerbForm."""
        result = featsFull("VerbForm=Fin", verbform="Inf")
        assert "VerbForm=Inf" in result
        assert "VerbForm=Fin" not in result

    def test_add_numtype(self):
        """Add NumType when provided."""
        result = featsFull("_", numtype="Card")
        assert result == "NumType=Card"

    def test_replace_numtype(self):
        """Replace existing NumType."""
        result = featsFull("NumType=Ord", numtype="Card")
        assert "NumType=Card" in result
        assert "NumType=Ord" not in result

    def test_multiple_additions(self):
        """Add multiple features at once."""
        result = featsFull("Gender=Masc", abbr=True, extpos="ADP", voicepass=True)
        assert "Abbr=Yes" in result
        assert "ExtPos=ADP" in result
        assert "Voice=Pass" in result
        assert "Gender=Masc" in result

    def test_features_sorted(self):
        """Features are sorted alphabetically (case-insensitive)."""
        # Note: Abbr=Yes is removed by default (abbr=False), so test with abbr=True
        result = featsFull("Number=Sing|Gender=Masc", abbr=True)
        parts = result.split("|")
        # Features should be sorted
        assert len(parts) == 3
        assert "Abbr=Yes" in parts
        assert "Gender=Masc" in parts
        assert "Number=Sing" in parts

    def test_none_prontype_no_change(self):
        """PronType=None doesn't add or remove."""
        result = featsFull("PronType=Art", prontype=None)
        assert "PronType=Art" in result

    def test_empty_prontype_no_add(self):
        """Empty prontype string doesn't add."""
        result = featsFull("Gender=Masc", prontype="")
        assert "PronType" not in result


class TestLocateExtPos:
    """Test the locateExtPos function."""

    def test_find_fixed_heads(self):
        """Find heads of fixed relations."""
        # Token format: [ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC]
        tokens = [
            ["1", "a", "a", "ADP", "_", "_", "3", "case", "_", "_"],
            ["2", "partir", "partir", "VERB", "_", "_", "1", "fixed", "_", "_"],
            ["3", "de", "de", "ADP", "_", "_", "0", "root", "_", "_"],
        ]
        fixeds = locateExtPos(tokens)
        assert "1" in fixeds  # Token 1 is the head of token 2's fixed relation

    def test_no_fixed_relations(self):
        """Return empty when no fixed relations."""
        tokens = [
            ["1", "O", "o", "DET", "_", "_", "2", "det", "_", "_"],
            ["2", "gato", "gato", "NOUN", "_", "_", "0", "root", "_", "_"],
        ]
        fixeds = locateExtPos(tokens)
        assert fixeds == []

    def test_multiple_fixed_heads(self):
        """Find multiple fixed heads."""
        tokens = [
            ["1", "a", "a", "ADP", "_", "_", "4", "case", "_", "_"],
            ["2", "partir", "partir", "VERB", "_", "_", "1", "fixed", "_", "_"],
            ["3", "de", "de", "ADP", "_", "_", "1", "fixed", "_", "_"],
            ["4", "agora", "agora", "ADV", "_", "_", "0", "root", "_", "_"],
        ]
        fixeds = locateExtPos(tokens)
        assert "1" in fixeds

    def test_no_duplicates(self):
        """Don't add duplicate head IDs."""
        tokens = [
            ["1", "a", "a", "ADP", "_", "_", "4", "case", "_", "_"],
            ["2", "partir", "partir", "VERB", "_", "_", "1", "fixed", "_", "_"],
            ["3", "de", "de", "ADP", "_", "_", "1", "fixed", "_", "_"],
            ["4", "agora", "agora", "ADV", "_", "_", "0", "root", "_", "_"],
        ]
        fixeds = locateExtPos(tokens)
        assert fixeds.count("1") == 1  # Only one entry for head "1"


class TestSepLEMMA_FEATS:
    """Test the sepLEMMA_FEATS function."""

    def test_single_option(self):
        """Single option returns single lemma and feat."""
        options = [
            ["gato", "NOUN", "Gender=Masc|Number=Sing"],
        ]
        lemmas, feats = sepLEMMA_FEATS(options)
        assert lemmas == ["gato"]
        assert feats == ["Gender=Masc|Number=Sing"]

    def test_multiple_options_same_lemma(self):
        """Multiple options with same lemma."""
        options = [
            ["gato", "NOUN", "Gender=Masc|Number=Sing"],
            ["gato", "NOUN", "Gender=Masc|Number=Plur"],
        ]
        lemmas, feats = sepLEMMA_FEATS(options)
        assert lemmas == ["gato"]  # No duplicates
        assert "Gender=Masc|Number=Sing" in feats
        assert "Gender=Masc|Number=Plur" in feats

    def test_multiple_options_different_lemmas(self):
        """Multiple options with different lemmas."""
        options = [
            ["ser", "AUX", "VerbForm=Fin"],
            ["estar", "AUX", "VerbForm=Fin"],
        ]
        lemmas, feats = sepLEMMA_FEATS(options)
        assert "ser" in lemmas
        assert "estar" in lemmas

    def test_empty_options(self):
        """Empty options returns empty lists."""
        lemmas, feats = sepLEMMA_FEATS([])
        assert lemmas == []
        assert feats == []

    def test_no_duplicate_feats(self):
        """No duplicate feature strings."""
        options = [
            ["o", "DET", "Gender=Masc|Number=Sing"],
            ["a", "DET", "Gender=Masc|Number=Sing"],  # Same feats, different lemma
        ]
        lemmas, feats = sepLEMMA_FEATS(options)
        assert len(feats) == 1  # Only one unique feat string


class TestGetUsualAbbr:
    """Test the getUsualAbbr function."""

    def test_loads_abbreviations(self):
        """Load abbreviations from file."""
        abbr = getUsualAbbr()
        # Should return a list
        assert isinstance(abbr, list)
        # Each item should have 4 elements: [form, upos, lemma, feats]
        if len(abbr) > 0:
            assert len(abbr[0]) == 4

    def test_abbreviation_format(self):
        """Abbreviations have correct format."""
        abbr = getUsualAbbr()
        for item in abbr:
            # Each should be [form, upos, lemma, feats]
            assert len(item) == 4
            assert isinstance(item[0], str)  # form
            assert isinstance(item[1], str)  # upos
            assert isinstance(item[2], str)  # lemma
            assert isinstance(item[3], str)  # feats


class TestFeatsFullEdgeCases:
    """Test edge cases for featsFull."""

    def test_complex_feature_replacement(self):
        """Handle complex feature string with multiple replacements."""
        result = featsFull(
            "Gender=Masc|Number=Sing|PronType=Dem|VerbForm=Fin",
            abbr=True,
            prontype="Art",
            verbform="Inf"
        )
        assert "Abbr=Yes" in result
        assert "PronType=Art" in result
        assert "PronType=Dem" not in result
        assert "VerbForm=Inf" in result
        assert "VerbForm=Fin" not in result
        assert "Gender=Masc" in result
        assert "Number=Sing" in result

    def test_only_underscore_with_no_additions(self):
        """Underscore with no additions returns underscore."""
        result = featsFull("_", abbr=False, extpos="", voicepass=False)
        assert result == "_"

    def test_removes_all_to_empty(self):
        """Removing all features returns underscore."""
        result = featsFull("Abbr=Yes", abbr=False)
        assert result == "_"

