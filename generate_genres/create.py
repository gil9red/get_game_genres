#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from collections import defaultdict
from pathlib import Path

from common import load_json, save_json, get_logger
from db import Genre
from genre_translate_file.load import FILE_NAME_GENRE_TRANSLATE


FILE_NAME_GENRES = Path(__file__).parent.resolve() / "genres.json"


log = get_logger("generate_genres")


def get_genres_with_aliases() -> dict[str, set[str]]:
    genre_translate: dict = load_json(FILE_NAME_GENRE_TRANSLATE)

    all_genres: dict[str, set[str]] = defaultdict(set)
    for alias, genre in genre_translate.items():
        if not genre:
            continue

        alias = alias.lower()

        if isinstance(genre, list):
            for name in genre:
                all_genres[name].add(alias)
        else:
            all_genres[genre].add(alias)

    all_genres = {
        genre: sorted(  # Оставляем только те псевдонимы, что не содержат название жанра
            x
            for x in aliases
            if genre.lower() not in x
        )
        for genre, aliases in all_genres.items()
    }
    return all_genres


def run():
    log.info("Запуск генератора жанров.")

    current_genres: dict = load_json(FILE_NAME_GENRES)
    log.info(f"Жанров: {len(current_genres)}")

    all_genres = get_genres_with_aliases()
    log.info(f"Жанров из файла трансляции: {len(all_genres)}")

    genres = dict()
    for genre in sorted(all_genres):
        if genre in current_genres:
            genres[genre] = current_genres.get(genre)
        else:
            log.info(f"Добавлен новый жанр: {genre!r}")
            genres[genre] = ""

    number = len(genres) - len(current_genres)
    if number:
        log.info(f"Добавлено жанров: {number}")

        log.info(f"Сохранение в {FILE_NAME_GENRES}")
        save_json(genres, FILE_NAME_GENRES)
    else:
        log.info("Новых жанров нет. Сохранять не нужно")

    for genre, description in genres.items():
        aliases: list[str] = sorted(all_genres.get(genre, []))

        Genre.add_or_update(
            name=genre,
            description=description,
            aliases=", ".join(aliases),
        )

    log.info("Завершено!\n")


if __name__ == "__main__":
    run()
