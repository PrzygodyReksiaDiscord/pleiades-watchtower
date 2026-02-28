from dataclasses import dataclass
from dotenv import load_dotenv
import os
import re
import urllib.parse

import discord


@dataclass(eq=False)
class StickerCategory:
    title: str
    regex: re.Pattern[str]
    priority: int

    @staticmethod
    def from_serialized(priority: int, /, title: str, regex: str) -> 'StickerCategory':
        return StickerCategory(
            title,
            re.compile(regex),
            priority
        )


def _match_category(sticker_id: str, categories: list[StickerCategory]) -> StickerCategory:
    for category in categories:
        if re.fullmatch(category.regex, sticker_id) is not None:
            return category
        

load_dotenv()
STICKER_URL_PREFIX = os.getenv('STICKER_URL_PREFIX') or 'https://github.com/PrzygodyReksiaDiscord/pleiades-watchtower/blob/main/'
STICKER_URL_SUFFIX = os.getenv('STICKER_URL_SUFFIX') or '?raw=true'


@dataclass(eq=False)
class Sticker:
    id: str
    category: StickerCategory
    path: str
    author: str
    name: str
    description: str
    supersedes: list[str]
    unlisted: bool = False
#   embed_color: str | None

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Sticker) and hash(self) == hash(value)

    @staticmethod
    def from_serialized(id: str, categories: list[StickerCategory], /, path: str, author: str, name: str, description: str, supersedes = None, unlisted = False) -> 'Sticker':
        return Sticker(
            id,
            _match_category(id, categories),
            path,
            author,
            name,
            description,
            supersedes or [],
            unlisted
        )
    
    @property
    def url(self) -> str:
        return f'{STICKER_URL_PREFIX}{urllib.parse.quote(self.path)}{STICKER_URL_SUFFIX}'


@dataclass(eq=False)
class GluedSticker:
    sticker: Sticker
    discriminator: str | None
    name_override: str | None
    description_override: str | None
#   date_earned: datetime

    @property
    def name(self) -> str:
        return self.name_override or self.sticker.name

    @property
    def description(self) -> str:
        return self.description_override or self.sticker.description


@dataclass(eq=False)
class Collector:
    id: str
    nickname: str
    discord_uid: int | None
    forum_id: int | None
    facebook_id: int | None
    youtube_id: str | None
    album: list[GluedSticker]
#   description: str | None

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Collector) and hash(self) == hash(value)
    
    @property
    def discord_ping(self) -> str | None:
        if self.discord_uid:
            return f'<@{self.discord_uid}>'
    
    @property
    def forum_link(self) -> str | None:
        if self.forum_id:
            return f'https://www.przygodyreksia.aidemmedia.pl/pliki/kretes/forum/reksioforum/memberlist.php?mode=viewprofile&u={self.forum_id}'
    
    @property
    def facebook_link(self) -> str | None:
        if self.facebook_id:
            return f'https://www.facebook.com/profile.php?id={self.facebook_id}'
    
    @property
    def youtube_link(self) -> str | None:
        if self.youtube_id:
            return f'https://www.youtube.com/channel/{self.youtube_id}'


class ConcreteSnowflake(discord.abc.Snowflake):
    def __init__(self, id: int):
        super().__init__()
        self.id = id
