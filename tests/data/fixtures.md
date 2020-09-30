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
3. c
   d
.
1. a
1. b
1. c
   d
.

numbered lists starting number
.
099. a
100. b
101. c
     d
.
99. a
01. b
01. c
    d
.

numbered lists nested
.
1. a
2. b
   1. x
   2. y
      z
.
1. a
1. b
   1. x
   1. y
      z
.

numbered lists [consecutive]
.
1. a
2. b
3. c
   d
.
1. a
2. b
3. c
   d
.

numbered lists starting number [consecutive]
.
099. a
100. b
101. c
     d
.
099. a
100. b
101. c
     d
.

numbered lists nested [consecutive]
.
1. a
2. b
   1. x
   2. y
      z
.
1. a
2. b
   1. x
   2. y
      z
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
