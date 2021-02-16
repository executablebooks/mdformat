from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mdformat.renderer.tree import TreeNode


def is_text_inside_autolink(node: "TreeNode") -> bool:
    assert node.type_ == "text"
    return (
        node.parent
        and node.parent.type_ == "link"
        and node.parent.opening.markup == "autolink"
    )


def is_tight_list(node: "TreeNode") -> bool:
    assert node.type_ in {"bullet_list", "ordered_list"}

    # The list has list items at level +1 so paragraphs in those list
    # items must be at level +2 (grand children)
    for child in node.children:
        for grand_child in child.children:
            if grand_child.type_ != "paragraph":
                continue
            is_tight = grand_child.opening.hidden
            if not is_tight:
                return False
    return True


def is_tight_list_item(node: "TreeNode") -> bool:
    assert node.type_ == "list_item"
    assert node.parent is not None
    return is_tight_list(node.parent)


def get_list_marker_type(node: "TreeNode") -> str:
    if node.type_ == "bullet_list":
        mode = "bullet"
        primary_marker = "-"
        secondary_marker = "*"
    else:
        mode = "ordered"
        primary_marker = "."
        secondary_marker = ")"
    consecutive_lists_count = 1
    current = node
    while True:
        previous_sibling = current.previous_sibling()
        if previous_sibling is None:
            return primary_marker if consecutive_lists_count % 2 else secondary_marker
        prev_type = previous_sibling.type_
        if (mode == "bullet" and prev_type == "bullet_list") or (
            mode == "ordered" and prev_type == "ordered_list"
        ):
            consecutive_lists_count += 1
            current = previous_sibling
        else:
            return primary_marker if consecutive_lists_count % 2 else secondary_marker
