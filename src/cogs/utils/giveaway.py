from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict, Optional
from __future__ import annotations

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
            """
        )
