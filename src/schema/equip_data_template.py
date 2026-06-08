from pathlib import Path

from .. import ModelReader, SchemaModel
from ..exceptions import PositionNotFound
from ..types import NotRequired, Vector2


def _extract_item(reader: ModelReader["EquipDataTemplate"], key: str) -> list[Vector2[int]]:
  reader.set_position(key)
  result: list[Vector2[int]] = []

  while reader.peek(2) == b"\x01\x00":
    result.insert(0, reader.get_value_by_type(Vector2[int]))

  return result


class EquipDataTemplate(SchemaModel):
  id: int
  prev: int
  next: int
  type: NotRequired[int]
  base: NotRequired[int]
  level: int
  group: NotRequired[int]
  important: NotRequired[int]
  equip_limit: NotRequired[int]
  restore_gold: int
  restore_item: list[Vector2[int]]
  destory_gold: int
  destory_item: list[Vector2[int]]
  trans_use_gold: int
  trans_use_item: list[Vector2[int]]
  upgrade_formula_id: NotRequired[list[int]]
  ship_type_forbidden: NotRequired[list[int]]

  @staticmethod
  def extract_restore_item(reader: ModelReader["EquipDataTemplate"]) -> list[Vector2[int]]:
    return _extract_item(reader=reader, key="restore_item")

  @staticmethod
  def extract_destory_item(reader: ModelReader["EquipDataTemplate"]) -> list[Vector2[int]]:
    return _extract_item(reader=reader, key="destory_item")

  @staticmethod
  def extract_trans_use_item(reader: ModelReader["EquipDataTemplate"]) -> list[Vector2[int]]:
    return _extract_item(reader=reader, key="trans_use_item")

  @staticmethod
  def extract_upgrade_formula_id(
    reader: ModelReader["EquipDataTemplate"],
  ) -> NotRequired[list[int]]:
    try:
      reader.set_position("upgrade_formula_id")
    except PositionNotFound:
      return NotRequired()  # pyright: ignore[reportReturnType]

    if reader.peek(2) != b"\x01\x00":
      return NotRequired([])

    return NotRequired(reader.get_value_by_type(list[int]))


def equip_data_template(source: Path, output: Path) -> dict[str, EquipDataTemplate]:
  reader = ModelReader(source, EquipDataTemplate, "id")
  return reader.write(output)
