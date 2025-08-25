'''
- czy nazwy są zgodne z [a-z0-9_]+
- czy nazwy się nie duplikują
- czy supersedes się poprawnie mapuje
- czy path jest poprawne
- czy są jakieś zbędne klucze poza path, author, name, description, supersedes i unlisted?
- czy są jakieś pliki graficzek nieużyte
'''

import pyjson5
import re

from models import StickerCategory, Sticker, GluedSticker, Collector
from paths import STICKERS_PATH, CATEGORIES_PATH

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
