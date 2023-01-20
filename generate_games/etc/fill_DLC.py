#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import re

from generate_games.generate_games import FILE_NAME_GAMES
from common import load_json, save_json


game_by_genres: dict = load_json(FILE_NAME_GAMES)
print(f'Данных из файла игр: {len(game_by_genres)}')

not_defined_dlc: list[str] = [
    name
    for name, genres in game_by_genres.items()
    if not genres and re.search(r'\(\w+\)', name)
]
print(f'Не имеют жанры: {len(not_defined_dlc)}')
print()

for name_dlc in not_defined_dlc:
    variants: list[str] = []
    for name in game_by_genres:
        if name_dlc == name:
            continue

        if re.sub(r'\W', '', name_dlc).upper().startswith(re.sub(r'\W', '', name).upper()):
            variants.append(name)

    if variants:
        name = max(variants, key=len)  # Выбираем игры с наибольшим количеством символов
        print(f'{name}\n{name_dlc}\n')

        game_by_genres[name_dlc] = game_by_genres[name]

print(f'Сохранение в {FILE_NAME_GAMES}')
save_json(game_by_genres, FILE_NAME_GAMES)
