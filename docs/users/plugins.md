# Plugins

Mdformat offers an extensible plugin system for code fence content formatting, Markdown parser extensions (like GFM tables),
and modifying/adding other functionality. This document explains how to use plugins.
If you want to create a new plugin, refer to the [contributing](../contributors/contributing.md) docs.

## Code formatter plugins

Mdformat features a plugin system to support formatting of Markdown code blocks where the coding language has been labeled.
For instance, if [`mdformat-black`](https://github.com/hukkin/mdformat-black) plugin is installed in the environment,
mdformat CLI will automatically format Python code blocks with [Black](https://github.com/psf/black).

For stability, mdformat Python API behavior will not change simply due to a plugin being installed.
Code formatters will have to be explicitly enabled in addition to being installed:

````python
import mdformat

unformatted = "```python\n'''black converts quotes'''\n```\n"
# Pass in `codeformatters` here! It is an iterable of coding languages
# that should be formatted
formatted = mdformat.text(unformatted, codeformatters={"python"})
assert formatted == '```python\n"""black converts quotes"""\n```\n'
````

### Existing plugins

<table>
  <tr>
    <th>Plugin</th>
    <th>Supported languages</th>
    <th>Notes</th>
  </tr>
  <tr>
    <td><a href="https://github.com/hukkin/mdformat-beautysh">mdformat-beautysh</a></td>
    <td><code>bash</code>, <code>sh</code></td>
    <td></td>
  </tr>
  <tr>
    <td><a href="https://github.com/hukkin/mdformat-black">mdformat-black</a></td>
    <td><code>python</code></td>
    <td></td>
  </tr>
  <tr>
    <td><a href="https://github.com/hukkin/mdformat-config">mdformat-config</a></td>
    <td><code>json</code>, <code>toml</code>, <code>yaml</code></td>
    <td></td>
  </tr>
  <tr>
    <td><a href="https://github.com/hukkin/mdformat-gofmt">mdformat-gofmt</a></td>
    <td><code>go</code></td>
    <td>Requires <a href="https://golang.org/doc/install">Go</a> installation</td>
  </tr>
  <tr>
    <td><a href="https://github.com/hukkin/mdformat-rustfmt">mdformat-rustfmt</a></td>
    <td><code>rust</code></td>
    <td>Requires <a href="https://github.com/rust-lang/rustfmt#quick-start">rustfmt</a> installation</td>
  </tr>
  <tr>
    <td><a href="https://github.com/hukkin/mdformat-shfmt">mdformat-shfmt</a></td>
    <td><code>bash</code>, <code>sh</code></td>
    <td>Requires either <a href="https://github.com/mvdan/sh#shfmt">shfmt</a> or <a href="https://docs.docker.com/get-docker/">Docker</a> installation</td>
  </tr>
  <tr>
    <td><a href="https://github.com/hukkin/mdformat-web">mdformat-web</a></td>
    <td><code>javascript</code>, <code>js</code>, <code>css</code>, <code>html</code>, <code>xml</code></td>
    <td></td>
  </tr>
</table>

## Parser extension plugins

Markdown-it-py offers a range of useful extensions to the base CommonMark parser (see the [documented list](https://markdown-it-py.readthedocs.io/en/latest/plugins.html)).

Mdformat features a plugin system to support the loading and rendering of such extensions.

For stability, mdformat Python API behavior will not change simply due to a plugin being installed.
Extensions will have to be explicitly enabled in addition to being installed:

```python
import mdformat

unformatted = "content...\n"
# Pass in `extensions` here! It is an iterable of extensions that should be loaded
formatted = mdformat.text(unformatted, extensions={"tables"})
```

### Existing plugins

<table>
  <tr>
    <th>Plugin</th>
    <th>Syntax Extensions</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><a href="https://github.com/KyleKing/mdformat-admon">mdformat-admon</a></td>
    <td><code>admonition</code></td>
    <td>Adds support for <a href="https://python-markdown.github.io/extensions/admonition/">python-markdown</a> admonitions</td>
  </tr>
  <tr>
    <td><a href="https://github.com/executablebooks/mdformat-deflist">mdformat-deflist</a></td>
    <td><code>deflist</code></td>
    <td>Adds support for <a href="https://pandoc.org/MANUAL.html#definition-lists">Pandoc-style</a> definition lists</td>
  </tr>
  <tr>
    <td><a href="https://github.com/executablebooks/mdformat-footnote">mdformat-footnote</a></td>
    <td><code>footnote</code></td>
    <td>Adds support for <a href="https://pandoc.org/MANUAL.html#footnotes">Pandoc-style</a> footnotes</td>
  </tr>
  <tr>
    <td><a href="https://github.com/butler54/mdformat-frontmatter">mdformat-frontmatter</a></td>
    <td><code>frontmatter</code></td>
    <td>Adds support for front matter, and formats YAML front matter</td>
  </tr>
  <tr>
    <td><a href="https://github.com/hukkin/mdformat-gfm">mdformat-gfm</a></td>
    <td><code>gfm</code></td>
    <td>Changes target specification to GitHub Flavored Markdown (GFM)</td>
  </tr>
  <tr>
    <td><a href="https://github.com/KyleKing/mdformat-mkdocs">mdformat-mkdocs</a></td>
    <td><code>mkdocs</code></td>
    <td>Changes target specification to MKDocs. Indents lists with 4-spaces instead of 2</td>
  </tr>
  <tr>
    <td><a href="https://github.com/executablebooks/mdformat-myst">mdformat-myst</a></td>
    <td><code>myst</code></td>
    <td>Changes target specification to <a href="https://myst-parser.readthedocs.io/en/latest/using/syntax.html">MyST</a></td>
  </tr>
  <tr>
    <td><a href="https://github.com/executablebooks/mdformat-tables">mdformat-tables</a></td>
    <td><code>tables</code></td>
    <td>Adds support for GitHub Flavored Markdown style tables</td>
  </tr>
  <tr>
    <td><a href="https://github.com/hukkin/mdformat-toc">mdformat-toc</a></td>
    <td><code>toc</code></td>
    <td>Adds the capability to auto-generate a table of contents</td>
  </tr>
</table>

## Other misc plugins

Other plugins that don't fit the above categories.

### Existing plugins

<table>
  <tr>
    <th>Plugin</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><a href="https://github.com/csala/mdformat-pyproject">mdformat-pyproject</a></td>
    <td>Adds support for loading options from a <code>[tool.mdformat]</code> section inside the <code>pyproject.toml</code> file, if it exists</td>
  </tr>
  <tr>
    <td><a href="https://github.com/csala/mdformat-simple-breaks">mdformat-simple-breaks</a></td>
    <td>Render <a href="https://mdformat.readthedocs.io/en/stable/users/style.html#thematic-breaks">thematic breaks</a> using three dashes instead of 70 underscores</td>
  </tr>
</table>
