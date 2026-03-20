from __future__ import annotations

import difflib

from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, RichLog, Static

from ..models import DiffProposal


class DiffViewScreen(ModalScreen[bool]):
    """Shows a diff and lets the user accept or reject it."""

    BINDINGS = [
        Binding("a", "accept", "Accept"),
        Binding("r", "reject", "Reject"),
        Binding("escape", "reject", "Reject"),
    ]

    def __init__(self, proposal: DiffProposal, name: str | None = None) -> None:
        super().__init__(name=name)
        self.proposal = proposal

    def compose(self) -> ComposeResult:
        with Vertical(id="diff-dialog"):
            yield Static("Proposed Changes", classes="dialog-title")
            yield Static(self.proposal.explanation, classes="explanation")
            yield RichLog(id="diff-display", wrap=True)
            with Horizontal(classes="dialog-buttons"):
                yield Button("Reject (r)", variant="error", id="reject")
                yield Button("Accept (a)", variant="success", id="accept")

    def on_mount(self) -> None:
        diff_lines = difflib.unified_diff(
            self.proposal.original_lines.splitlines(keepends=True),
            self.proposal.proposed_lines.splitlines(keepends=True),
            fromfile="original",
            tofile="proposed",
        )
        diff_text = "".join(diff_lines)
        if not diff_text:
            diff_text = "(no changes)"

        log = self.query_one("#diff-display", RichLog)
        syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
        log.write(syntax)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "accept")

    def action_accept(self) -> None:
        self.dismiss(True)

    def action_reject(self) -> None:
        self.dismiss(False)
