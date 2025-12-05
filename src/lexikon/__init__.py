"""PortiLexicon-UD - Portuguese lexicon for Universal Dependencies."""

from lexikon.lexikon import UDlexPT
from lexikon.abbrev import is_abbreviation, ends_with_abbreviation

__all__ = ["UDlexPT", "is_abbreviation", "ends_with_abbreviation"]
