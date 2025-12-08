import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import List

from .file_store import CacheStore


class LocalFileStore(CacheStore):
    """Filesystem-backed CacheStore using real file IO operations."""

    def read_json(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_json_atomic(self, path: Path, data: dict) -> None:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Use tempfile.NamedTemporaryFile for safer temp file handling
        # Create in same directory to ensure atomic rename works
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
        ) as tmp:
            json.dump(data, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)

        # Atomic replace (POSIX guarantees atomicity)
        os.replace(tmp_path, path)

    def list_dir(self, path: Path) -> List[Path]:
        if not path.exists():
            return []
        return [p for p in path.iterdir()]

    def move(self, src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
