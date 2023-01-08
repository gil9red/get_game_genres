#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import json

from db import Dump
from common_utils import get_logger
from genre_translate_file.load import FILE_NAME_GENRE_TRANSLATE
from common import load
from third_party.add_notify_telegram import add_notify


log = get_logger('genre_translate.txt')


def run(need_notify=True):
    log.info('Start load genres.')

    genre_translate = load(FILE_NAME_GENRE_TRANSLATE)
    is_first_run = not genre_translate

    log.info(f'Current genres: {len(genre_translate)}')

    new_genres = []
    for genre in Dump.get_all_genres():
        if genre not in genre_translate:
            log.info(f'Added new genre: {genre!r}')
            genre_translate[genre] = None
            new_genres.append(genre)

    if new_genres:
        text = f"Added genres ({len(new_genres)}): {', '.join(new_genres)}"
        log.info(text)

        # Если это первый запуск, то сообщение не отправляем
        if not is_first_run and need_notify:
            add_notify(log.name, text)

        log.info('Save genres')

        json.dump(
            genre_translate,
            open(FILE_NAME_GENRE_TRANSLATE, 'w', encoding='utf-8'),
            ensure_ascii=False,
            indent=4
        )

    else:
        log.info('No new genres')

    log.info('Finish!')


if __name__ == '__main__':
    run()
