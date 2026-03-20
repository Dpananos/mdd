from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.design import ColorSystem
from textual.theme import Theme
from textual.widgets import Footer, Header
from textual._work_decorator import work

SYNTHWAVE_THEME = Theme(
    name="synthwave",
    primary="#ff2975",
    secondary="#00e5ff",
    accent="#b026ff",
    warning="#ffd600",
    error="#ff1744",
    success="#00e676",
    background="#0d0221",
    surface="#1a1a3e",
    panel="#1e1245",
    dark=True,
)

from .models import Comment, CommentStatus
from .screens.comment_input import CommentInputScreen
from .screens.confirm_delete import ConfirmDeleteScreen
from .screens.diff_view import DiffViewScreen
from .services import claude
from .services.line_tracker import BlockLineTracker
from .services.persistence import load_comments, save_comments
from .widgets.comment_panel import CommentCard, CommentPanel
from .widgets.markdown_viewer import CommentableMarkdown

from textual.widgets import Markdown


class MddApp(App):
    CSS_PATH = "styles/app.tcss"
    TITLE = "mdd"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "add_comment", "Comment"),
        Binding("r", "reload", "Reload"),
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("shift+up", "extend_up", "Extend Up", show=False),
        Binding("shift+down", "extend_down", "Extend Down", show=False),
    ]

    def __init__(self, file_path: Path, session: str | None = None) -> None:
        super().__init__()
        self.register_theme(SYNTHWAVE_THEME)
        self.theme = "synthwave"
        self.file_path = file_path
        self.session = session
        self.source_text = file_path.read_text()
        self.comments: list[Comment] = load_comments(file_path)
        self.line_tracker = BlockLineTracker()
        self._sel_start: int | None = None
        self._sel_end: int | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with VerticalScroll(id="doc-pane"):
                yield CommentableMarkdown(self.source_text, id="markdown-doc")
            yield CommentPanel(id="comment-pane")
        yield Footer()

    def on_mount(self) -> None:
        if not claude.claude_available():
            self.notify(
                "Claude Code CLI not found on PATH. 'Send to Claude' will not work.",
                severity="warning",
                timeout=5,
            )

    async def on_markdown_table_of_contents_updated(
        self, message: Markdown.TableOfContentsUpdated
    ) -> None:
        """Fired after the markdown widget finishes rendering."""
        await self._rebuild_tracker()
        if getattr(self, "_pending_save_after_rebuild", False):
            self._pending_save_after_rebuild = False
            self._save()

    async def _rebuild_tracker(self) -> None:
        md = self.query_one("#markdown-doc", CommentableMarkdown)
        self.line_tracker.rebuild(md)
        self.line_tracker.reconcile_comments(self.comments)
        await self._refresh_ui()

    def _save(self) -> None:
        save_comments(self.file_path, self.comments)

    async def _refresh_ui(self) -> None:
        panel = self.query_one("#comment-pane", CommentPanel)
        await panel.refresh_comments(self.comments)
        md = self.query_one("#markdown-doc", CommentableMarkdown)
        commented_indices: set[int] = set()
        for c in self.comments:
            if c.block_index >= 0:
                for i in range(c.block_index, c.block_end + 1):
                    commented_indices.add(i)
        md.mark_commented_blocks(commented_indices)

    # --- Block selection ---

    def on_commentable_markdown_selection_changed(
        self, message: CommentableMarkdown.SelectionChanged
    ) -> None:
        self._sel_start = message.start
        self._sel_end = message.end

    # --- Add comment ---

    def action_add_comment(self) -> None:
        if self._sel_start is None or self._sel_end is None:
            self.notify("Click a block first, then press 'c' to comment.", severity="warning")
            return
        blocks = self.line_tracker.blocks
        if self._sel_start >= len(blocks) or self._sel_end >= len(blocks):
            self.notify("Selected block is invalid.", severity="warning")
            return
        preview = self.line_tracker.get_source_lines_range(
            self._sel_start, self._sel_end, self.source_text
        )
        # Truncate for the preview modal
        self.push_screen(
            CommentInputScreen(preview[:200]),
            callback=self._on_comment_entered,
        )

    async def _on_comment_entered(self, result: str | None) -> None:
        if not result or not result.strip():
            return
        if self._sel_start is None or self._sel_end is None:
            return
        blocks = self.line_tracker.blocks
        start_info = blocks[self._sel_start]
        end_info = blocks[self._sel_end]
        anchor = self.line_tracker.get_source_lines_range(
            self._sel_start, self._sel_end, self.source_text
        ).strip()[:80]
        comment = Comment(
            block_index=self._sel_start,
            block_end=self._sel_end,
            source_start=start_info.source_start,
            source_end=end_info.source_end,
            anchor_text=anchor,
            body=result.strip(),
        )
        self.comments.append(comment)
        self._save()
        await self._refresh_ui()

    # --- Delete comment ---

    def on_comment_card_delete_requested(
        self, message: CommentCard.DeleteRequested
    ) -> None:
        self._pending_delete_id = message.comment_id
        self.push_screen(ConfirmDeleteScreen(), callback=self._on_delete_confirmed)

    async def _on_delete_confirmed(self, confirmed: bool) -> None:
        if confirmed:
            self.comments = [
                c for c in self.comments if c.id != self._pending_delete_id
            ]
            self._save()
            await self._refresh_ui()

    # --- Edit comment ---

    def on_comment_card_edit_requested(
        self, message: CommentCard.EditRequested
    ) -> None:
        comment = self._find_comment(message.comment_id)
        if comment is None:
            return
        self._editing_comment_id = comment.id
        self.push_screen(
            CommentInputScreen(comment.anchor_text, existing_text=comment.body),
            callback=self._on_comment_edited,
        )

    async def _on_comment_edited(self, result: str | None) -> None:
        if not result or not result.strip():
            return
        comment = self._find_comment(self._editing_comment_id)
        if comment is None:
            return
        comment.body = result.strip()
        if comment.status == CommentStatus.REJECTED:
            comment.status = CommentStatus.OPEN
        self._save()
        await self._refresh_ui()

    # --- Send to Claude ---

    async def on_comment_card_send_to_claude_requested(
        self, message: CommentCard.SendToClaudeRequested
    ) -> None:
        comment = self._find_comment(message.comment_id)
        if comment is None:
            return
        if not claude.claude_available():
            self.notify("Claude Code CLI not found on PATH.", severity="error")
            return
        comment.status = CommentStatus.PENDING_REVIEW
        await self._refresh_ui()
        self._call_claude(comment)

    @work(exclusive=True, thread=False)
    async def _call_claude(self, comment: Comment) -> None:
        self.notify("Sending to Claude...")
        try:
            section_text = self.line_tracker.get_source_lines_range(
                comment.block_index, comment.block_end, self.source_text
            )
            proposal = await claude.propose_edit(
                full_document=self.source_text,
                section_text=section_text,
                section_start_line=comment.source_start,
                section_end_line=comment.source_end,
                comment_text=comment.body,
                session=self.session,
            )
            comment.diff_proposal = proposal
            self.push_screen(
                DiffViewScreen(proposal),
                callback=lambda accepted: self._on_diff_decision(comment, accepted),
            )
        except Exception as e:
            comment.status = CommentStatus.OPEN
            self.notify(f"Error: {e}", severity="error")
            await self._refresh_ui()

    # --- Diff accept/reject ---

    async def _on_diff_decision(self, comment: Comment, accepted: bool) -> None:
        if accepted:
            self._apply_diff(comment)
        else:
            comment.status = CommentStatus.REJECTED
            comment.diff_proposal = None
            self._save()
            await self._refresh_ui()

    def _apply_diff(self, comment: Comment) -> None:
        proposal = comment.diff_proposal
        if proposal is None:
            return

        # Write to disk
        self.file_path.write_text(proposal.full_proposed_doc)
        old_start = comment.source_start
        old_end = comment.source_end
        new_line_count = len(proposal.proposed_lines.splitlines())

        self.source_text = proposal.full_proposed_doc
        comment.status = CommentStatus.COMPLETE
        comment.diff_proposal = None

        # Remap other comments
        self.line_tracker.remap_after_edit(
            old_start, old_end, new_line_count, self.comments
        )

        # Re-render markdown — _rebuild_tracker runs via
        # on_markdown_table_of_contents_updated after rendering completes
        self._pending_save_after_rebuild = True
        md = self.query_one("#markdown-doc", CommentableMarkdown)
        md.update(self.source_text)

    # --- Focus block from comment card ---

    def on_comment_card_focus_block(self, message: CommentCard.FocusBlock) -> None:
        md = self.query_one("#markdown-doc", CommentableMarkdown)
        md.highlight_range(message.block_start, message.block_end)
        self._sel_start = message.block_start
        self._sel_end = message.block_end

    # --- Reload ---

    def action_reload(self) -> None:
        self.source_text = self.file_path.read_text()
        md = self.query_one("#markdown-doc", CommentableMarkdown)
        md.update(self.source_text)
        self.notify("Reloaded.")

    # --- Keyboard navigation ---

    def action_move_up(self) -> None:
        md = self.query_one("#markdown-doc", CommentableMarkdown)
        md.move_up()

    def action_move_down(self) -> None:
        md = self.query_one("#markdown-doc", CommentableMarkdown)
        md.move_down()

    def action_extend_up(self) -> None:
        md = self.query_one("#markdown-doc", CommentableMarkdown)
        md.extend_up()

    def action_extend_down(self) -> None:
        md = self.query_one("#markdown-doc", CommentableMarkdown)
        md.extend_down()

    # --- Helpers ---

    def _find_comment(self, comment_id: str) -> Comment | None:
        for c in self.comments:
            if c.id == comment_id:
                return c
        return None
