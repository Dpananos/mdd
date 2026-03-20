from __future__ import annotations

import json
from pathlib import Path

from ..models import Comment


def sidecar_path(source_file: Path) -> Path:
    return source_file.parent / f".{source_file.name}.mdd.json"


def save_comments(source_file: Path, comments: list[Comment]) -> None:
    path = sidecar_path(source_file)
    data = {
        "version": 1,
        "source_file": str(source_file),
        "comments": [c.to_dict() for c in comments],
    }
    path.write_text(json.dumps(data, indent=2))


def load_comments(source_file: Path) -> list[Comment]:
    path = sidecar_path(source_file)
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return [Comment.from_dict(cd) for cd in data.get("comments", [])]
