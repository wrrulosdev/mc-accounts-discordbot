from typing import Optional

import discord
from loguru import logger
from discord.ext import commands
from discord.guild import Guild
from discord.channel import CategoryChannel, TextChannel

from ....database import Database


class ChannelUtils:
    @staticmethod
    async def get_channel_by_id(bot: commands.Bot, channel_id: int) -> Optional[discord.channel.TextChannel]:
        """
        Get a channel by its ID.

        :param bot: The bot.
        :param channel_id: The ID of the channel.
        :return: The channel if found, None otherwise.
        """
        return bot.get_channel(channel_id)

    @staticmethod
    @logger.catch
    async def create_username_channel(username: str, price: str, category: CategoryChannel, guild: Guild) -> Optional[int]:
        """
        Creates a text channel with a name based on the username and price in the specified category.

        :param username: The username to include in the channel name.
        :param price: The price to include in the channel name.
        :param category: The category where the channel will be created.
        :param guild: The guild where the channel will be created.
        :return: The channel ID if creation is successful, otherwise None.
        """
        try:
            channel: Optional[TextChannel] = await guild.create_text_channel(f'💲│{price}-{username}', category=category)
            return channel.id
            
        except Exception as e:
            logger.error(f'Error creating username channel. {e}')
            
        return None
    
    @staticmethod
    @logger.catch
    def nick_channel(channel_name: str) -> tuple[bool, Optional[str]]:
        """
        Extracts the username from a channel name and checks if the account exists.

        :param channel_name: The channel name to extract the username from.
        :return: A tuple (True, username) if valid, otherwise (False, None).
        """
        if '-' not in channel_name:
            return False, None
        
        try:
            nick: str = channel_name.split('-')[1]
            
        except IndexError:
            return False, None
        
        if not Database().account_exists(nick=nick):
            return False, None

        return True, nick

        
