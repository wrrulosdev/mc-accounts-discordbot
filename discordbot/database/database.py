import sqlite3
import sys
import os

from typing import Optional
from contextlib import contextmanager

from loguru import logger

from ..models import User
from ..constants import BotConstants


class Database:
    def __init__(self) -> None:
        if not os.path.exists('db'):
            os.makedirs('db')

        if not os.path.exists(f'db/{BotConstants.DB_FILENAME}'):
            open(f'db/{BotConstants.DB_FILENAME}', 'w').close()

        try:
            self.conn: sqlite3.Connection = sqlite3.connect(f'db/{BotConstants.DB_FILENAME}')

        except sqlite3.Error as e:
            logger.critical(f'Failed to connect to the database: {e}')
            sys.exit(1)

        self._create_table()

    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursor."""
        cursor: Optional[sqlite3.Cursor] = None

        try:
            cursor = self.conn.cursor()
            yield cursor

        except sqlite3.Error as e:
            logger.error(f'Database error: {e}')
            self.conn.rollback()
            raise

        finally:
            if cursor:
                cursor.close()

    def _create_table(self) -> None:
        """Creates the users table if it doesn't exist."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nick TEXT NOT NULL,
                    status TEXT NOT NULL,
                    price INTEGER,
                    sold_to TEXT,
                    reason_inactive TEXT,
                    discord_channel_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                ''')
                self.conn.commit()

        except sqlite3.Error as e:
            logger.critical(f'Failed to create table: {e}')
            sys.exit(1)
    def _execute_query(self, query: str, params: tuple = ()) -> None:
        """
        Executes an insert or update query on the database.

        :param query: The SQL query to execute.
        :param params: The parameters for the query, default is an empty tuple.
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(query, params)
                self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f'Error executing query: {e}')

    def _fetch_data(self, query: str, params: tuple = ()) -> list:
        """
        Fetches data from the database.

        :param query: The SQL query to fetch data.
        :param params: The parameters for the query, default is an empty tuple.
        :return: A list of tuples containing the fetched data.
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f'Error fetching data: {e}')
            return []
        
    def add_account(self, nick: str, price: int = None) -> None:
        """
        Adds a new account with 'FOR SALE' as the default status and prevents other statuses.

        :param nick: The nickname of the account.
        :param price: The price of the account, default is None.
        """
        status: str = 'FOR SALE'
        self._execute_query('''
        INSERT INTO accounts (nick, status, price)
        VALUES (?, ?, ?);
        ''', (nick, status, price))
        
    def update_account_status(self, nick: str, status: str) -> None:
        """
        Updates the status of an existing account.

        :param nick: The nickname of the account.
        :param status: The new status for the account.
        """
        self._execute_query('''
        UPDATE accounts
        SET status = ?
        WHERE LOWER(nick) = LOWER(?);
        ''', (status, nick))
        
    def link_discord_channel(self, nick: str, channel_id: int) -> None:
        """
        Links a Discord channel to an account.

        :param nick: The nickname of the account.
        :param channel_id: The ID of the Discord channel to link.
        """
        self._execute_query('''
        UPDATE accounts
        SET discord_channel_id = ?
        WHERE LOWER(nick) = LOWER(?);
        ''', (channel_id, nick))
        
    def set_buyer(self, nick: str, buyer: str) -> None:
        """
        Sets the buyer of an account.

        :param nick: The nickname of the account.
        :param buyer: The buyer's name.
        """
        self._execute_query('''
        UPDATE accounts
        SET sold_to = ?
        WHERE LOWER(nick) = LOWER(?);
        ''', (buyer, nick))
        
    def set_inactive_reason(self, nick: str, reason: str) -> None:
        """
        Sets the reason for an account's inactivity.

        :param nick: The nickname of the account.
        :param reason: The reason for inactivity.
        """
        self._execute_query('''
        UPDATE accounts
        SET reason_inactive = ?
        WHERE LOWER(nick) = LOWER(?);
        ''', (reason, nick))
        
    def account_exists(self, nick: str) -> bool:
        """
        Checks if an account with the given nick already exists in the database, ignoring case.

        :param nick: The nickname of the account to check.
        :return: True if the account exists, otherwise False.
        """
        query: str = 'SELECT COUNT(*) FROM accounts WHERE LOWER(nick) = LOWER(?);'
        result: list = self._fetch_data(query, (nick,))
        return result[0][0] > 0

    def remove_account(self, nick: str) -> None:
        """
        Removes an account by its nick.

        :param nick: The nickname of the account to remove.
        """
        self._execute_query('''
        DELETE FROM accounts
        WHERE LOWER(nick) = LOWER(?);
        ''', (nick,))
        logger.info(f'Account with nick "{nick}" removed successfully.')
    
    def get_account(self, nick: str) -> User:
        """
        Fetches an account by its nick.

        :param nick: The nickname of the account to fetch.
        :return: A User object representing the account.
        """
        query: str = 'SELECT id, nick, status, price, sold_to, reason_inactive, discord_channel_id, created_at FROM accounts WHERE LOWER(nick) = LOWER(?)'
        user_data: list = self._fetch_data(query, (nick,))
        user: User = User(
            id=user_data[0][0],
            nick=user_data[0][1],
            status=user_data[0][2],
            price=user_data[0][3],
            buyer=user_data[0][4],
            reason_inactive=user_data[0][5],
            discord_channel_id=user_data[0][6],
            created_at=user_data[0][7]
        )
        return user
    
    def get_accounts(self, status: Optional[str] = None) -> list:
        """
        Lists accounts filtered by status and returns a list of User objects.

        :param status: The status to filter accounts by (optional).
        :return: A list of User objects representing the accounts.
        """
        query: str = 'SELECT id, nick, status, price, sold_to, reason_inactive, discord_channel_id, created_at FROM accounts'

        if status:
            query += ' WHERE status = ?'

        user_data_list: list = self._fetch_data(query, (status,) if status else ())

        users: list = []
        for user_data in user_data_list:
            user: User = User(
                id=user_data[0],
                nick=user_data[1],
                status=user_data[2],
                price=user_data[3],
                buyer=user_data[4],
                reason_inactive=user_data[5],
                discord_channel_id=user_data[6],
                created_at=user_data[7]
            )
            users.append(user)
        
        return users

    def _close(self) -> None:
        """Closes the database connection."""
        try:
            self.conn.close()
            logger.info('Database connection closed successfully.')

        except sqlite3.Error as e:
            logger.error(f'Failed to close database connection: {e}')
