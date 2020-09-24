# Changelog

This log documents all Python API or CLI breaking backwards incompatible changes.
Note that there is currently no guarantee for a stable Markdown formatting style across versions.

## 0.3.1

- Added
  - Plugin system for extending the parser ([#13](https://github.com/executablebooks/mdformat/issues/13)).
    Thank you [chrisjsewell](https://github.com/chrisjsewell) for the issue and the PR.
  - Exported `mdformat.renderer.MDRenderer` and `mdformat.renderer.MARKERS`

## 0.3.0

- Changed
  - Code formatter plugin function signature changed to `Callable[[str, str], str]`.
    The second input argument is full info string of the code block.

## 0.2.0

- Changed
  - Style: Use backtick for code fences whenever possible

## 0.1.2

- Added
  - Support for code formatter plugins

## 0.1.0

- Added
  - Initial mdformat release
