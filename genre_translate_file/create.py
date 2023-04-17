#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re

from common import load_json, save_json, get_logger
from db import Dump
from genre_translate_file.load import FILE_NAME_GENRE_TRANSLATE
from third_party.add_notify_telegram import add_notify


def get_similar_genre(genre: str, genre_translate: dict) -> list[str] | str | None:
    def _get_norm(text: str) -> str:
        return re.sub(r"\W", "", text).upper()

    genre = _get_norm(genre)
    genre_translate = {
        _get_norm(k): v
        for k, v in genre_translate.items()
    }
    return genre_translate.get(genre)


log = get_logger("genre_translate.txt")


def run(need_notify=True):
    log.info("Запуск трансляции жанров.")

    genre_translate: dict[str, list[str] | str | None] = load_json(
        FILE_NAME_GENRE_TRANSLATE
    )
    is_first_run = not genre_translate

    log.info(f"Жанров: {len(genre_translate)}")

    new_genres: dict[str, list[str] | str | None] = dict()
    for genre in Dump.get_all_genres():
        if genre not in genre_translate:
            log.info(f"Добавлен новый жанр: {genre!r}")

            # Попробуем найти жанр среди существующих
            value = get_similar_genre(genre, genre_translate)
            if value:
                log.info(f"Найдено значение из похожего жанра: {genre!r}={value!r}")

            genre_translate[genre] = value
            new_genres[genre] = value

    if new_genres:
        unknown_genres = []
        exists_genres = []
        for k, v in new_genres.items():
            if v:
                exists_genres.append(f"{k!r}={v!r}")
            else:
                unknown_genres.append(k)

        text = f"Добавлены жанры ({len(new_genres)}):"
        if unknown_genres:
            text += "\n" + ", ".join(unknown_genres)

        if exists_genres:
            text += "\n" + ", ".join(exists_genres)

        log.info(text)

        # Если это первый запуск, то сообщение не отправляем
        if not is_first_run and need_notify:
            add_notify(log.name, text)

        log.info("Сохранение жанров")
        save_json(genre_translate, FILE_NAME_GENRE_TRANSLATE)

    else:
        log.info("Нет новых жанров")

    log.info("Завершено!\n")


if __name__ == "__main__":
    run()
