import logging
import os
import re

import discord
from dotenv import load_dotenv
import gspread
from gspread.utils import ValueRenderOption
import pyjson5

from models import StickerCategory, Sticker, GluedSticker, Collector, ConcreteSnowflake
from paths import STICKERS_PATH, CATEGORIES_PATH


def try_int(s: str) -> int | None:
    try:
        return int(s)
    except:
        pass


def null_if_empty(s: str) -> str | None:
    return None if s == "" else s


GSHEETS_API_KEY = os.getenv("GSHEETS_API_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WEBHOOK_URL = os.getenv("PLEIADES_WEBHOOK_URL")

load_dotenv()
PLEIADES_SHEET_ID = os.getenv("SHEET_ID")
REKSIO_GUILD_ID = int(os.getenv("GUILD_ID"))
PLEIADES_CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

LOG_PATH = os.getenv("LOG_PATH") or "log.log"
DEBUG_USER_LIMIT = try_int(os.getenv("DEBUG_USER_LIMIT"))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s\t%(message)s",
    datefmt="%y-%m-%d %H:%M:%S %z",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_PATH, "a", "utf-8"),
    ],
)

dc_client = discord.Client(intents=discord.Intents.default())

gs_client = gspread.api_key(GSHEETS_API_KEY)
sheet = gs_client.open_by_key(PLEIADES_SHEET_ID).sheet1


def match_category(
    sticker_id: str, categories: list[StickerCategory]
) -> StickerCategory:
    for category in categories:
        if re.fullmatch(category.regex, sticker_id) is not None:
            return category


def fetch_assignment(stickers: list[Sticker]) -> list[Collector]:
    collectors = {}
    headers, *rows = sheet.get(value_render_option=ValueRenderOption.unformatted)
    notes = sheet.get_notes()
    for row_idx, row in enumerate(rows, start=1):
        (
            collector_id,
            name,
            discord_uid,
            forum_id,
            facebook_id,
            youtube_id,
            *sticker_ids,
        ) = row
        collector = Collector(
            collector_id,
            name,
            try_int(discord_uid),
            try_int(forum_id),
            try_int(facebook_id),
            null_if_empty(youtube_id),
            [],
        )
        for col_idx, sticker_id in enumerate(sticker_ids, start=6):
            sticker_id, *discriminator = sticker_id.strip().split(" ", maxsplit=1)
            discriminator = null_if_empty("".join(discriminator).strip(" ()"))
            note = ""
            try:
                note = notes[row_idx][col_idx]
            except IndexError:
                pass
            note = note.splitlines()
            collector.album.append(
                GluedSticker(
                    stickers[sticker_id],
                    discriminator,
                    null_if_empty(
                        " ".join(
                            [line for line in note if line.startswith("#")]
                        ).strip()
                    ),
                    null_if_empty(
                        " ".join(
                            [line for line in note if not line.startswith("#")]
                        ).strip()
                    ),
                )
            )
        collectors[collector.id] = collector
    return collectors


def extract_collector_id_from_message(message: discord.Message) -> str | None:
    lines = message.content.splitlines()
    if len(lines) < 1:
        return
    last_line = lines[len(lines) - 1]
    if last_line.startswith("-# ✨ "):
        return last_line.split(" ", maxsplit=2)[2]


async def process_thread(
    webhook: discord.Webhook, thread: discord.Thread
) -> list[discord.Message] | None:
    starter_message = await thread.fetch_message(thread.id)
    if starter_message is None:
        return
    if starter_message.author != webhook.user:
        return
    return list(await thread.history())


