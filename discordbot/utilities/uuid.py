import hashlib
import uuid
from json import JSONDecodeError
from typing import Optional

import requests


class PlayerUUIDFormat:
    def __init__(self, online_uuid: Optional[str], offline_uuid: Optional[str]) -> None:
        self.online_uuid: Optional[str] = online_uuid
        self.offline_uuid: Optional[str] = offline_uuid


class PlayerUUID:
    def __init__(self, username: str):
        self.username = username

    def get_uuid(self) -> PlayerUUIDFormat:
        """
        Method to get the UUID of the player
        :return: The UUID of the player
        """
        try:
            response: requests.Response = requests.get(
                f"https://api.mojang.com/users/profiles/minecraft/{self.username}")
            response.raise_for_status()
            return PlayerUUIDFormat(response.json()['id'], self._get_offline_uuid())

        except (JSONDecodeError, KeyError, requests.exceptions.HTTPError):
            return PlayerUUIDFormat(None, self._get_offline_uuid())

        except requests.exceptions.RequestException:
            return PlayerUUIDFormat(None, self._get_offline_uuid())

    def _get_offline_uuid(self) -> str:
        """
        Method to get the offline UUID of the player
        :return: The offline UUID of the player
        """
        return str(uuid.UUID(bytes=hashlib.md5(bytes(f'OfflinePlayer:{self.username}', 'utf-8')).digest()[:16],
                             version=3)).replace('-', '')