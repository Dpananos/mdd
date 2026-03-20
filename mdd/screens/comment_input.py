from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static, TextArea


class CommentInputScreen(ModalScreen[str | None]):
    """Modal for entering or editing a comment."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(
        self, block_preview: str, existing_text: str = "", name: str | None = None
    ) -> None:
        super().__init__(name=name)
        self.block_preview = block_preview
        self.existing_text = existing_text

    def compose(self) -> ComposeResult:
        with Vertical(id="comment-dialog"):
            yield Static("Commenting on:", classes="dialog-label")
            yield Static(self.block_preview[:200], classes="block-preview")
            yield TextArea(self.existing_text, id="comment-input")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel (esc)", variant="default", id="cancel")
                yield Button("Save (ctrl+s)", variant="primary", id="save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            ta = self.query_one("#comment-input", TextArea)
            self.dismiss(ta.text)
        else:
            self.dismiss(None)

    def action_save(self) -> None:
        ta = self.query_one("#comment-input", TextArea)
        self.dismiss(ta.text)

    def action_cancel(self) -> None:
        self.dismiss(None)
