from typing import TYPE_CHECKING, Any, get_args

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

if TYPE_CHECKING:
  from ..reader import SchemaReader


class NotAssigned:
  value = "<NotAssigned>"

  def __repr__(self) -> str:
    return self.value


NOT_ASSIGNED = NotAssigned()


class NotRequired[T]:
  """
  Same as `typing.NotRequired` but for `pydantic.BaseModel`\n
  `NotRequired` is a bit complex, i know `Sentinel` are available but unstable.\n\n

  The most useful benefit in this `NotRequired` are `Field` are not required\n
  but the downside is on model initialization itself, for example below:
  ```Python
    # this is not recommended, LSP gonna complain
    class Wrong(SchemaModel):
      x: NotRequired[int | None] = Field(default_factory=NotRequired)

    class Model(SchemaModel):
      x: NotRequired[int | None]
      y: NotRequired[int | None]

    # LSP are gonna complain ArgumentMissing
    # but it still an valid model
    Model(x=1)

    # to prevent LSP complaining we can wrap the Model like this
    Model(x=NotRequired(1), y=NotRequired())

    # recommended way to do this is
    Model.model_validate({ 'x': 1 }) # LSP will not complain at all
  ```
  we get all pydantic validator benefit on top of small sacrifice\n
  this have no downside at on `ModelReader` since we always use `model_validate`.
  """

  value: T

  def __init__(self, value: T = NOT_ASSIGNED) -> None:
    self.__dict__["value"] = value

  def __repr__(self) -> str:
    return str(self.value)

  def __hash__(self) -> int:
    if isinstance(self.value, NotAssigned):
      raise TypeError("NotRequired[NotAssigned] is not hashable.")

    return hash(self.value)

  def __eq__(self, other: Any) -> bool:
    other_val = other.value if isinstance(other, type(self)) else other

    if isinstance(self.value, NotAssigned) or isinstance(other_val, NotAssigned):
      return isinstance(self.value, type(other_val))

    return self.value == other_val

  def __getattr__(self, name: str) -> Any:
    if isinstance(self.value, NotAssigned):
      raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    attr = getattr(self.value, name)

    if callable(attr):
      return attr

    return attr

  def __setattr__(self, name: str, val: Any) -> None:
    if (name in self.__dict__) or hasattr(type(self), name):
      super().__setattr__(name, val)
      return

    if isinstance(self.value, NotAssigned):
      raise ValueError(f"Cannot set attribute '{name}' on an unassigned NotRequired field.")

    setattr(self.value, name, val)

  @classmethod
  def __get_pydantic_core_schema__(cls, source: type, handler: GetCoreSchemaHandler) -> CoreSchema:
    args = get_args(source)

    if len(args) != 1:
      raise TypeError("NotRequired require 1 args")

    schema = handler.generate_schema(args[0])

    def preprocess(x: Any) -> T:
      return x.value if isinstance(x, cls) else x

    def serializer(instance: "NotRequired[T]", serializer: Any) -> T:
      if isinstance(instance.value, NotAssigned):
        return serializer(instance.value.value)

      return serializer(instance.value)

    return core_schema.with_default_schema(
      core_schema.chain_schema(
        [
          core_schema.no_info_before_validator_function(preprocess, schema),
          core_schema.no_info_plain_validator_function(cls.validate),
        ]
      ),
      serialization=core_schema.wrap_serializer_function_ser_schema(serializer),
      default_factory=lambda: cls(NOT_ASSIGNED),  # pyright: ignore[reportArgumentType]
    )

  @classmethod
  def validate(cls, value: Any) -> "NotRequired[T]":
    if isinstance(value, cls):
      return value

    return cls(value)

  @classmethod
  def extract(cls, reader: "SchemaReader", types: type) -> "NotRequired[T]":
    return cls(reader.get_value_by_type(get_args(types)[0]))
