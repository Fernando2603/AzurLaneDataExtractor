import hashlib
from pathlib import Path
from typing import cast

import requests
from azlassets import config, protobuf, versioncontrol
from azlassets.classes import Client


def get_version(clientconfig: config.ClientConfig) -> versioncontrol.VersionResult:
  response = protobuf.get_version_response(  # type: ignore
    clientconfig.gateip, clientconfig.gateport
  )

  if response is None:
    raise ValueError("failed to get version response")

  for v in response.pb.version:
    if not v.startswith("$"):
      continue

    x = versioncontrol.parse_version_string(v)

    if x.version_type == versioncontrol.VersionType.AZL:
      return x

  raise ValueError("Failed to get game version")


if __name__ == "__main__":
  clientconfig = config.load_client_config(Client.EN)
  version = get_version(clientconfig)
  dst = Path(__file__).parent / "target"
  url = f"{clientconfig.cdnurl}/android/hash/{version.rawstring}"
  res = requests.get(url, headers={"user-agent": ""})

  for hashrow in versioncontrol.parse_hash_rows(res.content.decode("utf-8")):
    if (hashrow.filepath != "scripts32") and not hashrow.filepath.startswith("sharecfgdata"):
      continue

    path = dst / hashrow.filepath

    if path.exists() and (hashlib.md5(path.read_bytes()).hexdigest() == hashrow.md5hash):
      print(f"Skip -> {path.relative_to(dst.parent).as_posix()}")
      continue

    file_url = f"{clientconfig.cdnurl}/android/resource/{hashrow.md5hash}"
    response = requests.get(file_url)

    if (x := len(response.content)) != hashrow.size:
      raise ValueError(
        f"{hashrow.filepath} invalid response size, got {x}, expected {hashrow.size}"
      )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(cast(bytes, response.content))
    print(f"Write -> {path.relative_to(dst.parent).as_posix()}")

  (dst / "version.txt").write_text(version.version, encoding="utf-8")
