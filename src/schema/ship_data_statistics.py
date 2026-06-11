from pathlib import Path

from pydantic import Field

from .. import ModelReader, SchemaModel
from ..types import EmptyString, Vector2, Vector3


class ShipDataStatistics(SchemaModel):
  id: int
  type: int
  name: str
  english_name: str
  nationality: int
  armor_type: int
  rarity: int
  star: int
  ammo: int
  scale: int
  skin_id: int
  summon_offset: int
  backyard_speed: str
  attack_duration: int
  raid_distance: int
  oxy_max: int
  oxy_cost: int
  oxy_recovery: int
  oxy_recovery_bench: int
  oxy_recovery_surface: int
  attrs: list[int | float]
  attrs_growth: list[int | float]
  attrs_growth_extra: list[int | float]
  aim_offset: Vector3[int]
  base_list: Vector3[int]
  parallel_max: Vector3[int]
  preload_count: Vector3[int]
  equipment_proficiency: list[float | int]
  default_equip_list: list[int] = Field(default_factory=list)
  fix_equip_list: list[int] = Field(default_factory=list)
  depth_charge_list: list[int] = Field(default_factory=list)
  cld_box: Vector3[int]
  cld_offset: Vector3[int]
  huntingrange_level: int
  hunting_range: list[list[Vector2[int]]]
  strategy_list: list[Vector2[int]]
  position_offset: Vector3[int]
  lock: list[str] = Field(default_factory=list)
  tag_list: list[str] = Field(default_factory=list)
  gift_dislike: list[int] | EmptyString = Field(default_factory=list)

  @staticmethod
  def extract_strategy_list(reader: ModelReader["ShipDataStatistics"]) -> list[Vector2[int]]:
    reader.set_position("strategy_list")

    if reader.peek(1) != b"\x01":
      return []

    result: list[Vector2[int]] = []

    while reader.peek(4) == b"\x01\x00\x03\x00":
      result.append(reader.get_value_by_type(expect=Vector2[int]))

    return result

  @staticmethod
  def extract_hunting_range(reader: ModelReader["ShipDataStatistics"]) -> list[list[Vector2[int]]]:
    reader.set_position("hunting_range")

    if reader.peek(1) != b"\x01":
      return [[]]

    result: list[Vector2[int]] = []

    while reader.peek(4) == b"\x01\x00\x03\x00":
      result.append(reader.get_value_by_type(expect=Vector2[int]))

    output: list[list[Vector2[int]]] = []

    # opcodes by observing behaviour of the byte
    # 0x4C == TSETM | A-1<BASE>[D&0xFFFFFFFF<NUM>] <- A (<- multres)
    # 0x4D == TGET variant | ABC
    # 0x57 == TSET variant? act more like insert(0x4C Address, index, end address)
    for x in reader.find_all(b"\x4c\xfb", start=0, end=reader.constant_position):
      reader.position = x
      reader.seek(2)

      length = reader.read_int(tag=b"") - 1 # A-1<BASE>
      output.append([result.pop() for _ in range(length)])

    return output


def ship_data_statistics(source: Path, output: Path) -> dict[str, ShipDataStatistics]:
  reader = ModelReader(source, ShipDataStatistics, "id")
  return reader.write(output)
