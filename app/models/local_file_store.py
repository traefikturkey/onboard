import json
import shutil
from pathlib import Path
from typing import List

from .file_store import FileStore


class LocalFileStore(FileStore):
    """Filesystem-backed FileStore using real file IO operations."""

    def read_json(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_json_atomic(self, path: Path, data: dict) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        # os.replace or Path.replace is atomic on POSIX
        tmp.replace(path)

    def list_dir(self, path: Path) -> List[Path]:
        if not path.exists():
            return []
        return [p for p in path.iterdir()]

    def move(self, src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
