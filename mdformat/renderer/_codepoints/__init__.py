__all__ = ("UNICODE_PUNCTUATION", "UNICODE_WHITESPACE")

from .unicode_punctuation import UNICODE_PUNCTUATION
from .unicode_whitespace import UNICODE_WHITESPACE

ASCII_CTRL = frozenset(chr(i) for i in range(32))
ASCII_SPACE = frozenset({chr(9), chr(10), chr(11), chr(12), chr(13), chr(32)})
