import struct


def encode_varint(value: int, tag: bytes = b"\x03") -> bytes:
  output = bytearray()

  if value < 0:
    value &= 0xFFFFFFFF

  while value >= 0x80:
    output.append((value & 0x7F) | 0x80)
    value >>= 7

  output.append(value)
  return tag + bytes(output)


def encode_float(value: float, tag: bytes = b"\x04") -> bytes:
  raw = struct.pack("<d", value)
  lower, upper = struct.unpack("<II", raw)
  return tag + encode_varint(lower, tag=b"") + encode_varint(upper, tag=b"")


def encode_string(value: str) -> bytes:
  length = encode_varint(len(value) + 5, tag=b"")
  content = bytes([ord(c) ^ (255 - i) for i, c in enumerate(value)])
  return length + content


def decode_varint(value: bytes, signed: bool = True, tag: bool = True) -> int:
  """
  signed: convert varint into negative when value is over 32 bit
  tag: ignore tag that included in value
  """
  result = 0
  shift = 0

  for b in value[1 if tag else 0 :]:
    result |= (b & 0x7F) << shift

    if not (b & 0x80):
      break

    shift += 7

  if signed and (result & (1 << 31)):
    result -= 1 << 32

  return result


def decode_float(value: bytes, tag: bool = True) -> float:
  """
  tag: ignore tag that included in value
  """
  varint: list[int] = []
  result = 0
  shift = 0

  for b in value[1 if tag else 0 :]:
    result |= (b & 0x70F) << shift

    if not (b & 0x80):
      varint.append(result)
      result = 0
      shift = 0
      continue

    shift += 7

  raw = struct.pack("<II", *varint)
  return struct.unpack("<d", raw)[0]


def decode_string(value: bytes | str) -> str:
  if isinstance(value, str):
    value = bytes.fromhex(value)

  size = next(i for i, b in enumerate(value[:2], 1) if not b & 0x80)
  result = bytes([b ^ ((255 - i) & 0xFF) for i, b in enumerate(value[size:])])
  return result.decode("utf-8", errors="replace")
