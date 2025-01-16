###
# Because the logic of the commands is short, for simplicity they were all placed in the same file.
###
import datetime
import discord
from typing import Optional, Dict

from discord.channel import CategoryChannel
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands
from ezjsonpy import translate_message
from loguru import logger

from ....database import Database
from ....utilities import Validators, PlayerUUIDFormat, PlayerUUID
from ...utilities.channel import ChannelUtils
from ...utilities.categories import CategoriesUtils
from ...utilities.embed import EmbedUtilities
from ....constants import URLConstants, AccountStatus, CategoriesConstants, BotConstants
from ....models import User


class BotCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='nick', description=translate_message('commands.nick.description'))
    @logger.catch
    async def nick_command(self, interaction: discord.Interaction, username: str, price: int) -> None:
        """
        Add username to database.

        :param interaction: The interaction object.
        :param username: The username to add.
        :param int: Account price
        """
        if not Validators.has_permissions_role(user=interaction.user, guild=interaction.guild):
            await interaction.response.send_message(translate_message('noPerms'), ephemeral=True)
            return
        
        if not Validators.validate_username(username=username):
            await interaction.response.send_message(content=translate_message('invalidUsername'), ephemeral=True)
            return
            
        if Database().account_exists(nick=username):
            await interaction.response.send_message(content=translate_message('commands.nick.accountExists'), ephemeral=True)
            return
        
        if price <= 0:
            await interaction.response.send_message(content=translate_message('commands.nick.invalidPrice'), ephemeral=True)
            return
        
        Database().add_account(nick=username, price=price)
        category: Optional[CategoryChannel] = await CategoriesUtils.get_category('for_sale', interaction.guild)
        
        if category is None:
            logger.warning(translate_message('categoryNotFound').replace('$category', 'sales').replace('$command', 'nick'))
            await interaction.response.send_message(translate_message('commandError'), ephemeral=True)
            return
        
        channel_id: Optional[int] = await ChannelUtils.create_username_channel(
            username=username,
            price=str(price),
            category=category,
            guild=interaction.guild
        )
        
        if channel_id is None:
            return
        
        Database().link_discord_channel(nick=username, channel_id=channel_id)
        uuid: PlayerUUIDFormat = PlayerUUID(username=username).get_uuid()
        username_uuid: str = uuid.online_uuid if uuid.online_uuid else uuid.offline_uuid
        embed: discord.Embed = EmbedUtilities.create_embed(
            title=translate_message('commands.nick.embed.title'),
            description=translate_message('commands.nick.embed.description').replace('$name', username),
            thumbnail=f'{URLConstants.MCHEADS.replace("$uuid", username_uuid)}',
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='sold', description=translate_message('commands.sold.description'))
    @logger.catch
    async def sold_command(self, interaction: discord.Interaction, buyer: str) -> None:
        """
        Set an account to sold status in database

        :param interaction: The interaction object.
        :param buyer: The buyer of the account.
        """
        if not Validators.has_permissions_role(user=interaction.user, guild=interaction.guild):
            await interaction.response.send_message(translate_message('noPerms'), ephemeral=True)
            return
        
        channel_name: str = interaction.channel.name
        new_channel_name: str = channel_name.replace('💲', '❌')
        is_nick_channel: tuple[bool, Optional[str]] = ChannelUtils.nick_channel(channel_name=channel_name)
        
        if not is_nick_channel[0]:
            await interaction.response.send_message(translate_message('noAccountChannel'), ephemeral=True)
            return
        
        if '❌' in channel_name:
            await interaction.response.send_message(translate_message('alreadySold'), ephemeral=True)
            return
        
        nick: str = is_nick_channel[1]
        account_data: User = Database().get_account(nick=nick)
        
        if account_data.status == AccountStatus.INACTIVE:
            await interaction.response.send_message(translate_message('inactiveAccount'), ephemeral=True)
            return
        
        category: Optional[CategoryChannel] = await CategoriesUtils.get_category('sold', interaction.guild)
        
        if category is None:
            logger.warning(translate_message('categoryNotFound').replace('$category', 'sold').replace('$command', 'sold'))
            await interaction.response.send_message(translate_message('commandError'), ephemeral=True)
            return
        
        await interaction.channel.edit(name=new_channel_name, category=category)
        Database().set_buyer(nick=nick, buyer=buyer)
        Database().update_account_status(nick=nick, status=AccountStatus.SOLD)
        await interaction.response.send_message(translate_message('commands.sold.success'), ephemeral=True)

    @app_commands.command(name='reserve', description=translate_message('commands.reserve.description'))
    @logger.catch
    async def reserve_command(self, interaction: discord.Interaction) -> None:
        """
        Set an account to reservation status in database

        :param interaction: The interaction object.
        """
        if not Validators.has_permissions_role(user=interaction.user, guild=interaction.guild):
            await interaction.response.send_message(translate_message('noPerms'), ephemeral=True)
            return
        
        channel_name: str = interaction.channel.name
        is_nick_channel: tuple[bool, Optional[str]] = ChannelUtils.nick_channel(channel_name=channel_name)
        
        if not is_nick_channel[0]:
            await interaction.response.send_message(translate_message('noAccountChannel'), ephemeral=True)
            return
        
        if '❌' in channel_name:
            await interaction.response.send_message(translate_message('alreadySold'), ephemeral=True)
            return
        
        account_data: User = Database().get_account(nick=is_nick_channel[1])
        
        if account_data.status == AccountStatus.INACTIVE:
            await interaction.response.send_message(translate_message('inactiveAccount'), ephemeral=True)
            return
                        
        reservations_category: Optional[CategoryChannel] = await CategoriesUtils.get_category('reservations', interaction.guild)
        for_sale_category: Optional[CategoryChannel] = await CategoriesUtils.get_category('for_sale', interaction.guild)
        new_category: Optional[CategoryChannel] = None
        
        if reservations_category is None:
            logger.warning(translate_message('categoryNotFound').replace('$category', 'reservations').replace('$command', 'reserve'))
            await interaction.response.send_message(translate_message('commandError'), ephemeral=True)
            return
        
        if for_sale_category is None:
            logger.warning(translate_message('categoryNotFound').replace('$category', 'sales').replace('$command', 'reserve'))
            await interaction.response.send_message(translate_message('commandError'), ephemeral=True)
            return
        
        new_category = for_sale_category if interaction.channel.category.id == CategoriesConstants.RESERVATIONS_CATEGORY_ID else reservations_category
        await interaction.channel.edit(category=new_category)
        
        if new_category.id == CategoriesConstants.RESERVATIONS_CATEGORY_ID:
            Database().update_account_status(nick=is_nick_channel[1], status=AccountStatus.RESERVED)
            await interaction.response.send_message(translate_message('commands.reserve.success'), ephemeral=True)
            
        else:
            Database().update_account_status(nick=is_nick_channel[1], status=AccountStatus.SALE)
            await interaction.response.send_message(translate_message('commands.reserve.removeReservation'), ephemeral=True)
        
    @app_commands.command(name='inactive', description=translate_message('commands.inactive.description'))
    @logger.catch
    async def inactive_command(self, interaction: discord.Interaction, reason: str = 'Default') -> None:
        """
        Set an account to inactive status in database

        :param interaction: The interaction object.
        :param reason: Reason for inactivity
        """
        if not Validators.has_permissions_role(user=interaction.user, guild=interaction.guild):
            await interaction.response.send_message(translate_message('noPerms'), ephemeral=True)
            return
        
        channel_name: str = interaction.channel.name
        is_nick_channel: tuple[bool, Optional[str]] = ChannelUtils.nick_channel(channel_name=channel_name)
        
        if not is_nick_channel[0]:
            await interaction.response.send_message(translate_message('noAccountChannel'), ephemeral=True)
            return
        
        if '❌' in channel_name:
            await interaction.response.send_message(translate_message('alreadySold'), ephemeral=True)
            return
        
        account_data: User = Database().get_account(nick=is_nick_channel[1])
        
        if account_data.status != AccountStatus.INACTIVE:
            Database().update_account_status(nick=is_nick_channel[1], status=AccountStatus.INACTIVE)
            Database().set_inactive_reason(nick=is_nick_channel[1], reason=reason)
            await interaction.response.send_message(translate_message('commands.inactive.success'), ephemeral=True)
            
        else:
            Database().update_account_status(nick=is_nick_channel[1], status=AccountStatus.SALE)
            await interaction.response.send_message(translate_message('commands.inactive.removeInactivity'), ephemeral=True) 

    @app_commands.command(name='list', description=translate_message('commands.list.description'))
    @logger.catch
    async def list_users_command(self, interaction: discord.Interaction) -> None:
        """
        Lists users in pages, 10 per page, and allows navigation between pages with buttons.
        
        :param interaction: The interaction object.
        """
        if not Validators.has_permissions_role(user=interaction.user, guild=interaction.guild):
            await interaction.response.send_message(translate_message('noPerms'), ephemeral=True)
            return
        
        accounts_by_status: Dict[str, list] = {
            AccountStatus.SALE: [],
            AccountStatus.RESERVED: [],
            AccountStatus.SOLD: [],
            AccountStatus.INACTIVE: [],
        }
        all_accounts: list = Database().get_accounts()

        for account in all_accounts:            
            if account.status == AccountStatus.SALE:
                accounts_by_status[AccountStatus.SALE].append(account)
            elif account.status == AccountStatus.RESERVED:
                accounts_by_status[AccountStatus.RESERVED].append(account)
            elif account.status == AccountStatus.SOLD:
                accounts_by_status[AccountStatus.SOLD].append(account)
            elif account.status == AccountStatus.INACTIVE:
                accounts_by_status[AccountStatus.INACTIVE].append(account)

        for status in accounts_by_status:
            accounts_by_status[status].sort(key=lambda account: account.price, reverse=True)

        all_grouped_accounts = (
            accounts_by_status[AccountStatus.SALE] +
            accounts_by_status[AccountStatus.RESERVED] +
            accounts_by_status[AccountStatus.SOLD] +
            accounts_by_status[AccountStatus.INACTIVE]
        )

        view: PaginationView = PaginationView(all_grouped_accounts)
        await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True, delete_after=600)
        
    @app_commands.command(name='status', description=translate_message('commands.status.description'))
    @logger.catch
    async def status_command(self, interaction: discord.Interaction, username: str) -> None:
        """
        Set an account to inactive status in database

        :param interaction: The interaction object.
        :param username: The username to view.
        """
        if not Validators.has_permissions_role(user=interaction.user, guild=interaction.guild):
            await interaction.response.send_message(translate_message('noPerms'), ephemeral=True)
            return
        
        if not Validators.validate_username(username=username):
            await interaction.response.send_message(content=translate_message('invalidUsername'), ephemeral=True)
            return
            
        if not Database().account_exists(nick=username):
            await interaction.response.send_message(content=translate_message('commands.status.accountNotFound'), ephemeral=True)
            return
        
        dynamic_data: dict = {
            AccountStatus.SALE: {
                'color': discord.Color.green(),
            },
            AccountStatus.SOLD: {
                'color': discord.Color.dark_orange(),
            },
            AccountStatus.RESERVED: {
                'color': discord.Color.dark_magenta(),
            },
            AccountStatus.INACTIVE: {
                'color': discord.Color.dark_red(),
            },
        }

        user_data: User = Database().get_account(nick=username)
        uuid: PlayerUUIDFormat = PlayerUUID(username=username).get_uuid()
        username_uuid: str = uuid.online_uuid if uuid.online_uuid else uuid.offline_uuid
        embed: discord.Embed = EmbedUtilities.create_embed(
            title=translate_message('commands.status.embed.title').replace('$name', user_data.nick),
            description=translate_message('commands.status.embed.description').replace('$name', user_data.nick),
            color=dynamic_data[user_data.status]['color'],
            thumbnail=f'{URLConstants.MCHEADS.replace("$uuid", username_uuid)}',
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            footer=f'Account created on {user_data.created_at}',
            fields=[
                {'name': 'Status', 'value': user_data.status, 'inline': True}
            ]
        )
        
        if user_data.status == AccountStatus.INACTIVE:
            embed.add_field(name='Reason for inactivity', value=user_data.reason_inactive, inline=True)
            
        if user_data.status == AccountStatus.SOLD:
            embed.add_field(name='Account Buyer', value=user_data.buyer, inline=True)
            
        await interaction.response.send_message(content=' ', embed=embed, ephemeral=True)

    @app_commands.command(name='remove', description=translate_message('commands.remove.description'))
    @logger.catch
    async def remove_command(self, interaction: discord.Interaction, password: str) -> None:
        """
        Delete account from database.

        :param interaction: The interaction object.
        :param password: The password of this command.
        """
        if not Validators.has_permissions_role(user=interaction.user, guild=interaction.guild):
            await interaction.response.send_message(translate_message('noPerms'), ephemeral=True)
            return
        
        channel_name: str = interaction.channel.name
        is_nick_channel: tuple[bool, Optional[str]] = ChannelUtils.nick_channel(channel_name=channel_name)
        
        if not is_nick_channel[0]:
            await interaction.response.send_message(translate_message('noAccountChannel'), ephemeral=True)
            return
        
        if password != BotConstants.REMOVE_PASSWORD:
            await interaction.response.send_message(translate_message('commands.remove.invalidPassword'), ephemeral=True)
            return
        
        Database().remove_account(nick=is_nick_channel[1])
        await interaction.channel.delete(reason='User removed from database')
        

