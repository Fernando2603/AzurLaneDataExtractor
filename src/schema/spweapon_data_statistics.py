from pathlib import Path

from .. import ModelReader, SchemaModel
from ..exceptions import PositionNotFound
from ..types import IntegerBoolean, NotRequired, Vector2


def _extract_upgrade(
  reader: ModelReader["SpweaponDataStatistics"], key: str
) -> NotRequired[list[Vector2[int]]]:
  try:
    reader.set_position(key)
  except PositionNotFound:
    return NotRequired()  # pyright: ignore[reportReturnType]

  if reader.peek(2) != b"\x01\x00":
    return NotRequired([])

  result: list[Vector2[int]] = []

  while reader.peek(4) == b"\x01\x00\x03\x00":
    result.insert(0, reader.get_value_by_type(Vector2[int]))

  return NotRequired(result)


class SpweaponDataStatistics(SchemaModel):
  id: int
  upgrade_id: int
  level: int
  prev: int
  next: int
  name: NotRequired[str]
  icon: NotRequired[str]
  type: NotRequired[int]
  base: NotRequired[int]
  tech: NotRequired[int]
  rarity: NotRequired[int]
  descrip: NotRequired[str]
  value_1: NotRequired[int]
  value_2: NotRequired[int]
  value_1_random: NotRequired[int]
  value_2_random: NotRequired[int]
  attribute_1: NotRequired[str]
  attribute_2: NotRequired[str]
  unique: NotRequired[int]
  important: NotRequired[int]
  uncraftable: NotRequired[IntegerBoolean]
  effect_id: NotRequired[int]
  effect_id_display: NotRequired[int]
  usability: NotRequired[list[int]]
  label: NotRequired[list[str]]
  skill_upgrade: NotRequired[list[Vector2[int]]]
  hide_buff_upgrade: NotRequired[list[Vector2[int]]]

  @staticmethod
  def extract_label(reader: ModelReader["SpweaponDataStatistics"]) -> NotRequired[list[str]]:
    try:
      reader.set_position("label")
    except PositionNotFound:
      return NotRequired()  # pyright: ignore[reportReturnType]

    if reader.peek(2) != b"\x01\x00":
      return NotRequired([])

    return NotRequired(reader.get_value_by_type(list[str]))

  @staticmethod
  def extract_skill_upgrade(
    reader: ModelReader["SpweaponDataStatistics"],
  ) -> NotRequired[list[Vector2[int]]]:
    return _extract_upgrade(reader=reader, key="skill_upgrade")

  @staticmethod
  def extract_hide_buff_upgrade(
    reader: ModelReader["SpweaponDataStatistics"],
  ) -> NotRequired[list[Vector2[int]]]:
    return _extract_upgrade(reader=reader, key="hide_buff_upgrade")


def spweapon_data_statistics(source: Path, output: Path) -> dict[str, SpweaponDataStatistics]:
  reader = ModelReader(source, SpweaponDataStatistics, "id")
  return reader.write(output)
