import subprocess
import os
import sys

import discord
from loguru import logger
from discord.ext.commands.bot import Bot
from ezjsonpy import load_language, set_language

from .bot import DiscordBot
from .constants import BotConstants
from .database import Database


class Main:
    def __init__(self, debug: bool = False) -> None:
        self.debug: bool = debug
        subprocess.run('clear || cls', shell=True)
        
        if not os.path.exists('lang.json'):
            print('Lang.json file not found!')
            sys.exit(1)
        
        load_language('lang', 'lang.json')
        set_language('lang')
        self.logger_setup()
        self._bot: Bot = DiscordBot.create_bot(
            command_prefix='!!!!!!!!!!!!!!',
            help_command=None,
            intents=discord.Intents.all()
        )
        self._start_bot()

    @logger.catch
    def logger_setup(self) -> None:
        """Setup the logger."""
        logger.add(
            'debug.log',
            format='[{time:YYYY-MM-DD HH:mm:ss} {level} - {file}, {line}] ⮞ <level>{message}</level>',
            retention='16 days',
            rotation='12:00',
            enqueue=True
        )

    @logger.catch
    def _start_bot(self) -> None:
        """Start the mcptoolbot."""
        if BotConstants.TOKEN is None:
            logger.critical('No token found. Please set the DISCORD_TOKEN environment variable in a .env file.')
            sys.exit(1)

        Database()  # Initialize the database and test the connection
        self._bot.run(BotConstants.TOKEN)
