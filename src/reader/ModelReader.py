import contextlib
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any, cast, get_origin, override

from pydantic import TypeAdapter
from pydantic_core import PydanticUndefined

from ..exceptions import PositionNotFound, TagError
from ..SchemaModel import SchemaModel
from ..serializer import encode_string
from ..types import NotAssigned, NotRequired
from .SchemaReader import SchemaReader


class ModelReader[T: SchemaModel](SchemaReader):
  __slots__ = ("adapter", "model", "primary")

  def __init__(self, path: Path, model: type[T], primary: str) -> None:
    if primary not in model.model_fields:
      raise ValueError(
        f"Primary key {primary} not found in {model}, available keys are {model.model_fields}"
      )

    if (x := model.model_fields[primary].annotation) not in (str, int):
      raise ValueError(f"Primary key type {x} are not supported, expected str or int type")

    super().__init__(path=path, offset=0)
    self.model = model
    self.adapter = TypeAdapter(dict[str, model])
    self.primary = primary

  @override
  def lock_next(self, *, calculate_constant_position: bool = True) -> bool:
    if hasattr(self.model, "lock_next"):
      return self.model.lock_next(self)  # type: ignore

    if hasattr(self.model, "before_lock_next"):
      self.model.before_lock_next(self)  # type: ignore

    result = super().lock_next(calculate_constant_position=False)

    if hasattr(self.model, "after_lock_next"):
      result = cast(bool, self.model.after_lock_next(self, result))  # type: ignore

    if calculate_constant_position and result:
      self.calculate_constant_position()

    return result

  @override
  def set_position(self, key: str) -> None:
    if (key == self.primary) and (self.model.model_fields[key].annotation is int):
      position = self.find(encode_string(key) + b"\x03")
    else:
      position = self.find(key)

    if position == -1:
      raise PositionNotFound(f"{key} not found")

    self.position = position
    self.read_string()

  def get_model(self) -> T:
    result: dict[str, Any] = {}

    def _try_get_value[X](fn: Callable[[], X]) -> X:
      try:
        return fn()
      except Exception as e:
        print(f"offset = {self.offset}")
        print(f"length = {self.length}")
        print(" ".join(f"{b:02X}" for b in self.view[self.offset : self.offset + self.length]))

        field_type = self.model.model_fields[self.primary].annotation

        if (self.primary not in result) and (field_type is not None):
          try:
            result[self.primary] = self.get_value(key=self.primary, expect=field_type)
          except Exception:
            contextlib.suppress(Exception)

        print(f"-> {self.primary} = {result.get(self.primary, 'primary_not_found')}")
        print(f"-> {key}: {field_type.__name__ if field_type else None} = {default}")
        print(f"-> hex {key} = {' '.join(f'{b:02X}' for b in encode_string(key))}")

        if type(e) is not TagError:
          raise e

        print(f"{type(e).__name__}: {e}")
        raise SystemExit  # noqa: B904

    for key, field_info in self.model.model_fields.items():
      if hasattr(self.model, f"extract_{key}"):
        result[key] = _try_get_value(partial(getattr(self.model, f"extract_{key}"), self))
        continue

      default = field_info.get_default(call_default_factory=True)
      field_type = field_info.annotation

      if field_type is None:
        raise TypeError(f"Pydantic failed to parse annotation for {key}")

      if get_origin(field_type) == NotRequired:
        if default != PydanticUndefined:
          raise ValueError("Field default_factory on NotRequired are forbidden.")

        default = NotRequired()

      elif default == PydanticUndefined:
        default = None

      if field_type is type(None):
        result[key] = default
        continue

      result[key] = _try_get_value(
        partial(self.get_value, key=key, expect=field_type, default=default)
      )

    for key, field_type in self.model.__extract_extra__.items():
      try:
        origin = get_origin(field_type)
        value = self.get_value(
          key=key,
          expect=field_type,
          default=NotRequired() if origin == NotRequired else None,
        )

        if isinstance(value, NotRequired):
          if isinstance(value.value, NotAssigned):
            continue

          value = value.value

        result[key] = value

      except Exception:
        contextlib.suppress(Exception)

    try:
      return self.model.model_validate(result, strict=True)
    except:
      print(result)
      raise

  def parse(self) -> dict[str, T]:
    result: dict[str, T] = {}

    while self.lock_next():
      build = self.get_model()
      result[str(getattr(build, self.primary))] = build

    return result

  def write(self, path: Path) -> dict[str, T]:
    if not path.suffix:
      path = path / self.path.name

    path = path.with_suffix(".json")
    path.parent.mkdir(parents=True, exist_ok=True)

    output = self.parse()
    path.write_bytes(self.adapter.dump_json(output, indent=2))
    return output
