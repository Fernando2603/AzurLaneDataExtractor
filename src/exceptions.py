class TagError(Exception):
  """
  Raised when tag value doesn't match
  """

  def __init__(self, tag: str | bytes, expect: str | bytes) -> None:
    if isinstance(tag, bytes):
      tag = tag.hex()

    if isinstance(expect, bytes):
      expect = expect.hex()

    super().__init__(f"Unexpected tag {tag}, expected {expect}")


class PositionNotFound(Exception):
  """
  Raised when SchemaReader.set_position failed
  """
