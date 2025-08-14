from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class FileStore(ABC):
    """Abstract file store used for reading/writing/moving JSON files.

    Implementations may interact with the real filesystem or provide an
    in-memory simulation for unit tests.
    """

    @abstractmethod
    def read_json(self, path: Path) -> dict:
        pass

    @abstractmethod
    def write_json_atomic(self, path: Path, data: dict) -> None:
        pass

    @abstractmethod
    def list_dir(self, path: Path) -> List[Path]:
        pass

    @abstractmethod
    def move(self, src: Path, dst: Path) -> None:
        pass
