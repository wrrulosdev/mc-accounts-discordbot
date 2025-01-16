import re
from typing import Optional

from loguru import logger
from discord.member import Member
from discord.guild import Guild
from discord.role import Role

from ..constants import BotConstants


class Validators:
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validates if the username matches the allowed pattern (3-16 characters, letters, numbers, or underscores).

        :param username: The username to validate.
        :return: True if valid, otherwise False.
        """
        pattern: str = r'^[a-zA-Z0-9_]{3,16}$'
        
        if re.match(pattern, username):
            return True
        
        return False
    
    @staticmethod
    def has_permissions_role(user: Member, guild: Guild) -> bool:
        """
        Checks if the user has the permissions role in the guild.

        :param user: The user to check.
        :param guild: The guild where the role is assigned.
        :return: True if the user has the permissions role, otherwise False.
        """
        role: Optional[Role] = guild.get_role(int(BotConstants.PERMISSIONS_ROLE_ID))
        
        if role is None:
            logger.error('Permissions role id is invalid!')
            return False
        
        if not role in user.roles:
            return False
        
        return True
