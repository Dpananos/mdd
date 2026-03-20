from __future__ import annotations

from textual.events import Click
from textual.message import Message
from textual.widgets import Markdown
from textual.widgets._markdown import MarkdownBlock


class CommentableMarkdown(Markdown):
    """Markdown widget where rendered blocks are clickable for commenting.

    Click selects a single block. Shift+click or shift+up/down extends the
    selection to a contiguous range.
    """

    class SelectionChanged(Message):
        """Posted when the selected block range changes."""

        def __init__(self, start: int, end: int) -> None:
            self.start = start  # inclusive
            self.end = end  # inclusive
            super().__init__()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._sel_anchor: int | None = None  # the fixed end of the selection
        self._sel_cursor: int | None = None  # the moving end (keyboard/shift-click)

    @property
    def selection(self) -> tuple[int, int] | None:
        """Return (start, end) inclusive, or None if nothing selected."""
        if self._sel_anchor is not None and self._sel_cursor is not None:
            lo = min(self._sel_anchor, self._sel_cursor)
            hi = max(self._sel_anchor, self._sel_cursor)
            return (lo, hi)
        return None

    def _block_count(self) -> int:
        return len(list(self.query(MarkdownBlock)))

    def on_click(self, event: Click) -> None:
        widget = getattr(event, "widget", self)
        block = self._find_parent_block(widget)
        if block is None:
            return
        block_index = self._get_block_index(block)
        if block_index < 0:
            return

        if event.shift and self._sel_anchor is not None:
            self._sel_cursor = block_index
        else:
            self._sel_anchor = block_index
            self._sel_cursor = block_index

        self._emit_selection()

    def extend_up(self) -> None:
        """Extend (or start) the selection one block upward."""
        n = self._block_count()
        if n == 0:
            return
        if self._sel_anchor is None:
            # Nothing selected yet – select the last block
            self._sel_anchor = n - 1
            self._sel_cursor = n - 1
        if self._sel_cursor is not None and self._sel_cursor > 0:
            self._sel_cursor -= 1
        self._emit_selection()

    def extend_down(self) -> None:
        """Extend (or start) the selection one block downward."""
        n = self._block_count()
        if n == 0:
            return
        if self._sel_anchor is None:
            # Nothing selected yet – select the first block
            self._sel_anchor = 0
            self._sel_cursor = 0
        if self._sel_cursor is not None and self._sel_cursor < n - 1:
            self._sel_cursor += 1
        self._emit_selection()

    def move_up(self) -> None:
        """Move the selection one block up (no extend)."""
        n = self._block_count()
        if n == 0:
            return
        if self._sel_cursor is None:
            self._sel_anchor = n - 1
            self._sel_cursor = n - 1
        elif self._sel_cursor > 0:
            self._sel_cursor -= 1
            self._sel_anchor = self._sel_cursor
        self._emit_selection()

    def move_down(self) -> None:
        """Move the selection one block down (no extend)."""
        n = self._block_count()
        if n == 0:
            return
        if self._sel_cursor is None:
            self._sel_anchor = 0
            self._sel_cursor = 0
        elif self._sel_cursor < n - 1:
            self._sel_cursor += 1
            self._sel_anchor = self._sel_cursor
        self._emit_selection()

    def _emit_selection(self) -> None:
        sel = self.selection
        if sel is not None:
            self._highlight_selection()
            self.post_message(self.SelectionChanged(sel[0], sel[1]))

    def _find_parent_block(self, widget) -> MarkdownBlock | None:
        current = widget
        while current is not None and current is not self:
            if isinstance(current, MarkdownBlock):
                return current
            current = current.parent
        return None

    def _get_block_index(self, block: MarkdownBlock) -> int:
        for i, b in enumerate(self.query(MarkdownBlock)):
            if b is block:
                return i
        return -1

    def _highlight_selection(self) -> None:
        sel = self.selection  # uses anchor/cursor to compute (lo, hi)
        blocks = list(self.query(MarkdownBlock))
        for i, b in enumerate(blocks):
            if sel is not None and sel[0] <= i <= sel[1]:
                b.add_class("selected")
            else:
                b.remove_class("selected")

    def highlight_range(self, start: int, end: int) -> None:
        """Highlight a range of blocks (inclusive on both ends)."""
        self._sel_anchor = start
        self._sel_start = start
        self._sel_end = end
        self._highlight_selection()

    def mark_commented_blocks(self, indices: set[int]) -> None:
        blocks = list(self.query(MarkdownBlock))
        for i, b in enumerate(blocks):
            if i in indices:
                b.add_class("commented")
            else:
                b.remove_class("commented")