async def prepare_starter_message_content(client: discord.Client, collector: Collector) -> str:
    ret = f"Pseudonim: {collector.nickname}"
    if ping := collector.discord_ping:
        ret += f" ({ping})"
    if link := collector.forum_link:
        ret += f'\nProfil Forum "Przygody Reksia": {link}'
    if link := collector.youtube_link:
        ret += f"\nKanał YouTube: {link}"
    if link := collector.facebook_link:
        ret += f"\nProfil Facebook: {link}"
    ret += "\n\nLorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam tincidunt malesuada dui ut hendrerit. Pellentesque ex diam, fermentum id vulputate vel, fringilla in augue. Integer eget auctor est. Sed quis ultricies est, rhoncus vulputate nisl. Aliquam sollicitudin pretium nunc, eu pellentesque dolor viverra at. Pellentesque malesuada sapien eget mattis tristique. Morbi in mauris pretium, dignissim massa a, facilisis massa. In enim lacus, consequat a metus id, aliquet viverra dui. Aenean eu odio a lectus condimentum commodo. Curabitur rutrum luctus nisi, nec posuere lorem dapibus nec.\n"
    if collector.discord_uid:
        user = await client.fetch_user(collector.discord_uid)
        ret += "\n" + user.display_avatar.url
    ret += f"\n-# ✨ {collector.id}"
    return ret


def prepare_sticker_footer(glued_sticker: GluedSticker) -> str:
    ret = f"🖼️ {glued_sticker.sticker.id}"
    if glued_sticker.discriminator:
        ret += f" ({glued_sticker.discriminator})"
    return ret


async def update_albums(client: discord.Client, collectors: dict[str, Collector]):
    global DEBUG_USER_LIMIT
    try:
        logging.info(f"{client.user} has connected to Discord!")
        guild = client.get_guild(REKSIO_GUILD_ID)
        channel: discord.ForumChannel = guild.get_channel(PLEIADES_CHANNEL_ID)
        logging.info(f"Pleiades channel: #{channel.name}, type: {channel.type}")
        webhook = discord.Webhook.from_url(WEBHOOK_URL, client=client)
        to_delete = set()
        to_add = set(collectors.keys())
        thread_mapping = {}
        threads = {}
        # Fetch all threads created by the webhook
        for thread in channel.threads:
            if history := process_thread(webhook, thread) is not None:
                threads[thread.id] = history
        async for thread in channel.archived_threads():
            if history := process_thread(webhook, thread) is not None:
                threads[thread.id] = history
        # Check if there are any threads missing or no longer valid
        for thread_id, history in threads.items():
            if (
                collector_id := extract_collector_id_from_message(history[0])
                is not None
            ):
                thread_mapping[collector_id] = thread_id
                if collector_id in to_add:
                    to_add.remove(collector_id)
                else:
                    to_delete.append(collector_id)
        # Create missing threads
        for collector_id in to_add:
            collector = collectors[collector_id]
            sent_starter = await webhook.send(
                await prepare_starter_message_content(client, collector),
                thread_name=collector.nickname,
                allowed_mentions=discord.AllowedMentions.none(),
                silent=True,
                wait=True,
            )
            history = [sent_starter]
            thread_mapping[collector_id] = history
            for glued_sticker in collector.album:
                sticker_embed = (
                    discord.Embed(
                        title=glued_sticker.name, description=glued_sticker.description
                    )
                    .set_thumbnail(url=glued_sticker.sticker.url)
                    .set_footer(text=prepare_sticker_footer(glued_sticker))
                )
                history.append(
                    await webhook.send(
                        embed=sticker_embed,
                        thread=ConcreteSnowflake(sent_starter.id),
                        silent=True,
                        wait=True,
                    )
                )
#           thread: discord.Thread = guild.fetch_channel(thread_id)
#           thread.edit(locked=True, archived=True)
            if DEBUG_USER_LIMIT is not None:
                DEBUG_USER_LIMIT -= 1
                if DEBUG_USER_LIMIT <= 0:
                    break
    finally:
        await client.close()


if __name__ == "__main__":
    with open(CATEGORIES_PATH, encoding="utf-8") as categories_file:
        sticker_categories = [
            StickerCategory.from_serialized(i, **category)
            for (i, category) in enumerate(pyjson5.load(categories_file))
        ]

    with open(STICKERS_PATH, encoding="utf-8") as stickers_file:
        stickers = {
            id: Sticker.from_serialized(id, sticker_categories, **sticker)
            for (id, sticker) in pyjson5.load(stickers_file).items()
        }

    collectors = fetch_assignment(stickers)
    print(collectors)

    @dc_client.event
    async def on_ready():
        await update_albums(dc_client, collectors)

    dc_client.run(DISCORD_BOT_TOKEN)
