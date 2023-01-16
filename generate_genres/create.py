#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from pathlib import Path

from common import load_json, save_json, get_logger
from db import Genre
from genre_translate_file.load import FILE_NAME_GENRE_TRANSLATE


FILE_NAME_GENRES = Path(__file__).parent.resolve() / 'genres.json'


log = get_logger('generate_genres.txt')


def run():
    log.info("Старт")

    current_genres: dict = load_json(FILE_NAME_GENRES)
    log.info(f'Жанров: {len(current_genres)}')

    genre_translate: dict = load_json(FILE_NAME_GENRE_TRANSLATE)

    all_genres = set()
    for genres in genre_translate.values():
        if not genres:
            continue

        if isinstance(genres, list):
            all_genres.update(genres)
        else:
            all_genres.add(genres)

    all_genres = sorted(all_genres)
    log.info(f'Жанров из файла трансляции: {len(all_genres)}')

    new_genres = dict()
    for genre in all_genres:
        genre_info = current_genres.get(genre)
        if genre_info:
            new_genres[genre] = genre_info
        else:
            log.info(f'Добавлен новый жанр: {genre!r}')
            new_genres[genre] = dict(
                title='',
                description='',
            )

    number = len(new_genres) - len(current_genres)
    if number:
        log.info(f'Добавлено жанров: {number}')

        log.info(f'Сохранение в {FILE_NAME_GENRES}')
        save_json(new_genres, FILE_NAME_GENRES)
    else:
        log.info('Новых жанров нет. Сохранять не нужно')

    for genre, info in new_genres.items():
        Genre.add_or_update(
            name=genre,
            title=info['title'],
            description=info['description']
        )

    log.info("Финиш\n")


if __name__ == '__main__':
    run()
