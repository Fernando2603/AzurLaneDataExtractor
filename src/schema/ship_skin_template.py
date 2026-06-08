from pathlib import Path

from .. import ModelReader, SchemaModel
from ..exceptions import TagError
from ..types import EmptyString, IntegerBoolean, NotRequired, Vector2, Vector3, Vector4


class ShipSkinTemplateBoundBone(SchemaModel):
  vicegun: NotRequired[list[Vector2[int | float] | Vector3[int | float]]]
  cannon: NotRequired[list[Vector2[int | float] | Vector3[int | float]]]
  antiaircraft: NotRequired[list[Vector2[int | float] | Vector3[int | float]]]
  torpedo: NotRequired[list[Vector2[int | float] | Vector3[int | float]]]
  plane: NotRequired[list[Vector2[int | float] | Vector3[int | float]]]
  remote: NotRequired[Vector3[int | float]]


class ShipSkinTemplateGetShowing(SchemaModel):
  show: IntegerBoolean
  paint_offset: NotRequired[Vector3[int | float]]
  data: list[
    tuple[
      int | float,
      int | float,
      int | float,
      int | float,
      int | float,
      int | float,
    ]
  ]


class ShipSkinTemplate(SchemaModel):
  id: int
  name: str
  desc: str
  group_index: int
  ship_group: int
  skin_type: int
  painting: str
  prefab: str
  bg: str
  bg_sp: str
  rarity_bg: str
  bgm: str
  illustrator: int
  illustrator2: int
  voice_actor: int
  voice_actor_2: int
  tag: list[int]

  # misc
  shop_offset: list[int | float] | EmptyString
  purchase_offset: list[int | float] | EmptyString
  spine_offset: list[int | float] | EmptyString
  spine_offset_profile: list[int | float] | EmptyString
  spine_action_offset: bool | EmptyString
  live2d_offset: list[int | float]
  live2d_offset_profile: list[int | float] | EmptyString
  smoke: list[tuple[int, list[tuple[str, Vector3[int | float]]]]]
  bound_bone: ShipSkinTemplateBoundBone
  change_skin: dict[str, int | float | str] | str
  fx_container: Vector4[Vector3[int | float]]
  special_effects: tuple[str, Vector3[int | float], tuple[int | float]] | EmptyString
  get_showing: ShipSkinTemplateGetShowing | EmptyString

  ship_l2d_id: list[int] | EmptyString
  l2d_animations: list[str] | EmptyString
  l2d_drag_rate: list[int | float] | EmptyString
  l2d_ignore_drag: int
  l2d_voice_calibrate: dict[str, int | float | bool] | EmptyString
  l2d_se: dict[str, tuple[str, float]] | EmptyString
  l2d_para_range: dict[str, Vector2[int | float]] | EmptyString
  spine_use_live2d: IntegerBoolean
  lip_sync_gain: int
  lip_smoothing: int
  gyro: IntegerBoolean

  shop_type_id: int
  hand_id: int
  lover_kiss: str
  shop_id: int
  main_UI_FX: str
  skeleton_default_skin: str
  double_char: IntegerBoolean
  part_scale: str
  shop_dynamic_hx: IntegerBoolean
  voice_lang: list[int] | EmptyString
  time: Vector2[Vector3[int]] | EmptyString
  lover_hand: str
  show_skin: str

  @staticmethod
  def extract_time(reader: ModelReader["ShipSkinTemplate"]) -> Vector2[Vector3[int]] | EmptyString:
    reader.set_position("time")
    tag = reader.peek(1)

    if tag == b"\x05":
      return EmptyString()

    if tag != b"\x01":
      raise TagError(tag, "01 or 05")

    result: list[Vector3[int]] = []

    while reader.peek(4) == b"\x01\x00\x04\x00":
      result.append(reader.get_value_by_type(Vector3[int]))

    result.reverse()
    return Vector2(result)

  @staticmethod
  def extract_fx_container(
    reader: ModelReader["ShipSkinTemplate"],
  ) -> Vector4[Vector3[int | float]]:
    reader.set_position("fx_container")

    if (b := reader.peek(1)) != b"\x01":
      raise TagError(b, b"\x01")

    result: list[Vector3[int | float]] = []

    while reader.peek(4) == b"\x01\x00\x04\x00":
      result.append(reader.get_value_by_type(Vector3[int | float]))

    result.reverse()
    return Vector4(result)

  @staticmethod
  def extract_l2d_se(
    reader: ModelReader["ShipSkinTemplate"],
  ) -> dict[str, tuple[str, float]] | EmptyString:
    reader.set_position("l2d_se")

    if reader.peek(1) == b"\x05":
      return EmptyString()

    result: dict[str, tuple[str, float]] = {}
    running = True

    while running:
      key = reader.read_string()

      if reader.peek(3) == b"\x01\x00\x00":
        reader.seek(3)
        running = False

      value = reader.get_value_by_type(tuple[str, float])
      result[key] = value

    return dict(reversed(result.items()))

  @staticmethod
  def extract_l2d_para_range(
    reader: ModelReader["ShipSkinTemplate"],
  ) -> dict[str, Vector2[int | float]] | EmptyString:
    reader.set_position("l2d_para_range")

    if reader.peek(1) == b"\x05":
      return EmptyString()

    result: dict[str, Vector2[int | float]] = {}
    running = True

    if reader.peek(3) == b"\x01\x00\x03":
      reader.read_array()  # 905013 double? flush unused array

    while running:
      key = reader.read_string()

      if reader.peek(3) == b"\x01\x00\x00":
        reader.seek(3)
        running = False

      value = reader.get_value_by_type(Vector2[int | float])
      result[key] = value

    return dict(reversed(result.items()))

  @staticmethod
  def extract_special_effects(
    reader: ModelReader["ShipSkinTemplate"],
  ) -> tuple[str, Vector3[int | float], tuple[int | float]] | EmptyString:
    reader.set_position("special_effects")

    if reader.peek(1) == b"\x05":
      return EmptyString()

    v1: tuple[int | float] = reader.get_value_by_type(tuple[int | float])
    v2: Vector3[int | float] = reader.get_value_by_type(Vector3[int | float])
    v3: tuple[str] = reader.get_value_by_type(tuple[str])

    return (v3[0], v2, v1)

  @staticmethod
  def extract_bound_bone(reader: ModelReader["ShipSkinTemplate"]) -> ShipSkinTemplateBoundBone:
    reader.set_position("bound_bone")
    result: dict[str, list[Vector2[int | float] | Vector3[int | float]] | Vector3[int | float]] = {}
    running = True

    while running:
      key = reader.read_string()

      if reader.peek(3) == b"\x01\x00\x00":
        reader.seek(3)
        running = False

      # lazy to read opcodes, this is fast fix
      if key == "remote":
        result[key] = reader.get_value_by_type(Vector3[int | float])
        continue

      build: list[Vector2[int | float] | Vector3[int | float]] = []

      while True:
        b = reader.peek(4)

        if b == b"\x01\x00\x03\x00":
          build.insert(0, reader.get_value_by_type(Vector2[int | float]))
          continue

        if b == b"\x01\x00\x04\x00":
          build.insert(0, reader.get_value_by_type(Vector3[int | float]))
          continue

        break

      result[key] = build

    return ShipSkinTemplateBoundBone.model_validate(result, strict=True)

  @staticmethod
  def extract_get_showing(
    reader: ModelReader["ShipSkinTemplate"],
  ) -> ShipSkinTemplateGetShowing | EmptyString:
    reader.set_position("get_showing")

    if reader.peek(1) == b"\x05":
      return EmptyString()

    result: dict[str, IntegerBoolean | Vector3[int | float] | list[tuple[int | float, ...]]] = {}

    if reader.read_string() == "data":
      data: list[tuple[int | float, ...]] = []

      while reader.peek(4) == b"\x01\x00\x07\x00":
        data.insert(0, tuple(reader.get_value_by_type(list[int | float])))

      result["data"] = data

    if reader.peek(3) == b"\x01\x01\x00":
      reader.seek(3)

    key = reader.read_string()

    if key == "paint_offset":
      result["paint_offset"] = reader.get_value_by_type(Vector3[int | float])

      if reader.peek(3) == b"\x01\x01\x00":
        reader.seek(3)

      key = reader.read_string()

    if key == "show":
      result["show"] = IntegerBoolean(reader.read_varint())

    return ShipSkinTemplateGetShowing.model_validate(result, strict=True)

  @staticmethod
  def extract_smoke(
    reader: ModelReader["ShipSkinTemplate"],
  ) -> list[tuple[int, list[tuple[str, Vector3[int | float]]]]]:
    reader.set_position("smoke")
    result: list[tuple[int, list[tuple[str, Vector3[int | float]]]]] = []

    while reader.peek(4) == b"\x01\x00\x04\x00":
      build: list[tuple[str, Vector3[int | float]]] = []

      while reader.peek(4) == b"\x01\x00\x04\x00":
        v1 = reader.get_value_by_type(Vector3[int | float])
        v2 = reader.get_value_by_type(tuple[str])
        build.insert(0, (v2[0], v1))

      v3 = reader.get_value_by_type(tuple[int])
      result.insert(0, (v3[0], build))

    return result


def ship_skin_template(source: Path, output: Path) -> dict[str, ShipSkinTemplate]:
  reader = ModelReader(source, ShipSkinTemplate, "id")
  return reader.write(output)
