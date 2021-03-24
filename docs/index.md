# mdformat

> CommonMark compliant Markdown formatter

Mdformat is an opinionated Markdown formatter
that can be used to enforce a consistent style in Markdown files.
Mdformat is a Unix-style command-line tool as well as a Python library.

The features/opinions of the formatter include:

- Consistent indentation and whitespace across the board
- Always use ATX style headings
- Move all link references to the bottom of the document (sorted by label)
- Reformat indented code blocks as fenced code blocks
- Use `1.` as the ordered list marker if possible, also for noninitial list items

Mdformat by default will not change word wrapping.
The rationale for this is to support [Semantic Line Breaks](https://sembr.org/).

For a comprehensive description and rationalization of the style,
read [the style guide](users/style.md).

**NOTE:**
The formatting style produced by mdformat may change in each version.
It is recommended to pin mdformat dependency version.

```{toctree}
---
maxdepth: 2
caption: For users
---
users/installation_and_usage.md
users/plugins.md
users/style.md
```

```{toctree}
---
maxdepth: 2
caption: For developers
---
developers/contributing.md
developers/changelog.md
GitHub repository <https://github.com/executablebooks/mdformat>
```
