#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import json

from get_game_genres.app_parser.main import get_parsers
from get_game_genres.generate_games.generate_games import (
    FILE_NAME_GENRE_TRANSLATE,
    process_genres,
    load_json,
)

GENRE_TRANSLATE: dict[str, str | list[str] | None] = load_json(
    FILE_NAME_GENRE_TRANSLATE
)

GAME: str = "Death Must Die"
MANUAL_GENRES: list[str] = [
    # NOTE: Для ручного добавления жанров
]

print(f"Game: {GAME!r}")
print()

total_genres: list[str]
if MANUAL_GENRES:
    total_genres = MANUAL_GENRES
else:
    total_genres = []
    for p in get_parsers():
        p._need_logs = False
        try:
            genres: list[str] = p.get_game_genres(GAME)
            print(f"[{p.get_site_name()}] Genres ({len(genres)}): {genres}")
            total_genres += genres
        except Exception as e:
            print(f"[{p.get_site_name()}] Error: {e}")

print()

print(f"Raw genres ({len(total_genres)}): {total_genres}")

# NOTE: Тут нет приседания с DLC и MOD из generate_games
total_genres = process_genres(total_genres, GENRE_TRANSLATE)

print(f"Genres ({len(total_genres)}): {total_genres}")
print(
    f"Genres as JSON ({len(total_genres)}): "
    f"{json.dumps(total_genres, ensure_ascii=False)}"
)
"""
Game: 'Death Must Die'
...
Raw genres (23): ['Инди', 'Казуальные', 'Ролевые', 'Экшены', 'Вид сверху', 'Инди', 'Экшен', 'Одиночная', 'Ролевая', 'Сверху/Изометрия', 'Фэнтези', 'Экшн', 'Action', 'Casual', 'Early Access', 'Indie', 'RPG', 'Изометрия', 'Процедурная генерация', 'Рогалик', 'Ролевая игра', 'Фэнтези', 'Экшен']
Genres (5): ['Action/RPG', 'Casual', 'Fantasy', 'Isometric', 'Roguelike']
Genres as JSON (5): ["Action/RPG", "Casual", "Fantasy", "Isometric", "Roguelike"]
"""
