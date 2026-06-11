import types
from pathlib import Path
from typing import Any, Union, cast, get_args, get_origin, override

from pydantic import TypeAdapter, ValidationError

from ..exceptions import PositionNotFound, TagError
from .BinaryReader import BinaryReader


class SchemaReader(BinaryReader):
  __slots__ = ("cache", "constant_position", "instructions")

  def __init__(self, path: Path, offset: int = 0) -> None:
    super().__init__(source=path, offset=offset)
    self.cache: dict[Any, TypeAdapter[Any]] = {}
    self.constant_position = 0
    self.instructions: list[bytes] = []

  def calculate_constant_position(self) -> None:
    self.position = 0

    _length = self.read_int(b"")
    # normal is Flags, Params, FrameSize, Upvalues
    self.seek(3)  # skip FrameSize, <FrameSize+Flags>, Flags
    _upvalues_count = self.read_int(b"", max_length=1)
    # knum and kgc swapped, probably endian or obfuscated, idk idc
    _knum = self.read_int(b"")
    _kgc = self.read_int(b"")
    _instruction_count = self.read_int(b"")

    if _instruction_count:
      self.instructions = [self.read(4) for _ in range(_instruction_count)]

    # should be never appear on sharecfgdata, since its single file injection?
    # im not sure, obfuscated luajit is bit confusing
    if _upvalues_count:
      self.seek(2 * _upvalues_count)

    # SchemaReader is not gonna work with op codes, that for next time
    # This intended for removing unused header to improve find and find_all
    self.constant_position = self.position

  @override
  def find(
    self,
    sub: bytes | str,
    start: int | None = None,
    end: int | None = None,
  ) -> int:
    return super().find(sub, start=self.constant_position if start is None else start, end=end)

  @override
  def find_all(
    self,
    sub: bytes | str,
    start: int | None = None,
    end: int | None = None,
  ) -> list[int]:
    return super().find_all(sub, start=self.constant_position if start is None else start, end=end)

  @override
  def lock(self, offset: int, length: int, *, calculate_constant_position: bool = True) -> None:
    super().lock(offset=offset, length=length)

    if calculate_constant_position:
      self.calculate_constant_position()

  def lock_next(self, *, calculate_constant_position: bool = True) -> bool:
    self.position = 0
    self.offset += self.length

    if self.length == len(self.view):
      self.offset = 0

    self.length = len(self.view) - self.offset

    try:
      length = self.read_int(tag=b"") + self.position
    except EOFError:
      return False

    if (self.offset + length) > len(self.view):
      return False

    self.lock(self.offset, length, calculate_constant_position=calculate_constant_position)
    return True

  def read_table_header(self, array: bool = True) -> int:
    if (x := self.peek(1)) != b"\x01":
      raise TagError(x, b"\x01")

    self.seek(1)

    # array
    if array:
      if self.peek(1) != b"\x00":
        self.seek(2)
        return 0

      self.seek(1)
      length = self.read_int(tag=b"") - 1
      self.seek(1)

      return length

    # dict
    length = self.read_int(tag=b"")
    self.seek(1)
    return length

  def read_constant(self, position: int | None = None, length: int | None = None) -> list[Any]:
    if position is None:
      position = self.constant_position

    if length is None:
      length = self.length

    prev_position = self.position
    self.position = position
    reader = BinaryReader(source=self.read(length))
    self.position = prev_position

    kgc: list[Any] = []

    def get_table_constant() -> None | bool | int | float | str:
      tag = reader.peek(1)

      if tag == b"\x00":
        return reader.read_nil()

      if tag in b"\x01\x02":
        return reader.read_bool()

      if tag == b"\x03":
        return reader.read_varint()

      if tag == b"\x04":
        return reader.read_float()

      return reader.read_string()

    while (tag := reader.peek(1)) != b"":
      if tag == b"\x01":
        is_array = reader.peek(2) == b"\x01\x00"
        length = reader.read(4)[2] - 1 if is_array else reader.read(3)[1]

        table: dict[Any, Any] = {}
        array: list[Any] = []

        for _ in range(length):
          if is_array:
            array.append(get_table_constant())
            continue

          key = get_table_constant()
          value = get_table_constant()
          table[key] = value

        kgc.append(array if is_array else table)
        continue

      if tag in b"\x02\x03":
        kgc.append(reader.read_varint())
        continue

      if tag == b"\x04":
        kgc.append(reader.read_float())
        continue

      kgc.append(reader.read_string())

    return kgc

  def convert_tag_to_types(self, tag: bytes) -> set[type]:
    if tag == b"\x00":
      return {type(None)}

    if tag == b"\x01":
      return {list, set, tuple, bool}

    if tag == b"\x02":
      return {
        bool,
      }

    if tag == b"\x03":
      return {
        int,
      }

    if tag == b"\x04":
      return {
        float,
      }

    # guarantee tag >5
    return {
      str,
    }

  def get_value_by_type[T](self, expect: type[T] | types.UnionType) -> T:
    # due to LSP limitation of how generic is handled, aggressive cast/type_ignore will be used
    origin = get_origin(expect)
    base_type = origin if origin is not None else expect

    if expect in (type(None), None):
      return cast(T, self.read_nil())

    if (origin == Union) or (isinstance(origin, type) and (origin == types.UnionType)):
      errors: list[Exception] = []

      for arg in get_args(expect):
        position = self.position

        try:
          return self.get_value_by_type(arg)

        except Exception as e:
          errors.append(e)

          # recover position
          self.position = position

      if type(None) not in get_args(expect):
        raise ExceptionGroup("error", errors)

      return cast(T, None)

    if base_type is int:
      return cast(T, self.read_varint())

    if base_type is float:
      return cast(T, self.read_float())

    if base_type is bool:
      return cast(T, self.read_bool())

    if base_type is str:
      return cast(T, self.read_string())

    if base_type in (list, set):
      return self._read_array(expect=expect)  # type: ignore

    if base_type is tuple:
      return self._read_tuple(expect=expect)  # type: ignore

    if base_type is dict:
      return self._read_dict(expect=expect)  # type: ignore

    if hasattr(base_type, "extract"):
      return base_type.extract(self, expect)  # type: ignore

    raise NotImplementedError(f"type {expect} is not implemented yet.")

  def _read_array[X: list[Any] | set[Any]](self, expect: type[X]) -> X:
    length = self.read_table_header()
    inner_types = get_args(expect)

    if not length:
      return expect()  # pyright: ignore[reportUnknownVariableType]

    if not len(inner_types):
      return expect(self.read_array())  # pyright: ignore[reportUnknownVariableType]

    if len(inner_types) == 1:
      element_type = inner_types[0]

      # for blank array that unknown yet
      if element_type is type(None):
        return expect()  # pyright: ignore[reportUnknownVariableType]

      element_origin = get_origin(element_type) or element_type

      if element_origin not in (int, float, str, bool, Union, types.UnionType):
        raise NotImplementedError("Nested list are not implemented yet.")

      return expect(self.get_value_by_type(element_type) for _ in range(length))

    result: list[Any] = []

    for _ in range(length):
      tag = self.convert_tag_to_types(self.peek(1)) - {tuple, list, dict}

      if len(tag) != 1:
        raise ValueError(f"Unexpected behaviour, expected single length tag, got {tag}")

      tag = tag.pop()

      if tag not in inner_types:
        raise TagError(self.peek(1), str(inner_types))

      result.append(self.get_value_by_type(tag))

    return expect(result)

  def _read_tuple(self, expect: type[tuple[Any, ...]]) -> tuple[Any, ...]:
    length = self.read_table_header()
    inner_types = get_args(expect)

    if not length:
      # Unknown tuple: tuple[Never]
      if not len(inner_types):
        return ()

      raise ValueError("Tuple must have atleast single length")

    # Non-fixed: tuple[int, ...]
    if len(inner_types) == 2 and inner_types[1] is Ellipsis:
      element_type = inner_types[0]
      return tuple(self.get_value_by_type(element_type) for _ in range(length))

    # Fixed: tuple[int, int, int]
    if len(inner_types) != length:
      raise ValueError(f"tuple length mismatch! expect {len(inner_types)}, got {length}.")

    return tuple(self.get_value_by_type(x) for x in inner_types)

  def _read_dict[X](self, expect: type[dict[str, X]]) -> dict[str, X]:
    length = self.read_table_header(array=False)

    if not length:
      return {}

    build: dict[str, Any] = {}

    inner_types = get_args(expect)[1]
    inner = get_origin(inner_types)

    if (inner == Union) or (isinstance(inner, type) and (inner == types.UnionType)):
      inner_types = get_args(inner_types)
    else:
      inner_types = [inner_types]

    for element_type in inner_types:
      if element_type in (int, float, str, bool, type(None), None):
        continue

      raise NotImplementedError(f"dict[str, {element_type}] is not supported yet.")

    for _ in range(length):
      key = self.read_string()
      tag = self.convert_tag_to_types(self.peek(1)) - {set, tuple, list, dict}

      if len(tag) != 1:
        raise ValueError(f"Unexpected behaviour, expected single length tag, got {tag}")

      tag = tag.pop()

      if tag not in inner_types:
        raise TagError(self.peek(1), str(inner_types))

      build[key] = self.get_value_by_type(tag)

    return build

  def get_value[X](self, key: str, expect: type[X], default: X | None = None) -> X | None:
    try:
      self.set_position(key=key)
    except PositionNotFound as e:
      if default is None:
        raise e

      return default

    try:
      result = self.get_value_by_type(expect)

    except TagError as e:
      if default is None:
        raise e

      return default

    if expect not in self.cache:
      self.cache[expect] = TypeAdapter(expect)

    adapter = self.cache[expect]

    try:
      return adapter.validate_python(result, strict=True)

    except ValidationError as e:
      print(f"Expected {expect}, but {key} got type {type(result)} with value {result} instead.")
      raise e

  def set_position(self, key: str) -> None:
    """
    Set cursor position at beginning of value\n
    key[v]alue
    """
    position = self.find(key)

    if position == -1:
      raise PositionNotFound(f"{key} not found")

    self.position = position
    self.read_string()
