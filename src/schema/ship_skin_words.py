import json
from pathlib import Path

from .. import ModelReader, SchemaModel
from ..types import EmptyString, NotRequired


class ShipSkinWords(SchemaModel, extra="allow"):
  id: int
  voice_key: int
  voice_key_2: int
  battle: str
  couple_encourage: list[tuple[list[int | float], int, str, int]] | EmptyString
  detail: str
  drop_descrip: str
  expedition: str
  feeling1: str
  feeling2: str
  feeling3: str
  feeling4: str
  feeling5: str
  headtouch: str
  home: str
  hp_warning: str
  login: str
  lose: str
  mail: str
  main: str
  mission: str
  mission_complete: str
  profile: str
  propose: str
  skill: str
  touch: str
  touch2: str
  unlock: str
  upgrade: str
  win_mvp: str
  vote: str
  gift_prefer: str
  gift_dislike: str

  @staticmethod
  def extract_couple_encourage(
    reader: ModelReader["ShipSkinWords"],
  ) -> list[tuple[list[int | float], int, str, int]] | EmptyString:
    reader.set_position("couple_encourage")

    if reader.peek(1) == b"\x05":
      return EmptyString()

    result: list[tuple[list[int | float], int, str, int]] = []

    while reader.peek(2) in b"\x01\x00":
      expect = tuple[None, int, str, int]

      if reader.peek(3) == b"\x01\x00\x04":
        expect = tuple[None, int, str]

      value_1 = reader.get_value_by_type(expect)
      value_2 = reader.get_value_by_type(list[int | float])

      result.insert(0, (value_2, value_1[1], value_1[2], value_1[3] if len(value_1) > 3 else 0))

    return result


def _inject_extra_keys() -> None:
  # inject _replace
  for field in ShipSkinWords.model_fields:
    if field == "couple_encourage":
      continue

    ShipSkinWords.__extract_extra__[f"{field}_replace"] = NotRequired[str]

  # inject skill
  for i in range(5):  # known is up to 2
    ShipSkinWords.__extract_extra__[f"skill_{i}"] = NotRequired[str]

  # inject asmr
  for i in range(20):  # known is up to 10
    ShipSkinWords.__extract_extra__[f"asmr_{i:03}"] = NotRequired[str]

  # inject known custom collab key
  ShipSkinWords.__extract_extra__.update(
    {
      "skill_dal_1": NotRequired[str],
      "skill_dal_2": NotRequired[str],
      "dal_shop1": NotRequired[str],
      "dal_shop2": NotRequired[str],
      "dal_shop3": NotRequired[str],
      "dal_shop4": NotRequired[str],
      "dal_shop5": NotRequired[str],
      "atelier_yumia_item_1": NotRequired[str],
      "atelier_yumia_item_2": NotRequired[str],
      "atelier_yumia_item_3": NotRequired[str],
      "atelier_yumia_item_4": NotRequired[str],
      "atelier_yumia_item_5": NotRequired[str],
      "atelier_yumia_item_6": NotRequired[str],
      "atelier_yumia_item_7": NotRequired[str],
      "atelier_yumia_item_8": NotRequired[str],
      "atelier_yumia_item_9": NotRequired[str],
      "atelier_yumia_item_10": NotRequired[str],
      "atelier_yumia_item_11": NotRequired[str],
      "atelier_yumia_item_12": NotRequired[str],
      "atelier_yumia_shop_1": NotRequired[str],
      "atelier_yumia_shop_2": NotRequired[str],
      "atelier_yumia_shop_3": NotRequired[str],
      "atelier_yumia_shop_4": NotRequired[str],
      "atelier_yumia_shop_5": NotRequired[str],
      "ryza_item1": NotRequired[str],
      "ryza_item2": NotRequired[str],
      "ryza_item3": NotRequired[str],
      "ryza_item4": NotRequired[str],
      "ryza_item5": NotRequired[str],
      "ryza_shop1": NotRequired[str],
      "ryza_shop2": NotRequired[str],
      "ryza_shop3": NotRequired[str],
      "ryza_shop4": NotRequired[str],
      "ryza_shop5": NotRequired[str],
    }
  )

  # inject from build/sharecfg/character_voice.json if available
  _character_voice_path = Path(__file__).parents[2] / "build/sharecfg/character_voice.json"

  if not _character_voice_path.exists():
    return

  character_voice = json.loads(_character_voice_path.read_text(encoding="utf-8"))

  if "all" not in character_voice:
    character_voice["all"] = character_voice.keys()

  for voice_key in character_voice["all"]:
    if (
      voice_key.startswith("main")
      or voice_key.startswith("link")
      or (voice_key in ShipSkinWords.model_fields)
      or (voice_key in ShipSkinWords.__extract_extra__)
    ):
      continue

    ShipSkinWords.__extract_extra__[voice_key] = NotRequired[str]


_inject_extra_keys()


def ship_skin_words(source: Path, output: Path) -> dict[str, ShipSkinWords]:
  reader = ModelReader(source, ShipSkinWords, "id")
  return reader.write(output)
