from pathlib import Path
from typing import Any

from .. import ModelReader, SchemaModel
from ..exceptions import PositionNotFound
from ..types import NotRequired, Vector2


def _extract_skill_id(
  reader: ModelReader["EquipDataStatistics"],
  key: str,
) -> NotRequired[list[Vector2[int]]]:
  try:
    reader.set_position(key)
  except PositionNotFound:
    return NotRequired()  # pyright: ignore[reportReturnType]

  result: list[Vector2[int]] = []

  while reader.peek(2) == b"\x01\x00":
    result.insert(0, reader.get_value_by_type(Vector2[int]))

  return NotRequired(result)


def _extract_optional_array[T](
  reader: ModelReader["EquipDataStatistics"],
  key: str,
  expect: type[T],
) -> NotRequired[list[T]]:
  try:
    reader.set_position(key)
  except PositionNotFound:
    return NotRequired()  # pyright: ignore[reportReturnType]

  if reader.peek(2) == b"\x01\x00":
    return NotRequired(reader.get_value_by_type(list[expect]))

  return NotRequired([])


class EquipDataStatisticsEquipParameters(SchemaModel, extra="allow"):
  ambush_extra: NotRequired[int]
  avoid_extra: NotRequired[int]
  range: NotRequired[int]
  hunting_lv: NotRequired[int]


class EquipDataStatistics(SchemaModel):
  id: int
  name: NotRequired[str]
  base: NotRequired[int]
  type: NotRequired[int]
  icon: NotRequired[str]
  rarity: NotRequired[int]
  nationality: NotRequired[int]
  descrip: NotRequired[str]
  ammo: NotRequired[int]
  damage: NotRequired[str]
  value_1: NotRequired[str]
  value_2: NotRequired[int]
  value_3: NotRequired[int]
  attribute_1: NotRequired[str]
  attribute_2: NotRequired[str]
  attribute_3: NotRequired[str]
  torpedo_ammo: NotRequired[int]
  anti_siren: NotRequired[int]
  speciality: NotRequired[str]
  tech: NotRequired[int]
  skill_id: NotRequired[list[Vector2[int]]]
  hidden_skill_id: NotRequired[list[Vector2[int]]]
  ammo_info: NotRequired[list[Vector2[int]]]
  equip_info: NotRequired[list[int | Vector2[int]]]
  weapon_id: NotRequired[list[int]]
  ammo_icon: NotRequired[list[int]]
  part_main: NotRequired[list[int]]
  part_sub: NotRequired[list[int]]
  label: NotRequired[list[str]]
  property_rate: NotRequired[list[None]]
  equip_parameters: NotRequired[EquipDataStatisticsEquipParameters]

  @staticmethod
  def extract_skill_id(
    reader: ModelReader["EquipDataStatistics"],
  ) -> NotRequired[list[Vector2[int]]]:
    return _extract_skill_id(reader=reader, key="skill_id")

  @staticmethod
  def extract_hidden_skill_id(
    reader: ModelReader["EquipDataStatistics"],
  ) -> NotRequired[list[Vector2[int]]]:
    return _extract_skill_id(reader=reader, key="hidden_skill_id")

  @staticmethod
  def extract_ammo_info(
    reader: ModelReader["EquipDataStatistics"],
  ) -> NotRequired[list[Vector2[int]]]:
    return _extract_skill_id(reader=reader, key="ammo_info")

  @staticmethod
  def extract_equip_info(
    reader: ModelReader["EquipDataStatistics"],
  ) -> NotRequired[list[int | Vector2[int]]]:
    try:
      reader.set_position("equip_info")
    except PositionNotFound:
      return NotRequired()  # pyright: ignore[reportReturnType]

    result: list[list[int | None]] = []

    while reader.peek(2) == b"\x01\x00":
      result.insert(0, reader.get_value_by_type(list[int | None]))

    if len(result) == 1:
      if None in result[0]:
        raise ValueError("Unexpected value None in equip_info")

      return NotRequired(result[0])  # pyright: ignore[reportReturnType]

    # if multiple result is found, only one result can have None, and that is the main
    main: list[Any] = []
    sub: list[Any] = []

    for value in result:
      if (None not in value) and (len(value) == 2):
        sub.insert(0, value)
        continue

      if len(main):
        raise ValueError("Unexpected behaviour, found 2 main in equip_info")

      main.extend(value)

    # let parent model validator handle this
    output = [tuple(sub.pop()) if x is None else x for x in main]

    for x in sub:
      output.append(tuple(x))

    return NotRequired(output)  # pyright: ignore[reportReturnType]

  @staticmethod
  def extract_weapon_id(reader: ModelReader["EquipDataStatistics"]) -> NotRequired[list[int]]:
    return _extract_optional_array(reader=reader, key="weapon_id", expect=int)

  @staticmethod
  def extract_ammo_icon(reader: ModelReader["EquipDataStatistics"]) -> NotRequired[list[int]]:
    return _extract_optional_array(reader=reader, key="ammo_icon", expect=int)

  @staticmethod
  def extract_part_main(reader: ModelReader["EquipDataStatistics"]) -> NotRequired[list[int]]:
    return _extract_optional_array(reader=reader, key="part_main", expect=int)

  @staticmethod
  def extract_part_sub(reader: ModelReader["EquipDataStatistics"]) -> NotRequired[list[int]]:
    return _extract_optional_array(reader=reader, key="part_sub", expect=int)

  @staticmethod
  def extract_label(reader: ModelReader["EquipDataStatistics"]) -> NotRequired[list[str]]:
    return _extract_optional_array(reader=reader, key="label", expect=str)

  @staticmethod
  def extract_property_rate(reader: ModelReader["EquipDataStatistics"]) -> NotRequired[list[None]]:
    return _extract_optional_array(reader=reader, key="property_rate", expect=type(None))

  @staticmethod
  def extract_equip_parameters(
    reader: ModelReader["EquipDataStatistics"],
  ) -> NotRequired[EquipDataStatisticsEquipParameters]:
    try:
      reader.set_position("equip_parameters")
    except PositionNotFound:
      return NotRequired()  # pyright: ignore[reportReturnType]

    result: dict[str, int] = {}

    if reader.peek(1) == b"\x01":
      result = reader.get_value_by_type(dict[str, int])

    return NotRequired(EquipDataStatisticsEquipParameters.model_validate(result, strict=True))


def equip_data_statistics(source: Path, output: Path) -> dict[str, EquipDataStatistics]:
  reader = ModelReader(source, EquipDataStatistics, "id")
  return reader.write(output)
