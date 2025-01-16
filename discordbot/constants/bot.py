import os
from typing import Optional, Any

from dotenv import load_dotenv

load_dotenv()


class BotConstants:
    COGS_PATH: str = 'discordbot/bot/cogs'  # Change this if you rename the folder
    COG_PATH: str = 'discordbot.bot.cogs'  # Change this if you rename the folder
    TOKEN: Optional[str] = os.getenv('DISCORD_TOKEN')
    REMOVE_PASSWORD: Any = os.getenv('REMOVE_PASSWORD')
    PERMISSIONS_ROLE_ID: Any = os.getenv('PERMISSIONS_ROLE_ID')
    DB_FILENAME: str = 'accounts.db'


class ChannelConstants:
    POINTS_LOGS_CHANNEL: Any = os.getenv('POINTS_LOGS_CHANNEL')


class CategoriesConstants:
    FOR_SALE_CATEGORY_ID: Any = os.getenv('FOR_SALE_CATEGORY_ID')
    SOLD_CATEGORY_ID: Any = os.getenv('SOLD_CATEGORY_ID')
    RESERVATIONS_CATEGORY_ID: Any = os.getenv('RESERVATIONS_CATEGORY_ID')
    

class AccountStatus:
    SALE: str = 'FOR SALE'
    RESERVED: str = 'RESERVERD'
    SOLD: str = 'SOLD'
    INACTIVE: str = 'INACTIVE'


class URLConstants:
    MCHEADS: str = 'https://mc-heads.net/avatar/$uuid/100/nohelm'


class IDs:
    ADMIN_IDS: list[int] = [1257797619078660096, 772531685438783539]
