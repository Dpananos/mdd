# Sample Document

A software engineer, a QA tester, and a product manager walk into a bar. The engineer says "it works on my machine," the QA tester says "but does it work on *every* machine?", and the product manager says "can we ship it yesterday?"

## How It Works

mdd brings Google Drive-style commenting to your terminal. Here's the workflow:

1. **Open a document** — Run `mdd <file.md>` to load any markdown file in a TUI with a document pane on the left and a comment panel on the right.
2. **Select a section** — Click on a block of text to highlight it. Use `Shift+Up` / `Shift+Down` to extend your selection across multiple blocks.
3. **Leave a comment** — Press `c` to open the comment modal, type your feedback, and hit `Ctrl+S` to save. Comments are persisted to a sidecar JSON file so they survive between sessions.
4. **Send to Claude** — Click "Send to Claude" on any comment card. mdd sends the document, the selected section, and your comment to Claude Code, which proposes a concrete edit.
5. **Review the diff** — A diff view appears showing exactly what Claude wants to change. Press `a` to accept the edit (it's written to disk immediately) or `r` to reject it.
6. **Iterate** — Rejected comments can be edited and re-sent. Accepted edits update the document in place and remap all other comments to their new line positions.

## Conclusion

Why do software engineers prefer dark mode? Because light attracts bugs.

Why do programmers always mix up Halloween and Christmas? Because Oct 31 == Dec 25.

A SQL query walks into a bar, sees two tables, and asks... "Can I JOIN you?"

There are only 10 types of people in the world: those who understand binary and those who don't.