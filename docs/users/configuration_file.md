# Configuration file

Mdformat allows configuration in a [TOML](https://toml.io) file named `.mdformat.toml`.

The configuration file will be resolved starting from the location of the file being formatted,
and searching up the file tree until a config file is (or isn't) found.
When formatting standard input stream, resolution will be started from current working directory.

Command line interface arguments take precedence over the configuration file.

## Example configuration

```toml
# .mdformat.toml
#
# This file shows the default values and is equivalent to having
# no configuration file at all. Change the values for non-default
# behavior.
#
wrap = "keep"       # possible values: {"keep", "no", INTEGER}
number = false      # possible values: {false, true}
end_of_line = "lf"  # possible values: {"lf", "crlf"}
```
