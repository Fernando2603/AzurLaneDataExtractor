from pathlib import Path

from pydantic import Field

from .. import ModelReader, SchemaModel


class ShipDataTemplate(SchemaModel):
  id: int
  type: int
  group_type: int
  strengthen_id: int
  can_get_proficency: int
  max_level: int
  energy: int
  star: int
  star_max: int
  oil_at_start: int
  oil_at_end: int
  equip_id_1: int
  equip_id_2: int
  equip_id_3: int
  equip_1: list[int] = Field(default_factory=list)
  equip_2: list[int] = Field(default_factory=list)
  equip_3: list[int] = Field(default_factory=list)
  equip_4: list[int] = Field(default_factory=list)
  equip_5: list[int] = Field(default_factory=list)
  buff_list: list[int] = Field(default_factory=list)
  buff_list_display: list[int] = Field(default_factory=list)
  hide_buff_list: list[int] = Field(default_factory=list)
  airassist_time: list[int] = Field(default_factory=list)
  specific_type: list[str]


def ship_data_template(source: Path, output: Path) -> dict[str, ShipDataTemplate]:
  reader = ModelReader(source, ShipDataTemplate, "id")
  return reader.write(output)
