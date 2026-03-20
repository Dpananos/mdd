from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CommentStatus(Enum):
    OPEN = "open"
    PENDING_REVIEW = "pending_review"
    COMPLETE = "complete"
    REJECTED = "rejected"


@dataclass
class DiffProposal:
    original_lines: str
    proposed_lines: str
    full_original_doc: str
    full_proposed_doc: str
    explanation: str


@dataclass
class Comment:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    block_index: int = 0  # first block in the selection
    block_end: int = 0  # last block in the selection (inclusive)
    source_start: int = 0
    source_end: int = 0
    anchor_text: str = ""
    body: str = ""
    status: CommentStatus = CommentStatus.OPEN
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    diff_proposal: DiffProposal | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "block_index": self.block_index,
            "block_end": self.block_end,
            "source_start": self.source_start,
            "source_end": self.source_end,
            "anchor_text": self.anchor_text,
            "body": self.body,
            "status": self.status.value,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Comment:
        block_index = d.get("block_index", 0)
        return cls(
            id=d["id"],
            block_index=block_index,
            block_end=d.get("block_end", block_index),
            source_start=d.get("source_start", 0),
            source_end=d.get("source_end", 0),
            anchor_text=d.get("anchor_text", ""),
            body=d.get("body", ""),
            status=CommentStatus(d.get("status", "open")),
            created_at=d.get("created_at", ""),
        )
