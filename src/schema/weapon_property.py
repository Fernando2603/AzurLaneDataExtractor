from pathlib import Path

from .. import ModelReader, SchemaModel
from ..exceptions import PositionNotFound
from ..types import EmptyString, NotRequired


def _extract_optional_float(reader: ModelReader["WeaponProperty"], key: str) -> NotRequired[float]:
  try:
    reader.set_position(key)
  except PositionNotFound:
    return NotRequired()  # pyright: ignore[reportReturnType]

  if reader.peek(1) not in b"\x03\x04":
    return NotRequired(0.0)

  return NotRequired(float(reader.get_value_by_type(int | float)))


def _extract_optional_model[T: SchemaModel](
  reader: ModelReader["WeaponProperty"],
  key: str,
  model: type[T],
) -> NotRequired[T | EmptyString]:
  try:
    reader.set_position(key)
  except PositionNotFound:
    return NotRequired()  # pyright: ignore[reportReturnType]

  tag = reader.peek(1)

  if tag in b"\x05\x06":  # handle "" and " "
    return NotRequired(EmptyString())

  result: dict[str, bool | int | float | str] = {}

  if tag == b"\x01":
    result = reader.get_value_by_type(dict[str, bool | int | float | str])

  return NotRequired(model.model_validate(result, strict=True))


class WeaponPropertyChargeParam(SchemaModel, extra="allow"):
  fx: NotRequired[str]
  armor: NotRequired[int]
  time: NotRequired[int]
  isBound: NotRequired[bool]
  maxLock: NotRequired[int]
  lockTime: NotRequired[float]


class WeaponPropertyPrecastParam(SchemaModel, extra="allow"):
  fx: NotRequired[str]
  armor: NotRequired[int]
  time: NotRequired[float]
  isBound: NotRequired[bool]
  alertTime: NotRequired[float]


class WeaponProperty(SchemaModel):
  id: int
  base: NotRequired[int]
  type: NotRequired[int]
  damage: NotRequired[int]
  attack_attribute: NotRequired[int]
  attack_attribute_ratio: NotRequired[int]
  reload_max: NotRequired[int]
  aim_type: NotRequired[int]
  oxy_type: NotRequired[list[int]]
  search_type: NotRequired[int]
  torpedo_ammo: NotRequired[int]
  min_range: NotRequired[int]
  range: NotRequired[int]
  angle: NotRequired[int]
  axis_angle: NotRequired[int]
  queue: NotRequired[int]
  recover_time: NotRequired[float]
  initial_over_heat: NotRequired[int]
  expose: NotRequired[int]
  suppress: NotRequired[int]
  corrected: NotRequired[int]
  effect_move: NotRequired[int]
  action_index: NotRequired[str]
  shakescreen: NotRequired[int]
  fire_sfx: NotRequired[str]
  fire_fx: NotRequired[str]
  fire_fx_loop_type: NotRequired[int]
  barrage_ID: NotRequired[list[int]]
  bullet_ID: NotRequired[list[int]]
  auto_aftercast: NotRequired[float]
  search_condition: NotRequired[list[int] | EmptyString]
  spawn_bound: NotRequired[list[int] | str]
  charge_param: NotRequired[WeaponPropertyChargeParam | EmptyString]
  precast_param: NotRequired[WeaponPropertyPrecastParam | EmptyString]

  @staticmethod
  def extract_auto_aftercast(reader: ModelReader["WeaponProperty"]) -> NotRequired[float]:
    return _extract_optional_float(reader=reader, key="auto_aftercast")

  @staticmethod
  def extract_recover_time(reader: ModelReader["WeaponProperty"]) -> NotRequired[float]:
    return _extract_optional_float(reader=reader, key="recover_time")

  @staticmethod
  def extract_barrage_ID(reader: ModelReader["WeaponProperty"]) -> NotRequired[list[int]]:
    try:
      reader.set_position("barrage_ID")
    except PositionNotFound:
      return NotRequired()  # pyright: ignore[reportReturnType]

    result: list[int] = []

    if reader.peek(2) == b"\x01\x00":
      result = reader.get_value_by_type(list[int])

    return NotRequired(result)

  @staticmethod
  def extract_charge_param(
    reader: ModelReader["WeaponProperty"],
  ) -> NotRequired[WeaponPropertyChargeParam | EmptyString]:
    return _extract_optional_model(
      reader=reader,
      key="charge_param",
      model=WeaponPropertyChargeParam,
    )

  @staticmethod
  def extract_precast_param(
    reader: ModelReader["WeaponProperty"],
  ) -> NotRequired[WeaponPropertyPrecastParam | EmptyString]:
    return _extract_optional_model(
      reader=reader,
      key="precast_param",
      model=WeaponPropertyPrecastParam,
    )

  @staticmethod
  def after_lock_next(reader: ModelReader["WeaponProperty"], result: bool) -> bool:
    try:
      reader.set_position(reader.primary)
    except PositionNotFound:
      return False

    return result


def weapon_property(source: Path, output: Path) -> dict[str, WeaponProperty]:
  reader = ModelReader(source, WeaponProperty, "id")

  return reader.write(output)
