import atheris

with atheris.instrument_imports():
    import hashlib
    import sys
    import warnings

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
        handle_err(data)
        raise

    if not is_md_equal(data, formatted_data):
        handle_err(data)
        raise Exception("Formatted Markdown not equal!")


def handle_err(data):
    codepoints = [hex(ord(x)) for x in data]
    sys.stderr.write(f"Input was {type(data)}:\n{data}\nCodepoints:\n{codepoints}\n")

    # Atheris already writes crash data to a file, but it seems it is not UTF-8 encoded.
    # I'm not sure what the encoding is exactly. Anyway, let's write another file here
    # that is guaranteed to be valid UTF-8.
    data_bytes = data.encode()
    filename = "crash-utf8-" + hashlib.sha256(data_bytes).hexdigest()
    with open(filename, "wb") as f:
        f.write(data_bytes)
    sys.stderr.write(f"Wrote UTF-8 encoded data to {filename}\n")

    sys.stderr.flush()


def main():
    # For possible options, see https://llvm.org/docs/LibFuzzer.html#options
    fuzzer_options = sys.argv
    atheris.Setup(fuzzer_options, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
