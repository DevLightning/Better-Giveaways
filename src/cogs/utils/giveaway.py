from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict, Optional, List, Union, overload

import discord  # type: ignore
from discord.ext import vbu  # type: ignore


class GiveawayDict(TypedDict):
    """
    A typed dictionary for the Giveaway dataclass.
    """

    # NOTE: Make sure this is equal to the Giveaway dataclass.
    guild_id: int
    channel_id: int
    message_id: int
    ends_at: datetime
    reward: str


@dataclass
class Giveaway:
    """
    A giveaway data class.

    Attributes
    ----------
    guild_id : int
        The ID of the guild that the giveaway is hosted in.
    channel_id : int
        The ID of the channel that the giveaway is hosted in.
    message_id : int
        The ID of the message containing the giveaway.
    ends_at : datetime.datetime
        The date and time at which the giveaway ends.
    """

    guild_id: int
    channel_id: int
    message_id: int
    ends_at: datetime
    reward: str

    @property
    def message_url(self) -> str:
        return f"https://discordapp.com/channels/{self.guild_id}/{self.channel_id}/{self.message_id}"

    @classmethod
    def from_dict(cls, data: GiveawayDict) -> Giveaway:
        """
        Create a new instance of the Giveaway class from a dictionary.

        Parameters
        ----------
        data : GiveawayDict
            The dictionary containing the giveaway's information.

        Returns
        -------
        Giveaway
            The new instance of the Giveaway class.
        """

        return cls(**data)

    @classmethod
    async def from_database(
        cls,
        db: vbu.DatabaseConnection,
        guild_id: int,
        channel_id: int,
        message_id: int,
    ) -> Optional[Giveaway]:
        """
        Fetch a giveaway from the database.

        Parameters
        ----------
        db : vbu.DatabaseConnection
            The database connection to use.
        guild_id : int
            The ID of the guild that the giveaway is hosted in.
        channel_id : int
            The ID of the channel that the giveaway is hosted in.
        message_id : int
            The ID of the message containing the giveaway.

        Returns
        -------
        Giveaway
            The new instance of the Giveaway class.
        None
            If the giveaway does not exist in the database.
        """

        # NOTE: We can pretty safely assume that there's either 0 or 1 entries in this `payload` list.
        payload = await db(
            """
            SELECT * FROM giveaways WHERE guild_id = $1 AND channel_id = $2 AND message_id = $3
            """,
            guild_id,
            channel_id,
            message_id,
        )

        try:
            data = payload[0]
            return cls.from_dict(data)
        except IndexError:
            return None

    async def update(self, db: vbu.DatabaseConnection) -> None:
        """
        Update the database with the giveaway's information.

        Parameters
        ----------
        db : vbu.DatabaseConnection
            The database connection to use.

        Returns
        -------
        None
        """

        await db(
            """
            INSERT INTO giveaways
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (
                guild_id, channel_id, message_id
            ) DO UPDATE SET
                guild_id = $1,
                channel_id = $2,
                message_id = $3,
                ends_at = $4,
                reward = $5
            """,
            self.guild_id,
            self.channel_id,
            self.message_id,
            self.ends_at,
            self.reward,
        )

    async def end(self, db: vbu.DatabaseConnection, bot: vbu.Bot) -> None:
        """
        End the giveaway.

        Parameters
        ----------
        db : vbu.DatabaseConnection
            The database connection to use.

        Returns
        -------
        None
        """

        # Delete the giveaway from the database.
        await db(
            """
            DELETE FROM giveaways
            WHERE guild_id = $1 AND channel_id = $2 AND message_id = $3
            """,
            self.guild_id,
            self.channel_id,
            self.message_id,
        )

        # Respond to the giveaway message with the winner.
        channel = bot.get_channel(self.channel_id)
        if channel is None:
            return
        try:
            message = await channel.fetch_message(self.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return
        await message.reply(f"{self.reward} has been given to the winner!")


@overload
async def get_giveaways(
    db: vbu.DatabaseConnection, *, guild: Optional[Union[discord.Guild, int]]
) -> Optional[List[Giveaway]]:
    ...


@overload
async def get_giveaways(
    db: vbu.DatabaseConnection, *, channel: Optional[Union[discord.TextChannel, int]]
) -> Optional[List[Giveaway]]:
    ...


@overload
async def get_giveaways(
    db: vbu.DatabaseConnection, *, message: Optional[Union[discord.PartialMessage, int]]
) -> Optional[Giveaway]:
    ...


@overload
async def get_giveaways(db: vbu.DatabaseConnection) -> Optional[List[Giveaway]]:
    ...


async def get_giveaways(
    db: vbu.DatabaseConnection,
    *,
    guild: Union[discord.Guild, int] = None,
    channel: Union[discord.TextChannel, int] = None,
    message: Union[discord.PartialMessage, int] = None,
) -> Optional[Union[List[Giveaway], Giveaway]]:
    """
    Fetch a list of giveaways from the database.

    Parameters
    ----------
    db : vbu.DatabaseConnection
        The database connection to use.
    guild : Union[discord.Guild, int]
        The guild to fetch giveaways from.
    channel : Union[discord.TextChannel, int]
        The channel to fetch giveaways from.
    message : Union[discord.PartialMessage, int]
        The message to fetch giveaways from.

    Returns
    -------
    List[Giveaway]
        The list of giveaways.

    Raises
    ------
    ValueError
        If you don't provide exactly one of `guild`, `channel`, or `message`.
    """

    if len([arg for arg in (guild, channel, message) if arg is not None]) > 1:
        raise ValueError(
            "Must provide at most one of `guild`, `channel`, or `message`."
        )

    if guild is not None:
        guild_id = guild.id if isinstance(guild, discord.Guild) else guild
        payload = await db(
            """
            SELECT * FROM giveaways WHERE guild_id = $1
            """,
            guild_id,
        )
    elif channel is not None:
        channel_id = channel.id if isinstance(channel, discord.TextChannel) else channel
        payload = await db(
            """
            SELECT * FROM giveaways WHERE channel_id = $1
            """,
            channel_id,
        )
    elif message is not None:
        message_id = (
            message.id if isinstance(message, discord.PartialMessage) else message
        )
        payload = await db(
            """
            SELECT * FROM giveaways WHERE message_id = $1
            """,
            message_id,
        )
    else:
        payload = await db(
            """
            SELECT * FROM giveaways
            """
        )

    return [Giveaway.from_dict(data) for data in payload]
