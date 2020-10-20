# Formatting style

Mdformat's formatting style is crafted so that writing, editing and collaborating on Markdown files is as smooth as possible.
The style attempts to minimize diffs (for ease of reviewing changes) and be consistent,
sometimes at the cost of some readability.

## Headings

For consistency, only ATX headings are used.
Setext headings are reformatted using the ATX style.
ATX headings are used because they can be consistently used for any heading level,
whereas setext headings only allow level 1 and 2 headings.

For example these setext headings

```markdown
First level heading
===

Second level heading
---
```

will be reformatted in ATX style

```markdown
# First level heading

## Second level heading
```

## Ordered lists

Mdformat uses `1.` or `1)` as the ordered list marker, also for noninital list items.
For example:

```markdown
1. Item 1
1. Item 2
1. Item 3
```

This "non-numbering" style was chosen to minimize diffs. But how exactly? Lets imagine we are listing the alphabets, using a proper consecutive numbering style:

```markdown
1. b
2. c
3. d
```

Now we notice an error was made, and that the first character "a" is missing.
We add it as the first item in the list.
As a result, the numbering of every subsequent item in the list will increase by one,
meaning that the diff will touch every line in the list.
The non-numbering style solves this issue: only the added line will show up in the diff.

Mdformat allows consecutive numbering via configuration.

## Code blocks

Only fenced code blocks are allowed.
Indented code blocks are reformatted as fenced code blocks.

Fenced code blocks are preferred because they allow setting an info string,
which indented code blocks do not support.

## Word wrap

Mdformat by default will not change word wrapping.
The rationale for this is to encourage and support [Semantic Line Breaks](<https://sembr.org/>),
a technique described by Brian Kernighan in the early 1970s:

> **Hints for Preparing Documents**
>
> Most documents go through several versions (always more than you
> expected) before they are finally finished. Accordingly, you should
> do whatever possible to make the job of changing them easy.
>
> First, when you do the purely mechanical operations of typing, type
> so subsequent editing will be easy. Start each sentence on a new line.
> Make lines short, and break lines at natural places, such as after
> commas and semicolons, rather than
> randomly. Since
> most people change documents by rewriting phrases and adding, deleting
> and rearranging sentences, these precautions simplify any editing you
> have to do later.
>
> _— Brian W. Kernighan. "UNIX for Beginners". 1974_
