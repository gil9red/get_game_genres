#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import shutil
import re

from pathlib import Path

from common import get_current_datetime_str, load_json, save_json, get_logger
from db import Dump
from genre_translate_file.load import FILE_NAME_GENRE_TRANSLATE


log = get_logger('generate_games.txt')


DIR = Path(__file__).parent.resolve()

FILE_NAME_GAMES = DIR / 'game_by_genres.json'

FILE_NAME_BACKUP = DIR / 'backup'
FILE_NAME_BACKUP.mkdir(parents=True, exist_ok=True)

# Example: "Action", "Adventure" -> "Action-adventure"
GENRE_COMPRESSION = [
    ("Action", "Adventure", "Action-adventure"),
    ("Action", "RPG", "Action/RPG"),
    ("First-person", "Shooter", "FPS"),
    ("First-person", "FPS", "FPS"),
    ("Shooter", "FPS", "FPS"),
    ("Third-person", "Shooter", "TPS"),
    ("Third-person", "TPS", "TPS"),
    ("Shooter", "TPS", "TPS"),
    ("Survival", "Horror", "Survival horror"),
]


def do_genres_compression(genres: list[str], need_log: bool = True) -> list[str]:
    genres = sorted(set(genres))
    to_remove = set()

    for src_1, src_2, target in GENRE_COMPRESSION:
        if src_1 in genres and src_2 in genres:
            to_remove.add(src_1)
            to_remove.add(src_2)
            genres.append(target)

            if need_log:
                log.info(f'Compress genres {src_1!r} and {src_2!r} -> {target!r}')

    for x in to_remove:
        genres.remove(x)

    return sorted(set(genres))


def remove_partial_duplicates(genres: list[str], need_log: bool = True) -> list[str]:
    genres = genres.copy()

    # Example: ['Action-adventure', 'Action/RPG', 'Adventure', 'RPG'] ->
    #          -> {('action', 'adventure'): 'Action-adventure', ('action', 'rpg'): 'Action/RPG'}
    words_by_complex_genre: dict[tuple[str], str] = dict()
    for genre in genres:
        words: list[str] = [word.lower() for word in map(str.strip, re.split(r'\W', genre)) if word]
        if len(words) > 1:
            words_by_complex_genre[tuple(words)] = genre

    # Example: ['Action-adventure', 'Action/RPG', 'Adventure', 'RPG'] ->
    #          -> ['Action-adventure', 'Action/RPG']
    to_remove = []
    for words, complex_genre in words_by_complex_genre.items():
        for genre in genres:
            if genre.lower() in words:
                if need_log:
                    log.info(f"Remove partial duplicate {genre!r} of {complex_genre!r}")
                to_remove.append(genre)

    for genre in to_remove:
        genres.remove(genre)

    return genres


def run():
    log.info('Start.')

    if FILE_NAME_GAMES.exists():
        backup_file_name = str(
            FILE_NAME_BACKUP / f'{get_current_datetime_str()}_{FILE_NAME_GAMES.name}'
        )
        shutil.copy(
            FILE_NAME_GAMES,
            backup_file_name
        )
        log.info(f'Save backup to: {backup_file_name}')
        log.info('')

    log.info('Loading cache...')

    game_by_genres: dict = load_json(FILE_NAME_GAMES)
    log.info(f'game_by_genres ({len(game_by_genres)})')

    new_game_by_genres = Dump.dump()
    log.info(f'new_game_by_genres ({len(new_game_by_genres)})')

    genre_translate: dict = load_json(FILE_NAME_GENRE_TRANSLATE)
    log.info(f'genre_translate ({len(genre_translate)})')

    log.info('Finish loading cache.')
    log.info('')

    log.info('Search games...')

    number = 0

    for game, genres in new_game_by_genres.items():
        if game in game_by_genres:
            continue

        log.info(f'Added game {game!r} with genres ({len(genres)}): {genres}')
        number += 1

        new_genres = []

        for x in genres:
            tr_genres = genre_translate.get(x)
            if not tr_genres:  # null, [], ""
                continue

            if isinstance(tr_genres, str):
                new_genres.append(tr_genres)

            elif isinstance(tr_genres, list):
                new_genres.extend(tr_genres)

            else:
                log.warning(f'Unsupported type genres {tr_genres} from {x!r}')

        new_genres = do_genres_compression(new_genres)
        new_genres = remove_partial_duplicates(new_genres)

        log.info(f'Successful translate genres ({len(new_genres)}): {new_genres}')
        game_by_genres[game] = new_genres

        log.info('')

    log.info(f'Finish search games. New games: {number}.')

    log.info(f'Saving to {FILE_NAME_GAMES}')

    save_json(game_by_genres, FILE_NAME_GAMES)

    log.info('Finish!')


if __name__ == '__main__':
    run()
