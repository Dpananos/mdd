# mdd

Terminal markdown reviewer with AI-powered editing. Think Google Docs comments, but in your terminal, with Claude doing the edits.

## Install

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Dpananos/mdd.git
cd mdd
uv sync
```

For AI-powered edits, you also need [Claude Code](https://claude.ai/code) on your PATH.

## Usage

```bash
uv run python main.py <file.md>
```

To resume a specific Claude Code session:

```bash
uv run python main.py <file.md> --session <session-id>
```

## Workflow

1. **Select a section** -- Click a block of text, or use `Shift+Up` / `Shift+Down` to extend across multiple blocks
2. **Leave a comment** -- Press `c`, type your feedback, `Ctrl+S` to save
3. **Send to Claude** -- Click "Send to Claude" on any comment card. Claude proposes a concrete edit to the section based on your comment
4. **Review the diff** -- Press `a` to accept (written to disk immediately) or `r` to reject
5. **Iterate** -- Rejected comments can be edited and re-sent. Accepted edits remap all other comments to their new line positions

Comments are persisted to a sidecar `.mdd.json` file so they survive between sessions.

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `c` | Comment on selected block(s) |
| `r` | Reload document from disk |
| `q` | Quit |
| `Up` / `Down` | Move block selection |
| `Shift+Up` / `Shift+Down` | Extend block selection |
| `Ctrl+S` | Save (in comment modal) |
| `Escape` | Cancel / close modal |
| `a` / `r` | Accept / reject diff |
