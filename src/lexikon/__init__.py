"""PortiLexicon-UD - Portuguese lexicon for Universal Dependencies."""

from lexikon.lexikon import UDlexPT
from lexikon.abbrev import is_abbreviation, ends_with_abbreviation

# Singleton instance - created once on first import
lex = UDlexPT()

__all__ = ["UDlexPT", "lex", "is_abbreviation", "ends_with_abbreviation"]
