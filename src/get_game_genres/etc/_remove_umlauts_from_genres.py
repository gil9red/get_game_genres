#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from get_game_genres.common import load_json, save_json, process_umlauts
from get_game_genres.db import Dump
from get_game_genres.export_import.export import run as run_export_games
from get_game_genres.genre_translate_file.load import FILE_NAME_GENRE_TRANSLATE
from get_game_genres.generate_games.generate_games import FILE_NAME_GAMES, run as run_generate_games
from get_game_genres.generate_genres.create import run as run_generate_genres


for dump in Dump.select():
    genres = [process_umlauts(genre) for genre in dump.genres]
    if genres != dump.genres:
        print(f"Обновлен {dump}")
        dump.genres = genres
        dump.save()

# Обновление списка игр из Dump
run_export_games()

# Чистим трансляции жанров
genre_translate: dict[str, list[str] | str | None] = load_json(
    FILE_NAME_GENRE_TRANSLATE
)
new_genre_translate = {
    process_umlauts(k): v
    for k, v in genre_translate.items()
}
if genre_translate != new_genre_translate:
    print(
        f"Обновление словаря трансляций, замена названий жанров "
        f'на: {", ".join(new_genre_translate.keys() - genre_translate.keys())}'
    )
    save_json(new_genre_translate, FILE_NAME_GENRE_TRANSLATE)

# Чистим жанры игр
FILE_NAME_GAMES.unlink(missing_ok=True)
run_generate_games()

run_generate_genres()
