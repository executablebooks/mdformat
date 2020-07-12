# mdformat
**WARNING:** This is pre-alpha software.
There is no stable library API, and the Markdown formatting rules may change at any time.

## Usage
### As a pre-commit hook
` mdformat ` can be used as a [pre-commit](<https://github.com/pre-commit/pre-commit>) hook.
Add the following to your project's ` .pre-commit-config.yaml ` to enable this:

~~~yaml
- repo: https://github.com/hukkinj1/mdformat
  rev: 0.0.2  # Use the ref you want to point at
  hooks:
  - id: mdformat
~~~
