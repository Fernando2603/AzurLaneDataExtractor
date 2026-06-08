import importlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

SCHEMA: dict[str, Callable[[Path, Path], Any]] = {}

for file in (Path(__file__).parent / "src/schema").glob("*.py"):
  if file.stem.startswith("_"):
    continue

  module = importlib.import_module(f"src.schema.{file.stem}")

  if hasattr(module, file.stem):
    SCHEMA[file.stem] = getattr(module, file.stem)


def sharecfgdata(source: Path, output: Path) -> None:
  for name, function in SCHEMA.items():
    src = source / name
    dst = (output / name).with_suffix(".json")

    if not src.exists():
      print(f"[SKIP]: {src.as_posix()} not found.")
      continue

    function(src, dst)
    print(f"[WRITE]: {dst.as_posix()}")


if __name__ == "__main__":
  sharecfgdata(
    source=Path(__file__).parent / "target/sharecfgdata",
    output=Path(__file__).parent / "build/sharecfgdata",
  )
