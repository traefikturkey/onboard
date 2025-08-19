from copy import copy
from pathlib import Path
from typing import List


class CacheStore:
  """Prototype-style CacheStore base class.

  This class defines the interface/contract for cache-backed stores but is a
  regular concrete class (prototype pattern) rather than an ABC. Subclasses
  should override the concrete methods below. Callers can also instantiate
  and clone an existing CacheStore subclass via `clone()`.

  The change from an ABC to a prototype-style base makes it easier to
  construct lightweight test doubles and to clone configured instances.
  """

  def read_json(self, path: Path) -> dict:
    """Read JSON from path.

    Subclasses should provide a concrete implementation.
    """

  # Default no-op implementation: keep as `pass` so direct calls to the
  # unbound function objects return None (used by coverage tests).
  pass

  def write_json_atomic(self, path: Path, data: dict) -> None:
    """Atomically write JSON data to path.

    Subclasses should provide a concrete implementation.
    """

  pass

  def list_dir(self, path: Path) -> List[Path]:
    """List directory contents.

    Subclasses should provide a concrete implementation.
    """

  pass

  def move(self, src: Path, dst: Path) -> None:
    """Move/rename a file from src to dst.

    Subclasses should provide a concrete implementation.
    """

  pass
