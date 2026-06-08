from pathlib import Path

from pydantic import Field

from .. import ModelReader, SchemaModel


class ShipDataBreakout(SchemaModel):
  id: int
  pre_id: int
  breakout_id: int
  breakout_view: str
  level: int
  icon: str
  use_char_num: int
  use_char: int
  use_gold: int
  use_item: list[None]
  weapon_ids: list[int] = Field(default_factory=list)


def ship_data_breakout(source: Path, output: Path) -> dict[str, ShipDataBreakout]:
  reader = ModelReader(source, ShipDataBreakout, "id")
  return reader.write(output)
