from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Static

from ..models import Comment, CommentStatus


class CommentCard(Static):
    """Displays a single comment with action buttons."""

    class DeleteRequested(Message):
        def __init__(self, comment_id: str) -> None:
            self.comment_id = comment_id
            super().__init__()

    class SendToClaudeRequested(Message):
        def __init__(self, comment_id: str) -> None:
            self.comment_id = comment_id
            super().__init__()

    class EditRequested(Message):
        def __init__(self, comment_id: str) -> None:
            self.comment_id = comment_id
            super().__init__()

    class FocusBlock(Message):
        def __init__(self, block_start: int, block_end: int) -> None:
            self.block_start = block_start
            self.block_end = block_end
            super().__init__()

    def __init__(self, comment: Comment, **kwargs) -> None:
        super().__init__(**kwargs)
        self.comment = comment

    def compose(self) -> ComposeResult:
        status_text = self._status_label()
        yield Static(status_text, classes="status-badge")
        if self.comment.anchor_text:
            preview = self.comment.anchor_text[:60]
            yield Static(f'"{preview}"', classes="anchor-preview")
        yield Static(self.comment.body, classes="comment-body")
        with Horizontal(classes="comment-actions"):
            yield Button("Delete", variant="error", id=f"del-{self.comment.id}")
            if self.comment.status in (CommentStatus.OPEN, CommentStatus.REJECTED):
                yield Button("Edit", variant="default", id=f"edit-{self.comment.id}")
                yield Button(
                    "Send to Claude",
                    variant="primary",
                    id=f"claude-{self.comment.id}",
                )

    def _status_label(self) -> str:
        labels = {
            CommentStatus.OPEN: "[bold #00e5ff][ OPEN ][/bold #00e5ff]",
            CommentStatus.PENDING_REVIEW: "[bold #ffd600][ PENDING... ][/bold #ffd600]",
            CommentStatus.COMPLETE: "[bold #00e676][ COMPLETE ][/bold #00e676]",
            CommentStatus.REJECTED: "[bold #ff1744][ REJECTED ][/bold #ff1744]",
        }
        return labels.get(self.comment.status, "")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("del-"):
            self.post_message(self.DeleteRequested(self.comment.id))
        elif btn_id.startswith("claude-"):
            self.post_message(self.SendToClaudeRequested(self.comment.id))
        elif btn_id.startswith("edit-"):
            self.post_message(self.EditRequested(self.comment.id))
        event.stop()

    def on_click(self) -> None:
        if self.comment.block_index >= 0:
            self.post_message(
                self.FocusBlock(self.comment.block_index, self.comment.block_end)
            )


class CommentPanel(Vertical):
    """Right sidebar listing all comments."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Static("// COMMENTS", id="panel-header")
        yield VerticalScroll(id="comment-list")

    async def refresh_comments(self, comments: list[Comment]) -> None:
        comment_list = self.query_one("#comment-list", VerticalScroll)
        await comment_list.remove_children()
        for comment in comments:
            await comment_list.mount(CommentCard(comment, id=f"card-{comment.id}"))
