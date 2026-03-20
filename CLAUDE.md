# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is mdd?

A terminal-based markdown document reviewer with AI-powered editing. Users open a `.md` file, select blocks, leave comments, and send them to Claude Code CLI for proposed edits shown as diffs.

## Commands

```bash
# Run the app
uv run python main.py <file.md>
uv run python main.py test_doc.md --session <session-id>  # resume a Claude session

# Install dependencies
uv sync
```

No tests or linting are configured yet.

## Architecture

```
main.py → MddApp (app.py) → Services + Widgets + Screens
```

**MddApp** is a Textual TUI app with a 70/30 split layout: markdown viewer (left) and comment panel (right).

**Services** (`mdd/services/`):
- `claude.py` — Spawns `claude` CLI as a subprocess, sends a structured prompt with document context + section + comment, parses `<explanation>` and `<revised>` tags from JSON output. Supports `-c` (continue session) and `-r` (resume specific session) with fallback to fresh conversation.
- `line_tracker.py` — `BlockLineTracker` maps rendered Textual markdown blocks to source line ranges. After an edit is accepted, `remap_after_edit()` shifts line numbers on all other comments and `reconcile_comments()` uses `SequenceMatcher` fuzzy matching to re-anchor comments whose blocks moved.
- `persistence.py` — Saves/loads comments to a `.{filename}.mdd.json` sidecar file alongside the document.

**Screens** (`mdd/screens/`) — Modal dialogs: `CommentInputScreen` (write/edit comment), `DiffViewScreen` (accept/reject proposed diff), `ConfirmDeleteScreen`.

**Widgets** (`mdd/widgets/`):
- `CommentableMarkdown` — Extends Textual's Markdown widget with block click selection, multi-block range selection (shift+arrow), and visual highlighting for selected/commented blocks.
- `CommentPanel` / `CommentCard` — Right sidebar listing comments with status badges and action buttons. Cards emit `Message` subclasses (`DeleteRequested`, `SendToClaudeRequested`, etc.) that `MddApp` handles.

**Models** (`mdd/models.py`): `Comment` (dataclass with block indices, source line range, status), `CommentStatus` (OPEN → PENDING_REVIEW → COMPLETE/REJECTED), `DiffProposal`.

## Key patterns

- Inter-widget communication uses Textual's `Message` class, not direct method calls
- Background work (Claude calls) uses `@work(exclusive=True, thread=False)` async decorator
- Styling is in `mdd/styles/app.tcss` (Textual CSS) with a custom "synthwave" theme registered in `app.py`
- All type hints use `from __future__ import annotations` for forward references

## Keyboard shortcuts

- `q` — Quit
- `c` — Add comment on selected block(s)
- `r` — Reload document from disk
- `up/down` — Move block selection
- `shift+up/down` — Extend block selection
- `ctrl+s` — Save comment (in comment modal)
- `escape` — Cancel/close modal
- `a` / `r` — Accept/reject diff (in diff view)
