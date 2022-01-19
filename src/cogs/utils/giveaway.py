from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict, Optional, List, Union, overload

import discord  # type: ignore
from discord.ext import vbu  # type: ignore


class GiveawayRoleRewardDict(TypedDict):
    """
    A typed dictionary for the GiveawayReward dataclass.
    """

    # NOTE: Make sure this is equal to the GiveawayRoleReward dataclass.
    role_id: int


@dataclass
class GiveawayRoleReward:
    """
    A givaway role reward dataclass.

    Attributes
    ----------
    role_id : int
        The ID of the Discord role being rewarded.
    """

    role_id: int

    @classmethod
    def from_dict(cls, data: GiveawayRoleRewardDict) -> GiveawayRoleReward:
        return cls(**data)


class GiveawayDict(TypedDict):
    """
    A typed dictionary for the Giveaway dataclass.
    """

    # NOTE: Make sure this is equal to the Giveaway dataclass or it's typed dict if available.
    guild_id: int
    channel_id: int
    message_id: int
    ends_at: datetime
    role_rewards: Optional[List[GiveawayRoleRewardDict]]


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
    role_rewards: Optional[List[GiveawayRoleReward]] = None

    @staticmethod
    def __generate_id(guild_id: int, channel_id: int, message_id: int) -> str:
        return f"{guild_id}/{channel_id}/{message_id}"

    @property
    def _id(self) -> str:
        """
        Unique indentifier for the giveaway, based on the guild ID, channel
        ID, and message ID combined with a forward slash.

        Example
        -------
        >>> Giveaway(
        ...     123,
        ...     456,
        ...     789,
        ...     datetime.now(),
        ...     "Classic Nitro"
        ... )._id
        "123/456/789"

        Returns
        -------
        str
            The unique identifier.
        """

        return self.__generate_id(self.guild_id, self.channel_id, self.message_id)

    @property
    def message_url(self) -> str:
        """
        Generates a URL to the giveaway message. Equivelant to
        `https://discord.com/channels/{self.guild_id}/{self.channel_id}/{self.message_id}`.

        Returns
        -------
        str
            The URL.
        """

        return f"https://discord.com/channels/{self._id}"

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

        return cls(
            data["guild_id"],
            data["channel_id"],
            data["message_id"],
            data["ends_at"],
            [
                GiveawayRoleReward.from_dict(reward)
                for reward in data.get("role_rewards") or []
            ],
        )

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
            SELECT *
            FROM giveaways
            WHERE id = $1
            """,
            cls.__generate_id(guild_id, channel_id, message_id),
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
                id
            ) DO UPDATE SET
                id = $1,
                guild_id = $2,
                channel_id = $3,
                message_id = $4,
                ends_at = $5
            """,
            self._id,
            self.guild_id,
            self.channel_id,
            self.message_id,
            self.ends_at,
        )

        if self.role_rewards is not None:
            for reward in self.role_rewards:
                await db(
                    """
                    INSERT INTO giveaway_role_rewards
                    VALUES ($1, $2)
                    ON CONFLICT (role_id, giveaway_id) DO UPDATE SET
                        role_id = $1,
                        giveaway_id = $2
                    """,
                    reward.role_id,
                    self._id,
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
            WHERE id = $1
            """,
            self._id,
        )

        # Respond to the giveaway message with the winner.
        channel = bot.get_channel(self.channel_id)
        if channel is None:
            return
        try:
            # ? Reason for seemingly reduntant typehint: For some reason
            # ? `fetch_message` returns `Any |discord.Message`? Not sure why
            message: discord.Message = await channel.fetch_message(self.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

        try:
            reaction = next(
                reaction for reaction in message.reactions if reaction.emoji == "🎉"
            )
        except StopIteration:
            reaction = None
        finally:
            if reaction is None:
                return

        participants = [user async for user in reaction.users() if not user.bot]

        if not participants:
            await message.reply(
                f"Nobody joined :< `({len(participants)} participants)`"
            )
            return

        winner = random.choice(participants)

        await message.reply(
            f"**{winner.mention}** has won! ({len(participants)} participants)\ndebug: {self.role_rewards!r}"
        )


async def get_giveaway(db: vbu.DatabaseConnection, id: str) -> Optional[Giveaway]:
    """
    Fetch a giveaway from the database.

    Parameters
    ----------
    db : vbu.DatabaseConnection
        The database connection to use.
    id : str
        The ID of the giveaway.

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
        SELECT *
        FROM giveaways
        WHERE id = $1
        """,
        id,
    )

    try:
        data = payload[0]
        return Giveaway.from_dict(data)
    except IndexError:
        return None


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

    elif guild is not None:
        guild_id = guild.id if isinstance(guild, discord.Guild) else guild
        payload = await db(
            """
            SELECT *
            FROM giveaways
            WHERE guild_id = $1
            """,
            guild_id,
        )
    elif channel is not None:
        channel_id = channel.id if isinstance(channel, discord.TextChannel) else channel
        payload = await db(
            """
            SELECT *
            FROM giveaways
            WHERE channel_id = $1
            """,
            channel_id,
        )
    elif message is not None:
        message_id = (
            message.id if isinstance(message, discord.PartialMessage) else message
        )
        payload = await db(
            """
            SELECT *
            FROM giveaways
            WHERE message_id = $1
            """,
            message_id,
        )
    else:
        payload = await db(
            """
            SELECT * FROM giveaways
            """
        )

    payload = {row["id"]: dict(row) for row in payload}
    payload_role_rewards = await db(
        """
        SELECT *
        FROM giveaway_role_rewards
        WHERE giveaway_id = ANY($1::text[])
        """,
        list(payload),
    )
    for row in payload_role_rewards:
        payload_row = payload[row["giveaway_id"]]
        try:
            payload_row["role_rewards"].append({"role_id": row["role_id"]})
        except KeyError:
            payload_row["role_rewards"] = [{"role_id": row["role_id"]}]

    return [Giveaway.from_dict(data) for data in payload.values()]
