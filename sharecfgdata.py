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
    target = [src]

    if not src.exists():
      print(f"[SKIP]: {src.as_posix()} not found.")
      continue

    for i in range(1, 4):
      if (x := src.with_name(f"{name}_{i}")).exists():
        target.append(x)

    for file in target:
      dst = (output / file.name).with_suffix(".json")
      function(file, dst)
      print(f"[WRITE]: {dst.as_posix()}")


if __name__ == "__main__":
  sharecfgdata(
    source=Path(__file__).parent / "target/sharecfgdata",
    output=Path(__file__).parent / "build/sharecfgdata",
  )
