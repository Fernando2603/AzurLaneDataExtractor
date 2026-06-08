import struct
from pathlib import Path

from ..exceptions import TagError
from ..serializer import encode_string


class BinaryReader:
  __slots__ = ("length", "offset", "path", "position", "view")

  def __init__(self, path: Path, offset: int = 0) -> None:
    self.path = path
    self.view = path.read_bytes()
    self.length = len(self.view)
    self.offset = offset
    self.position = 0

  def lock(self, offset: int, length: int) -> None:
    self.offset = offset
    self.length = length
    self.position = 0

  def tell(self) -> int:
    return self.offset + self.position

  def seek(self, length: int) -> None:
    self.position = min(self.position + length, self.offset + self.length)

  def peek(self, length: int) -> bytes:
    if not length:
      return b""

    position = self.position
    out = self.read(length)
    self.position = position
    return out

  def find(
    self,
    sub: bytes | str,
    start: int | None = None,
    end: int | None = None,
  ) -> int:
    if isinstance(sub, str):
      sub = encode_string(sub)

    start = self.offset + (max(0, min(start, self.length)) if start is not None else 0)
    end = self.offset + (min(self.length, max(end, 0)) if end is not None else self.length)

    result = self.view.find(sub, start, end)

    if result == -1:
      return -1

    return result - self.offset

  def find_all(
    self,
    sub: bytes | str,
    start: int | None = None,
    end: int | None = None,
  ) -> list[int]:
    if isinstance(sub, str):
      sub = encode_string(sub)

    start = self.offset + (max(0, min(start, self.length)) if start is not None else 0)
    end = self.offset + (min(self.length, max(end, 0)) if end is not None else self.length)

    result: list[int] = []

    while (value := self.view.find(sub, start, end)) != -1:
      start = value + len(sub)
      result.append(value - self.offset)

    return result

  def read(self, length: int) -> bytes:
    if not length:
      return b""

    pos = self.tell()
    end = min(pos + length, self.offset + self.length)
    out = self.view[pos:end]
    self.position += length

    return out

  def read_int(self, tag: bytes = b"\x03", signed: bool = True, max_length: int = 10) -> int:
    if len(tag):
      if (x := self.peek(1)) != tag:
        raise TagError(x, tag)

      self.seek(1)

    result = 0
    shift = 0

    for _ in range(max_length):
      byte = self.read(1)

      if not byte:
        raise EOFError("Unexpected EOF")

      b = byte[0]

      result |= (b & 0x7F) << shift

      if not (b & 0x80):
        break

      shift += 7

    if signed and (result & (1 << 31)):
      result -= 1 << 32

    return result

  def read_nil(self) -> None:
    if (x := self.peek(1)) != b"\x00":
      raise TagError(x, b"\x00")

    self.seek(1)

  def read_bool(self) -> bool:
    value = self.peek(1)

    # bool doesnt have an tag, but this is better for SchemaReader.get_value to handle
    if value not in b"\x01\x02":
      raise TagError(value, "01 or 02")

    self.seek(1)
    return value == b"\x02"

  def read_float(self) -> float:
    lower = self.read_int(tag=b"\x04", signed=False)
    upper = self.read_int(tag=b"", signed=False)

    raw_bytes = struct.pack("<II", lower, upper)
    return struct.unpack("<d", raw_bytes)[0]

  def read_varint(self) -> int:
    return self.read_int(tag=b"\x03")

  def read_string(self) -> str:
    length = self.read_int(tag=b"", max_length=2) - 5

    if not length:
      return ""

    result = bytes([b ^ ((255 - i) & 0xFF) for i, b in enumerate(self.read(length))])
    return result.decode("utf-8", errors="replace")

  def read_array(self, error: bool = True) -> list[int | float | str]:
    if (x := self.peek(1)) != b"\x01":
      message = TagError(x, b"\x01")

      if error:
        raise message

      print(message)
      return []

    # blank array
    if (x := self.peek(2)) == b"\x01\t":
      self.seek(3)
      return []

    self.seek(2)
    length = self.read_int(tag=b"") - 1
    self.seek(1)  # \x00
    result: list[int | float | str] = []

    for _ in range(length):
      tag = self.peek(1)

      if tag == b"\x03":
        value = self.read_varint()

      elif tag == b"\x04":
        value = self.read_float()

      else:
        value = self.read_string()

      result.append(value)

    return result

  def read_dict(self, error: bool = True) -> dict[str, int | float | str]:
    if (x := self.peek(1)) != b"\x01":
      message = TagError(x, b"\x01")

      if error:
        raise message

      print(message)
      return {}

    if (x := self.peek(2)) == b"\x01\t":
      self.seek(3)
      return {}

    self.seek(1)
    length = self.read_int(tag=b"") - 1
    self.seek(1)
    result: dict[str, int | float | str] = {}

    for _ in range(length):
      key = self.read_string()
      tag = self.peek(1)

      if tag == b"\x03":
        value = self.read_varint()

      elif tag == b"\x04":
        value = self.read_float()

      else:
        value = self.read_string()

      result[key] = value

    return result
