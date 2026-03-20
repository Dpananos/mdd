from __future__ import annotations

import asyncio
import json
import re
import shutil

from ..models import DiffProposal


def claude_available() -> bool:
    return shutil.which("claude") is not None


async def propose_edit(
    full_document: str,
    section_text: str,
    section_start_line: int,
    section_end_line: int,
    comment_text: str,
    session: str | None = None,
) -> DiffProposal:
    prompt = f"""You are reviewing a markdown document. A reviewer left a comment on a specific section.
Your job is to propose a concrete edit to the markdown that addresses their comment.

Rules:
1. Return ONLY the revised version of the section provided, not the entire document.
2. Preserve the original markdown formatting style.
3. Do not add explanatory text outside the structured response.

Here is the full markdown document for context:

<document>
{full_document}
</document>

Here is the specific section (lines {section_start_line + 1}-{section_end_line}) that the comment is about:

<section>
{section_text}
</section>

Here is the reviewer's comment:

<comment>
{comment_text}
</comment>

Respond in this exact format:

<explanation>
Brief explanation of what you changed and why.
</explanation>

<revised>
The revised markdown section goes here.
</revised>"""

    args = ["claude"]
    if session:
        args += ["-r", session]
    else:
        args += ["-c"]  # continue most recent conversation
    args += ["-p", prompt, "--output-format", "json"]

    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

    # Fallback: if -c failed (no recent session), retry without it
    if proc.returncode != 0 and not session:
        fallback_args = ["claude", "-p", prompt, "--output-format", "json"]
        proc = await asyncio.create_subprocess_exec(
            *fallback_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

    if proc.returncode != 0:
        error_msg = stderr.decode().strip() if stderr else "Unknown error"
        raise RuntimeError(f"Claude Code failed (exit {proc.returncode}): {error_msg}")

    # Parse JSON output from claude --output-format json
    raw = stdout.decode()
    try:
        data = json.loads(raw)
        response_text = data.get("result", raw)
    except json.JSONDecodeError:
        response_text = raw

    explanation = _extract_tag(response_text, "explanation")
    revised = _extract_tag(response_text, "revised")

    # Build full proposed document by splicing
    doc_lines = full_document.splitlines(keepends=True)
    revised_lines = revised.splitlines(keepends=True)
    # Ensure revised ends with newline if original section did
    if doc_lines and section_end_line <= len(doc_lines):
        proposed_doc_lines = (
            doc_lines[:section_start_line]
            + revised_lines
            + doc_lines[section_end_line:]
        )
    else:
        proposed_doc_lines = doc_lines[:section_start_line] + revised_lines

    full_proposed_doc = "".join(proposed_doc_lines)

    return DiffProposal(
        original_lines=section_text,
        proposed_lines=revised,
        full_original_doc=full_document,
        full_proposed_doc=full_proposed_doc,
        explanation=explanation,
    )


def _extract_tag(text: str, tag: str) -> str:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else text