class PaginationView(View):
    def __init__(self, users: list, user_per_page: int = 15):
        super().__init__(timeout=600)
        self.users: list = users
        self.user_per_page: int = user_per_page
        self.current_page: int = 0

    def get_embed(self) -> discord.Embed:
        """
        Generate the embed to show the users of the current page
        
        :return embed: Full embed to send
        """
        start: int = self.current_page * self.user_per_page
        end: int = start + self.user_per_page
        page_users: list = self.users[start:end]
        status_to_emoji: Dict[str, str] = {
            AccountStatus.SALE: '🟢',
            AccountStatus.RESERVED: '🟠',
            AccountStatus.SOLD: '🔴',
            AccountStatus.INACTIVE: '⚪',
        }
        embed: discord.Embed = EmbedUtilities.create_embed(
            title=translate_message('commands.list.embed.title'),
            description=translate_message('commands.list.embed.description').replace('$accounts', str(len(self.users))),
            footer=f'Page {self.current_page + 1} of {(len(self.users) + self.user_per_page - 1) // self.user_per_page}',
            color=discord.Color.magenta(),
        )
        previous_status: Optional[str] = None
        
        for user in page_users:
            emoji: str = status_to_emoji.get(user.status, '⚫')

            if user.status != previous_status:
                if previous_status is not None:
                    embed.description = f'{embed.description}\n'
            
            embed.description = f'{embed.description}\n{emoji} {user.nick} - ({user.status})'
            previous_status = user.status
                
        return embed

    @discord.ui.button(label=translate_message('commands.list.embed.buttons.previous'), style=discord.ButtonStyle.blurple)
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        """
        Button to go to the previous page
        
        :param interaction: The interaction object.
        :param button: Button
        """
        if self.current_page == 0:
            await interaction.response.send_message(translate_message('commands.list.embed.buttons.previousLimit'), ephemeral=True)
            return

        self.current_page -= 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label=translate_message('commands.list.embed.buttons.next'), style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        """
        Button to go to the next page
        
        :param interaction: The interaction object.
        :param button: Button
        """
        if self.current_page == (len(self.users) + self.user_per_page - 1) // self.user_per_page - 1:
            await interaction.response.send_message(translate_message('commands.list.embed.buttons.nextLimit'), ephemeral=True)
            return

        self.current_page += 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)


async def setup(bot: commands.Bot) -> None:
    """Load the Cog with the commands."""
    await bot.add_cog(BotCommands(bot))
