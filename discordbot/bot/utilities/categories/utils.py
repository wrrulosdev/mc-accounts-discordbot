from typing import Optional

import discord
from loguru import logger
from discord.ext import commands
from discord.guild import Guild
from discord.channel import CategoryChannel

from ....constants import CategoriesConstants


class CategoriesUtils:
    @staticmethod
    async def get_category(name: str, guild: Guild) -> Optional[CategoryChannel]:
        """
        Fetches a category channel by its name from the provided guild.

        Based on the provided category name, it fetches the corresponding category ID 
        and then retrieves the CategoryChannel object from the guild. If the name is 
        invalid or the category is not found, an appropriate log message is generated 
        and None is returned.

        :param name: The name of the category to fetch ('for_sale', 'sold', or 'reservations').
        :param guild: The guild where the category channel is located.
        :return: The CategoryChannel object corresponding to the name if found, otherwise None.
        """
        category_id: Optional[int] = None
        
        if name == 'for_sale':
            category_id = CategoriesConstants.FOR_SALE_CATEGORY_ID
            
        elif name == 'sold':
            category_id = CategoriesConstants.SOLD_CATEGORY_ID
        
        elif name == 'reservations':
            category_id = CategoriesConstants.RESERVATIONS_CATEGORY_ID
            
        else:
            logger.warning('Invalid category name!')
            return None
        
        category: Optional[CategoryChannel] = discord.utils.get(guild.categories, id=int(category_id))
        
        if category is None:
            logger.error(f'Category channel not found. ID not found! {category_id}')
            return None
        
        return category
