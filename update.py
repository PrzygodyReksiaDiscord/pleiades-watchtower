from dataclasses import dataclass
import logging
import os
import re

import discord
from dotenv import load_dotenv
import gspread
from gspread.utils import ValueRenderOption
import pyjson5

from models import StickerCategory, Sticker, GluedSticker, Collector
from paths import STICKERS_PATH, CATEGORIES_PATH


def try_int(s: str) -> int | None:
    try:
        return int(s)
    except:
        pass


def null_if_empty(s: str) -> str | None:
    return None if s == '' else s


GSHEETS_API_KEY = os.getenv('GSHEETS_API_KEY')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
WEBHOOK_URL = os.getenv('PLEIADES_WEBHOOK_URL')

load_dotenv()
PLEIADES_SHEET_ID = os.getenv('SHEET_ID')
REKSIO_GUILD_ID = int(os.getenv('GUILD_ID'))
PLEIADES_CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

LOG_PATH = os.getenv('LOG_PATH') or 'log.log'


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s\t%(message)s',
    datefmt='%y-%m-%d %H:%M:%S %z',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_PATH, 'a', 'utf-8'),
    ],
)

dc_client = discord.Client(intents=discord.Intents.default())

gs_client = gspread.api_key(GSHEETS_API_KEY)
sheet = gs_client.open_by_key(PLEIADES_SHEET_ID).sheet1


def match_category(sticker_id: str, categories: list[StickerCategory]) -> StickerCategory:
    for category in categories:
        if re.fullmatch(category.regex, sticker_id) is not None:
            return category


def fetch_assignment(stickers: list[Sticker]) -> list[Collector]:
    collectors = []
    headers, *rows = sheet.get(value_render_option=ValueRenderOption.unformatted)
    notes = sheet.get_notes()
    for (row_idx, row) in enumerate(rows, start=1):
        collector_id, name, discord_uid, forum_id, facebook_id, youtube_id, *sticker_ids = row
        collector = Collector(
            collector_id,
            name,
            try_int(discord_uid),
            try_int(forum_id),
            try_int(facebook_id),
            null_if_empty(youtube_id),
            []
        )
        for (col_idx, sticker_id) in enumerate(sticker_ids, start=6):
            sticker_id, *discriminator = sticker_id.strip().split(' ', maxsplit=1)
            discriminator = null_if_empty(''.join(discriminator).strip(' ()'))
            note = ''
            try:
                note = notes[row_idx][col_idx]
            except IndexError:
                pass
            note = note.splitlines()
            collector.album.append(GluedSticker(
                stickers[sticker_id],
                discriminator,
                null_if_empty(' '.join([line for line in note if line.startswith('#')]).strip()),
                null_if_empty(' '.join([line for line in note if not line.startswith('#')]).strip())
            ))
        collectors.append(collector)
    return collectors


async def update_albums(client: discord.Client, collectors: list[Collector]):
    try:
        logging.info(f'{client.user} has connected to Discord!')
        guild = client.get_guild(REKSIO_GUILD_ID)
        channel: discord.ForumChannel = guild.get_channel(PLEIADES_CHANNEL_ID)
        logging.info(f'Pleiades channel: #{channel.name}, type: {channel.type}')
        webhook = discord.Webhook.from_url(WEBHOOK_URL, client=client)
    finally:
        await client.close()


if __name__ == '__main__':
    with open(CATEGORIES_PATH, encoding='utf-8') as categories_file:
        sticker_categories = [
            StickerCategory.from_serialized(i, **category)
            for (i, category) in enumerate(pyjson5.load(categories_file))
        ]

    with open(STICKERS_PATH, encoding='utf-8') as stickers_file:
        stickers = {
            id: Sticker.from_serialized(sticker_categories, **sticker)
            for (id, sticker) in pyjson5.load(stickers_file).items()
        }

    collectors = fetch_assignment(stickers)
    print(collectors)

    @dc_client.event
    async def on_ready():
        await update_albums(dc_client, collectors)

    dc_client.run(DISCORD_BOT_TOKEN)
