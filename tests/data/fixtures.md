strip paragraph lines
.
trailing whitespace 
at the end of paragraph lines 
should be stripped                   
.
trailing whitespace
at the end of paragraph lines
should be stripped
.

strip quotes
.
> Paragraph 1
> 
> Paragraph 2
.
> Paragraph 1
>
> Paragraph 2
.

no escape ampersand
.
R&B, rock & roll
.
R&B, rock & roll
.

list whitespaces
.
- item one
  
- item two
  - sublist
  
  - sublist
.
- item one

- item two

  - sublist

  - sublist
.

convert setext to ATX heading
.
Top level heading
=========

2nd level heading
---------
.
# Top level heading

## 2nd level heading
.

Lists with different bullets
.
- a
- b
* c
.
- a
- b

* c
.

numbered lists
.
1. a
2. b
.
1. a
1. b
.

references:
.
[ref2]: link3 "title"

[text](link1) [text](link2 "title") [ref1] [ref2] [text][ref1]

![text](link1) ![text](link2 "title") ![ref1] ![ref2] ![text][ref1]

[ref1]: link4
[unused]: link5
.
[text](<link1>) [text](<link2> "title") [ref1][ref1] [ref2][ref2] [text][ref1]

![text](link1) ![text](link2 "title") ![ref1] ![ref2] ![text][ref1]

[ref1]: link4
[ref2]: link3 "title"
.
