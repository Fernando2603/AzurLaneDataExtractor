from typing import Any, cast, get_origin

from pydantic import BaseModel, model_serializer, model_validator

from .types import NotAssigned, NotRequired

NOT_ASSIGNED = NotAssigned()


class SchemaModel(BaseModel):
  # used for key injection, example: ship_skin_words
  __extract_extra__: dict[str, type] = {}

  @model_validator(mode="before")
  @classmethod
  def not_required_validator(cls, data: Any) -> Any:
    if isinstance(data, dict):
      data = {k: v for k, v in data.items() if v != NOT_ASSIGNED}  # pyright: ignore

    return data

  @model_serializer(mode="wrap")
  def not_required_serializer(self, handler: Any) -> dict[str, Any]:
    result = handler(self)

    for field, info in type(self).model_fields.items():
      if get_origin(info.annotation) != NotRequired:
        continue

      value = cast(NotRequired[Any], getattr(self, field))

      if isinstance(value.value, NotAssigned):
        del result[field]

    return result
