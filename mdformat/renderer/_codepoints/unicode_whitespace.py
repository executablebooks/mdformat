"""Pre-generated unicode whitespace characters.

Run this module to generate and print an up-to-date set of characters.
"""
UNICODE_WHITESPACE = frozenset(
    {
        "\t",
        "\u2008",
        "\u2009",
        "\u3000",
        "\u1680",
        "\u2005",
        "\u2003",
        "\x0c",
        "\u200a",
        "\u2006",
        " ",
        "\x0b",
        "\r",
        "\u2001",
        "\u205f",
        "\u2002",
        "\n",
        "\xa0",
        "\u202f",
        "\u2004",
        "\u2007",
        "\u2000",
    }
)

if __name__ == "__main__":
    import string
    import sys
    import unicodedata

    UNICODE_CHARS = frozenset(chr(c) for c in range(sys.maxunicode + 1))
    UNICODE_WHITESPACE = frozenset(
        c for c in UNICODE_CHARS if unicodedata.category(c) == "Zs"
    ) | frozenset(string.whitespace)
    print(repr(UNICODE_WHITESPACE))
