from mdformat._cli import run


def test_no_files_passed():
    assert run(()) == 0
