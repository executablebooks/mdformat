import sys
from typing import NoReturn

import mdformat._cli


def run_cli() -> NoReturn:
    exit_code = mdformat._cli.run(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    run_cli()
