import json
import re
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import lupa

GLUA = lupa.LuaRuntime(unpack_returned_tuples=True)
_get_defined_line = cast(
  Callable[[Any], tuple[int, int]],
  GLUA.eval("""
  function(f)
    local info = debug.getinfo(f)
    return info.linedefined - 1, info.lastlinedefined
  end
"""),
)


def parse_table(obj: Any, source: str, root: bool = False) -> Any:
  if lupa.lua_type(obj) == "function":
    start, end = _get_defined_line(obj)
    value = textwrap.dedent("\n".join(source.splitlines()[start:end]))
    # its a bit different from AzurLaneTools/AzurLaneData but lupa or normal lua
    # is able to call this via eval or execute
    return f"-- lua function:\n{value}"

  if not hasattr(obj, "keys"):
    return obj

  keys = list(obj.keys())

  if (
    not root
    and all(isinstance(k, int) for k in keys)
    and (sorted(keys) == list(range(1, len(keys) + 1)))
  ):
    return [parse_table(obj[i], source) for i in range(1, len(keys) + 1)]

  return {str(k): parse_table(obj[k], source) for k in keys}


def parse_lua(src: Path) -> Any:
  source = src.read_text(encoding="utf-8-sig")
  return parse_table(GLUA.execute(source), source)


def parse_buff(src: Path) -> Any:
  source = src.read_text(encoding="utf-8-sig")

  # easy fix
  if (st := "ShipType.MainShipType") in source:
    source = source.replace(st, "main")

  if (st := "ShipType.VanguardShipType") in source:
    source = source.replace(st, "vanguard")

  if (st := "ShipType.SubShipType") in source:
    source = source.replace(st, "submarine")

  return parse_table(GLUA.execute(source), source)


def lua2json(src: Path, dst: Path) -> Any:
  # non-sharing runtime gonna make it easier to implement multi-thread later
  lua = lupa.LuaRuntime(unpack_returned_tuples=True)

  # make it easier to use getattr
  script = src.read_text(encoding="utf-8-sig")

  if script.startswith("return"):
    data = parse_table(lua.execute(script), script, True)
  else:
    source = textwrap.dedent("""
      {script}
      pg = pg or {{}}
      pg.base = pg.base or {{}}
      pg.base.{name} = pg.base.{name} or {{}}
      cs = cs or {{}}
      cs.{name} = cs.{name} or {{}}
    """).format(name=src.stem, script=script)

    try:
      lua.execute(source)
    except lupa.LuaSyntaxError:
      # dot notation
      source = re.sub(r"\.([^\x00-\x7F]+)", r'["\1"]', source)

      # assignment
      source = re.sub(r"([^\x00-\x7F\s]+)(\s*=)", r'["\1"]\2', source)

      # hidden space
      source = re.sub(r" (\s*=)", r'[" "]\1', source)  # noqa: RUF001

      if src.stem == "child2_node":
        source = source.replace("﻿id", "id")

      if src.stem.startswith("word_template_"):
        source = re.sub(r"\n(\s*=)", r'["\1"] =', source)

      lua.execute(source)

    # can be improved.. but meh if it's working why not.
    lg = lua.globals()
    cs = getattr(lg.cs, src.stem)  # pyright: ignore
    pg = getattr(lg.pg, src.stem)  # pyright: ignore
    base = getattr(lg.pg.base, src.stem)  # pyright: ignore

    if len(list(base.keys())):
      table = base
    elif len(list(cs.keys())):
      table = cs
    else:
      table = pg

    data = parse_table(table, source, True)

    if hasattr(pg, "all") and (x := pg.all):
      keys = list(x.values())
      data = { str(k): data[str(k)] for k in keys }
      data["all"] = keys

  dst.parent.mkdir(parents=True, exist_ok=True)

  if dst.exists() and dst.is_dir():
    dst = dst / src.stem

  dst.with_suffix(".json").write_text(
    json.dumps(data, indent=2, ensure_ascii=False),
    encoding="utf-8",
  )

  return data
