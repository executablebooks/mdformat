__all__ = (
    "UNICODE_PUNCTUATION",
    "UNICODE_WHITESPACE",
    "ASCII_CTRL",
    "ASCII_WHITESPACE",
)

from ._unicode_punctuation import UNICODE_PUNCTUATION
from ._unicode_whitespace import UNICODE_WHITESPACE

ASCII_CTRL = frozenset(chr(i) for i in range(32))
ASCII_WHITESPACE = frozenset({chr(9), chr(10), chr(11), chr(12), chr(13), chr(32)})
