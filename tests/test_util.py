from mdformat._util import HTML2JSON


def test_html2json():
    data = HTML2JSON().parse('<div><p class="x">a<s>j</s></p></div><a>b</a>')
    assert data == [
        {
            "tag": "div",
            "attrs": {},
            "children": [
                {
                    "tag": "p",
                    "attrs": {"class": "x"},
                    "data": "a",
                    "children": [{"tag": "s", "attrs": {}, "data": "j"}],
                }
            ],
        },
        {"tag": "a", "attrs": {}, "data": "b"},
    ]


def test_html2json_strip():
    data = HTML2JSON().parse('<div><p class="x y">a<s>j</s></p></div><a>b</a>', {"x"})
    assert data == [
        {
            "tag": "div",
            "attrs": {},
            "children": [{"tag": "p", "attrs": {"class": "x y"}}],
        },
        {"tag": "a", "attrs": {}, "data": "b"},
    ]
