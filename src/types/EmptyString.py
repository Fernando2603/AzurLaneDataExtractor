from typing import TYPE_CHECKING, Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from ..exceptions import TagError

if TYPE_CHECKING:
  from ..reader import SchemaReader


class EmptyString(str):
  def __new__(cls, value: str = "") -> "EmptyString":
    if value != "":
      raise ValueError("Value must be empty string")

    return super().__new__(cls, value)

  @classmethod
  def __get_pydantic_core_schema__(cls, source: type, handler: GetCoreSchemaHandler) -> CoreSchema:
    return core_schema.no_info_after_validator_function(cls.validate, core_schema.str_schema())

  @classmethod
  def validate(cls, value: Any) -> "EmptyString":
    if isinstance(value, cls):
      return value

    return cls(value)

  @classmethod
  def extract(cls, reader: "SchemaReader", _: type) -> "EmptyString":
    if (b := reader.peek(1)) != b"\x05":
      raise TagError(b, b"\x05")

    return cls("")
