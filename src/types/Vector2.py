from collections.abc import Iterable
from typing import TYPE_CHECKING, get_args

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

if TYPE_CHECKING:
  from ..reader import SchemaReader


class Vector2[T](tuple[T]):
  def __new__(cls, value: Iterable[T]) -> "Vector2[T]":
    value = tuple(value)

    if len(value) != 2:
      raise ValueError("Vector2 must contain exactly 2 items")

    return super().__new__(cls, value)

  @property
  def x(self) -> T:
    return self[0]

  @property
  def y(self) -> T:
    return self[1]

  @classmethod
  def __get_pydantic_core_schema__(cls, source: type, handler: GetCoreSchemaHandler) -> CoreSchema:
    args = get_args(source)
    item = handler.generate_schema(args[0] if args else float)
    schema = core_schema.tuple_positional_schema([item, item])
    return core_schema.no_info_after_validator_function(cls, schema)

  @classmethod
  def extract(cls, reader: "SchemaReader", _type: "Vector2[T]") -> "Vector2[T]":
    arg = get_args(_type)[0]
    return cls(reader._read_tuple(tuple[arg, arg]))
