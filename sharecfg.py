import hashlib
import json
import subprocess
from pathlib import Path
from typing import cast

import UnityPy
from UnityPy.classes import TextAsset

from src.lua2json import lua2json, parse_buff

UABDEC = "bin/uabdec.exe"
BCDEC = "bin/bcdec.exe"
LJDEC = "bin/ljdec.exe"


def decompile_scripts32(src: Path, dst: Path) -> None:
  if not src.exists():
    raise FileNotFoundError(src.as_posix())

  dst.parent.mkdir(parents=True, exist_ok=True)
  subprocess.run([UABDEC, src.as_posix(), dst.as_posix()])


def unpack_scripts32(src: Path, dst: Path) -> set[str]:
  if not src.exists():
    raise FileNotFoundError(src.as_posix())

  dst.mkdir(parents=True, exist_ok=True)
  asset = UnityPy.load(src.as_posix())  # pyright: ignore[reportUnknownMemberType]

  cache: dict[str, str] = {}
  cache_path = Path(__file__).parent / "scripts32.json"

  changed: set[str] = set()
  checked: set[str] = set()
  relative = Path("assets/luabuilds/android/normal")

  if cache_path.exists():
    cache = json.loads(cache_path.read_bytes())

  for obj in asset.objects:
    if obj.type.name != "TextAsset":
      continue

    path = Path(cast(str, obj.container)).relative_to(relative)

    # filter unwanted asset
    if not path.is_relative_to("gamecfg/buff") and not path.is_relative_to("sharecfg"):
      continue

    data = cast(TextAsset, obj.read())
    path = path.with_name(data.name)
    script = cast(memoryview, data.m_Script)
    checksum = hashlib.sha256(script).hexdigest()
    posix_path = path.as_posix()

    checked.add(posix_path)

    if cache.get(posix_path) == checksum:
      continue

    cache[posix_path] = checksum

    fullpath = dst / path
    fullpath.parent.mkdir(parents=True, exist_ok=True)
    fullpath.write_bytes(script)
    changed.add(posix_path)

  for removed in set(cache.keys()) - checked:
    # keeping the json from build is okay i guess
    # since it doesn't have any impact even on buff
    del cache[removed]

  # make git tracking easier with sort_keys
  cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")
  return changed


def decompile_bytecode(src: Path, dst: Path) -> None:
  if not src.exists():
    raise FileNotFoundError(src.as_posix())

  dst.mkdir(parents=True, exist_ok=True)
  subprocess.run(
    [BCDEC, src.as_posix(), dst.as_posix()],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )

  for root, dirs, _ in src.walk():
    for directory in dirs:
      source = root / directory
      target = dst / root.relative_to(src) / directory

      target.mkdir(parents=True, exist_ok=True)
      subprocess.run(
        [BCDEC, source.as_posix(), target.as_posix()],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
      )


def decompile_luajit(src: Path, dst: Path) -> None:
  if not src.exists():
    raise FileNotFoundError(src.as_posix())

  dst.mkdir(parents=True, exist_ok=True)
  subprocess.run([LJDEC, src.as_posix(), "-o", dst.as_posix(), "-f", "-s"])


def extract_lua_to_json(src: Path, dst: Path) -> None:
  if not src.exists():
    raise FileNotFoundError(src.as_posix())

  dst.mkdir(parents=True, exist_ok=True)
  buff = src / "gamecfg/buff"

  for path in src.rglob("*.lua"):
    output = dst / path.relative_to(src).with_suffix(".json")
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
      if path.is_relative_to(buff):
        output.write_text(
          json.dumps(parse_buff(path), indent=2, ensure_ascii=False),
          encoding="utf-8",
        )

        continue

      lua2json(path, output)

    except Exception as e:
      print(f"{output.as_posix()}: {e}")


if __name__ == "__main__":
  parent = Path(__file__).parent / "scripts32"
  parent.mkdir(parents=True, exist_ok=True)

  target = Path(__file__).parent / "target/scripts32"
  build_path = Path(__file__).parent / "build"
  bundle_path = parent / "scripts32"
  bytecode_path = parent / "bytecode"
  luajit_path = parent / "luajit"
  lua_path = parent / "lua"

  # can be boosted via multiprocessing, for now this is enough
  decompile_scripts32(target, bundle_path)
  unpack_scripts32(bundle_path, bytecode_path)
  decompile_bytecode(bytecode_path, luajit_path)
  decompile_luajit(luajit_path, lua_path)
  extract_lua_to_json(lua_path, build_path)
