from collections.abc import Iterable
from typing import TYPE_CHECKING, get_args

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

if TYPE_CHECKING:
  from ..reader import SchemaReader


class Vector4[T](tuple[T]):
  def __new__(cls, value: Iterable[T]) -> "Vector4[T]":
    value = tuple(value)

    if len(value) != 4:
      raise ValueError("Vector4 must contain exactly 4 items")

    return super().__new__(cls, value)

  # using unity order (x, y, z, w)
  @property
  def x(self) -> T:
    return self[0]

  @property
  def y(self) -> T:
    return self[1]

  @property
  def z(self) -> T:
    return self[2]

  @property
  def w(self) -> T:
    return self[3]

  @classmethod
  def __get_pydantic_core_schema__(cls, source: type, handler: GetCoreSchemaHandler) -> CoreSchema:
    args = get_args(source)
    item = handler.generate_schema(args[0] if args else float)
    schema = core_schema.tuple_positional_schema([item, item, item, item])
    return core_schema.no_info_after_validator_function(cls, schema)

  @classmethod
  def extract(cls, reader: "SchemaReader", _type: "Vector4[T]") -> "Vector4[T]":
    arg = get_args(_type)[0]
    return cls(reader._read_tuple(tuple[arg, arg, arg, arg]))
