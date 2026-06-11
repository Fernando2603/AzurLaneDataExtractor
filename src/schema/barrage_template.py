from pathlib import Path

from .. import ModelReader, SchemaModel
from ..exceptions import PositionNotFound
from ..types import NotRequired


class BarrageTemplate(SchemaModel):
  id: int
  angle: int | float
  delay: int | float
  first_delay: int | float
  delta_delay: int | float
  delta_angle: int | float
  delta_offset_x: int | float
  delta_offset_z: int | float
  offset_prioritise: bool
  offset_x: int | float
  offset_z: int | float
  primal_repeat: int
  random_angle: NotRequired[bool]
  senior_delay: int | float
  senior_repeat: int | float
  trans_ID: int

  @staticmethod
  def after_lock_next(reader: ModelReader["BarrageTemplate"], result: bool) -> bool:
    try:
      reader.set_position(reader.primary)
    except PositionNotFound:
      return False

    return result


def barrage_template(source: Path, output: Path) -> dict[str, BarrageTemplate]:
  reader = ModelReader(source, BarrageTemplate, "id")
  return reader.write(output)
