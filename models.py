from dataclasses import dataclass
import re


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


@dataclass(eq=False)
class GluedSticker:
    sticker: Sticker
    discriminator: str | None
    name_override: str | None
    description_override: str | None


@dataclass(eq=False)
class Collector:
    id: str
    nickname: str
    discord_uid: int | None
    forum_id: int | None
    facebook_id: int | None
    youtube_id: str | None
    album: list[GluedSticker]

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Collector) and hash(self) == hash(value)
