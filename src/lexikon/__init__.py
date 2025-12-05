"""PortiLexicon-UD - Portuguese lexicon for Universal Dependencies."""

from lexikon.lexikon import UDlexPT

# Singleton instance - created once on first import
lex = UDlexPT()

__all__ = ["UDlexPT", "lex"]
