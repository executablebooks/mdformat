from html.parser import HTMLParser
from typing import Iterable, List, Optional, Set

from markdown_it import MarkdownIt

import mdformat.plugins


def is_md_equal(
    md1: str,
    md2: str,
    *,
    enabled_extensions: Iterable[str] = (),
    enabled_codeformatters: Iterable[str] = (),
) -> bool:
    """Check if two Markdown produce the same HTML.

    Renders HTML from both Markdown strings, strip content of tags with
    specified classes, and checks equality of the generated ASTs.
    """
    ignore_classes = [f"language-{lang}" for lang in enabled_codeformatters]
    mdit = MarkdownIt()
    for name in enabled_extensions:
        plugin = mdformat.plugins.PARSER_EXTENSIONS[name]
        plugin.update_mdit(mdit)
        ignore_classes.extend(getattr(plugin, "ignore_classes", []))
    html1 = HTML2AST().parse(mdit.render(md1), ignore_classes)
    html2 = HTML2AST().parse(mdit.render(md2), ignore_classes)

    return html1 == html2


class HTML2AST(HTMLParser):
    """Parser HTML to AST."""

    def parse(self, text: str, strip_classes: Iterable[str] = ()) -> List[dict]:
        self.tree: List[dict] = []
        self.current: Optional[dict] = None
        self.feed(text)
        self.strip_classes(self.tree, set(strip_classes))
        return self.tree

    def strip_classes(self, tree: List[dict], classes: Set[str]) -> List[dict]:
        """Strip content from tags with certain classes."""
        items = []
        for item in tree:
            if set(item["attrs"].get("class", "").split()).intersection(classes):
                items.append({"tag": item["tag"], "attrs": item["attrs"]})
                continue
            items.append(item)
            item["children"] = self.strip_classes(item.get("children", []), classes)
            if not item["children"]:
                item.pop("children")

        return items

    def handle_starttag(self, tag: str, attrs: list) -> None:
        tag_item = {"tag": tag, "attrs": dict(attrs), "parent": self.current}
        if self.current is None:
            self.tree.append(tag_item)
        else:
            children = self.current.setdefault("children", [])
            children.append(tag_item)
        self.current = tag_item

    def handle_endtag(self, tag: str) -> None:
        # walk up the tree to the tag's parent
        while self.current is not None:
            if self.current["tag"] == tag:
                self.current = self.current.pop("parent")
                break
            self.current = self.current.pop("parent")

    def handle_data(self, data: str) -> None:
        # ignore data outside tabs
        if self.current is not None:
            # ignore empty lines and trailing whitespace
            self.current["data"] = [
                li.rstrip() for li in data.splitlines() if li.strip()
            ]
