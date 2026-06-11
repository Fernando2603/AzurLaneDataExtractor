import json
import shutil
from pathlib import Path
from typing import Any

BUILD = Path(__file__).parent / "build"


def merge_gamecfg_buff() -> None:
  src = BUILD / "gamecfg/buff"
  dst = BUILD / "gamecfg/buff.json"

  if not src.exists():
    return

  result: dict[str, Any] = {}

  for file in src.glob("*.json"):
    if not file.stem.startswith("buff_"):
      continue

    key = file.stem[5:]
    result[key] = json.loads(file.read_text(encoding="utf-8"))

  dst.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
  print(f"[WRITE]: {dst.as_posix()}")

  shutil.rmtree(src)
  print(f"[DELETE]: {src.as_posix()}")


def update_version() -> None:
  src = Path(__file__).parent / "target/version.txt"

  if src.exists():
    (BUILD / "version.txt").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
  merge_gamecfg_buff()
  update_version()
