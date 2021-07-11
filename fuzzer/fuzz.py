# TODO: move all imports except `atheris` under this contextmanager in atheris>1.0.11
# with atheris.instrument_imports():
import sys
import warnings

import atheris

import mdformat
from mdformat._util import is_md_equal

# Suppress all warnings.
warnings.simplefilter("ignore")


def test_one_input(input_bytes: bytes) -> None:
    # We need a Unicode string, not bytes
    fdp = atheris.FuzzedDataProvider(input_bytes)
    data = fdp.ConsumeUnicode(sys.maxsize)

    try:
        formatted_data = mdformat.text(data)
    except BaseException:
        print_err(data)
        raise

    if not is_md_equal(data, formatted_data):
        print_err(data)
        raise Exception("Formatted Markdown not equal!")


def print_err(data):
    codepoints = [hex(ord(x)) for x in data]
    sys.stderr.write(f"Input was {type(data)}:\n{data}\nCodepoints:\n{codepoints}\n")
    sys.stderr.flush()


def main():
    # For possible options, see https://llvm.org/docs/LibFuzzer.html#options
    fuzzer_options = sys.argv
    atheris.Setup(fuzzer_options, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
