from mdformat._cli import run
from mdformat._conf import read_toml_opts

UNFORMATTED_MARKDOWN = "\n\n# A header\n\n"
FORMATTED_MARKDOWN = "# A header\n"


def run_with_clear_cache(*args, **kwargs):
    read_toml_opts.cache_clear()
    return run(*args, **kwargs)
