from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

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


def get_previous_version() -> str:
  response = requests.get(
    "https://raw.githubusercontent.com/Fernando2603/AzurLaneData/main/version.txt"
  )

  if response.status_code != 200:
    return ""

  return response.text


def check():
  with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
    clientconfig = config.load_client_config(Client.EN)
    version = get_version(clientconfig)

  print(version.version, version.version == get_previous_version())


if __name__ == "__main__":
  check()
