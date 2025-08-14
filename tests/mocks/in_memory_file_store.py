import json
from pathlib import Path
from typing import Dict, List

from app.models.file_store import CacheStore


class InMemoryFileStore(CacheStore):
    """In-memory FileStore for unit tests.

    Simulates files in memory. Supports configurable content and size to test
    archive behavior and corrupt JSON handling.
    """

    def __init__(self) -> None:
        self.files: Dict[Path, str] = {}

    def read_json(self, path: Path) -> dict:
        if path not in self.files:
            raise FileNotFoundError(path)
        data = self.files[path]
        return json.loads(data)

    def write_json_atomic(self, path: Path, data: dict) -> None:
        txt = json.dumps(data)
        # Simulate atomic write by writing to a temp path then moving
        tmp = Path(str(path) + ".tmp")
        self.files[tmp] = txt
        # replace
        if tmp in self.files:
            self.files[path] = self.files[tmp]
            del self.files[tmp]

    def list_dir(self, path: Path) -> List[Path]:
        prefix = str(path).rstrip("/") + "/"
        return [p for p in self.files.keys() if str(p).startswith(prefix)]

    def move(self, src: Path, dst: Path) -> None:
        if src not in self.files:
            raise FileNotFoundError(src)
        self.files[dst] = self.files[src]
        del self.files[src]

    # Helpers for tests
    def create_file(self, path: Path, content: str) -> None:
        self.files[path] = content

    def file_size(self, path: Path) -> int:
        return len(self.files.get(path, ""))
