from pathlib import Path

from .. import ModelReader, SchemaModel
from ..exceptions import PositionNotFound, TagError
from ..types import EmptyString, NotRequired, Vector3, Vector4


class AircraftTemplateBoundBone(SchemaModel, extra="allow"):
  weapon: list[Vector3[int | float]]


class AircraftTemplate(SchemaModel):
  id: int
  name: NotRequired[str]
  base: NotRequired[int]
  icon: NotRequired[str]
  type: NotRequired[int]
  nationality: NotRequired[int]
  weapon_ID: NotRequired[list[int]]
  model_ID: NotRequired[str]
  scale: NotRequired[int | float]
  accuracy: NotRequired[int]
  max_hp: NotRequired[int]
  attack_power: NotRequired[int]
  speed: NotRequired[int]
  crash_DMG: NotRequired[int]
  AP_growth: NotRequired[int]
  hp_growth: NotRequired[int]
  ACC_growth: NotRequired[int]
  spawn_brownian: NotRequired[int]
  dodge_limit: NotRequired[int | float]
  dodge: NotRequired[int | float]
  cld_box: NotRequired[Vector3[int]]
  cld_offset: NotRequired[Vector3[int]]
  position_offset: NotRequired[Vector3[int]]
  fx_container: NotRequired[Vector4[Vector3[int | float]]]
  bound_bone: NotRequired[AircraftTemplateBoundBone]
  funnel_behavior: NotRequired[dict[str, int | float] | EmptyString]

  @staticmethod
  def extract_weapon_ID(reader: ModelReader["AircraftTemplate"]) -> NotRequired[list[int]]:
    try:
      reader.set_position("weapon_ID")
    except PositionNotFound:
      return NotRequired()  # pyright: ignore[reportReturnType]

    if reader.peek(2) != b"\x01\x00":
      return NotRequired([])

    return NotRequired(reader.get_value_by_type(list[int]))

  @staticmethod
  def extract_fx_container(
    reader: ModelReader["AircraftTemplate"],
  ) -> NotRequired[Vector4[Vector3[int | float]]]:
    try:
      reader.set_position("fx_container")
    except PositionNotFound:
      return NotRequired()  # pyright: ignore[reportReturnType]

    if (b := reader.peek(1)) != b"\x01":
      raise TagError(b, b"\x01")

    result: list[Vector3[int | float]] = []

    while reader.peek(4) == b"\x01\x00\x04\x00":
      result.append(reader.get_value_by_type(Vector3[int | float]))

    result.reverse()
    return NotRequired(Vector4(result))

  @staticmethod
  def extract_bound_bone(
    reader: ModelReader["AircraftTemplate"],
  ) -> NotRequired[AircraftTemplateBoundBone]:
    try:
      reader.set_position("bound_bone")
    except PositionNotFound:
      return NotRequired()  # pyright: ignore[reportReturnType]

    result: dict[str, list[Vector3[int | float]]] = {}
    running = True

    while running:
      key = reader.read_string()

      if reader.peek(3) == b"\x01\x00\x00":
        reader.seek(3)
        running = False

      build: list[Vector3[int | float]] = []

      while True:
        b = reader.peek(4)

        if b == b"\x01\x00\x04\x00":
          build.insert(0, reader.get_value_by_type(Vector3[int | float]))
          continue

        break

      result[key] = build

    return NotRequired(AircraftTemplateBoundBone.model_validate(result, strict=True))

  @staticmethod
  def extract_funnel_behavior(
    reader: ModelReader["AircraftTemplate"],
  ) -> NotRequired[dict[str, int | float] | EmptyString]:
    try:
      reader.set_position("funnel_behavior")
    except PositionNotFound:
      return NotRequired()  # pyright: ignore[reportReturnType]

    if reader.peek(1) == b"\x05":
      return NotRequired(EmptyString())

    return NotRequired(reader.get_value_by_type(dict[str, int | float]))


def aircraft_template(source: Path, output: Path) -> dict[str, AircraftTemplate]:
  reader = ModelReader(source, AircraftTemplate, "id")
  return reader.write(output)
