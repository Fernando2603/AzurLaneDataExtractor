from pathlib import Path

from .. import ModelReader, SchemaModel
from ..types import NotRequired


class WeaponName(SchemaModel):
  id: int
  name: NotRequired[str]
  base: NotRequired[int]


def weapon_name(source: Path, output: Path) -> dict[str, WeaponName]:
  reader = ModelReader(source, WeaponName, "id")
  return reader.write(output)
