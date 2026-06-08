from typing import TYPE_CHECKING, Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from ..exceptions import TagError

if TYPE_CHECKING:
  from ..reader import SchemaReader


class IntegerBoolean(int):
  def __new__(cls, value: int) -> "IntegerBoolean":
    if value not in (0, 1):
      raise ValueError("Value must be exactly 0 or 1")

    return super().__new__(cls, value)

  @classmethod
  def __get_pydantic_core_schema__(cls, source: type, handler: GetCoreSchemaHandler) -> CoreSchema:
    return core_schema.no_info_after_validator_function(
      cls.validate,
      core_schema.union_schema([core_schema.is_instance_schema(cls), core_schema.int_schema()]),
    )

  @classmethod
  def validate(cls, value: Any) -> "IntegerBoolean":
    if isinstance(value, cls):
      return value

    return cls(value)

  @classmethod
  def extract(cls, reader: "SchemaReader", _: type) -> "IntegerBoolean":
    if (b := reader.peek(1)) != b"\x03":
      raise TagError(b, b"\x03")

    return cls(reader.read_varint())
