from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from textual.widgets._markdown import MarkdownBlock

from ..models import Comment

if False:  # TYPE_CHECKING
    from ..widgets.markdown_viewer import CommentableMarkdown


@dataclass
class BlockInfo:
    block_index: int
    source_start: int  # 0-indexed, inclusive
    source_end: int  # 0-indexed, exclusive
    anchor_text: str


class BlockLineTracker:
    def __init__(self) -> None:
        self.blocks: list[BlockInfo] = []

    def rebuild(self, md_widget: CommentableMarkdown) -> None:
        self.blocks.clear()
        all_blocks = list(md_widget.query(MarkdownBlock))

        for i, block in enumerate(all_blocks):
            start, end = block.source_range  # tuple[int, int], always set
            anchor = (block.source or "").strip()[:80]
            self.blocks.append(
                BlockInfo(
                    block_index=i,
                    source_start=start,
                    source_end=end,
                    anchor_text=anchor,
                )
            )

    def get_source_lines(self, block_index: int, source_text: str) -> str:
        if block_index < 0 or block_index >= len(self.blocks):
            return ""
        info = self.blocks[block_index]
        lines = source_text.splitlines(keepends=True)
        return "".join(lines[info.source_start : info.source_end])

    def get_source_lines_range(
        self, block_start: int, block_end: int, source_text: str
    ) -> str:
        """Get source lines spanning from block_start to block_end (inclusive)."""
        if block_start < 0 or block_end >= len(self.blocks):
            return ""
        start_info = self.blocks[block_start]
        end_info = self.blocks[block_end]
        lines = source_text.splitlines(keepends=True)
        return "".join(lines[start_info.source_start : end_info.source_end])

    def remap_after_edit(
        self,
        old_start: int,
        old_end: int,
        new_line_count: int,
        comments: list[Comment],
    ) -> None:
        delta = new_line_count - (old_end - old_start)
        for comment in comments:
            if comment.source_start >= old_end:
                comment.source_start += delta
                comment.source_end += delta
            elif comment.source_start >= old_start:
                comment.block_index = -1
                comment.source_start = -1
                comment.source_end = -1

    def reconcile_comments(self, comments: list[Comment]) -> None:
        for comment in comments:
            if 0 <= comment.block_index < len(self.blocks):
                continue

            # Try line-range match
            match = self._find_by_lines(comment.source_start, comment.source_end)
            if match is not None:
                comment.block_index = match.block_index
                comment.source_start = match.source_start
                comment.source_end = match.source_end
                continue

            # Fuzzy anchor match
            best_score = 0.0
            best_block: BlockInfo | None = None
            for info in self.blocks:
                if not comment.anchor_text or not info.anchor_text:
                    continue
                score = SequenceMatcher(
                    None, comment.anchor_text, info.anchor_text
                ).ratio()
                if score > best_score:
                    best_score = score
                    best_block = info

            if best_block and best_score > 0.6:
                comment.block_index = best_block.block_index
                comment.source_start = best_block.source_start
                comment.source_end = best_block.source_end
            else:
                comment.block_index = -1

    def _find_by_lines(self, start: int, end: int) -> BlockInfo | None:
        for info in self.blocks:
            if info.source_start == start and info.source_end == end:
                return info
        return None
