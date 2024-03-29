#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import json
from pathlib import Path

from common import load_json


FILE_NAME_GENRE_TRANSLATE = Path(__file__).parent.resolve() / "data" / "genre_translate.json"


if __name__ == "__main__":
    genre_translate: dict = load_json(FILE_NAME_GENRE_TRANSLATE)
    print(f"Genre_translate ({len(genre_translate)}): {genre_translate}")
    print()

    # Print all undefined genres without '{' / '}' and indent
    # Сохранение синтаксиса для последующей удобной вставки кусков в merge_genre_translate.json
    genre_null_translate = {
        k: v
        for k, v in genre_translate.items()
        if v is None
    }
    print(f"Genre null translate ({len(genre_null_translate)}):")
    json_text = json.dumps(genre_null_translate, ensure_ascii=False, indent=4)
    lines = json_text.splitlines()[1:-1]
    for i, line in enumerate(lines):
        print(line.strip())
        if i > 0 and i % 40 == 0:
            print()
