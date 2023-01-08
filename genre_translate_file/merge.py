#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import shutil
from pathlib import Path

from genre_translate_file.load import FILE_NAME_GENRE_TRANSLATE
from common import get_current_datetime_str, load_json, save_json
from common_utils import get_logger

# Инструкция:
# Из <genre_translate.json> скопировать в <merge_genre_translate.json> жанры, что еще не
# определены и в значение указать стандартизированное название жанра
# При выполнении скрипта значения из <merge_genre_translate.json> обновят <genre_translate.json>

DIR = Path(__file__).parent.resolve()
FILE_NAME_MERGE_GENRE_TRANSLATE = str(DIR / 'data' / 'merge_genre_translate.json')

FILE_NAME_BACKUP = DIR / 'backup'
FILE_NAME_BACKUP.mkdir(parents=True, exist_ok=True)

log = get_logger('merge_genre_translate.txt')

log.info('Start.')

backup_file_name = (
    FILE_NAME_BACKUP / f'{get_current_datetime_str()}_{Path(FILE_NAME_GENRE_TRANSLATE).name}'
)
log.info(f'Save backup to: {backup_file_name}')
shutil.copy(
    FILE_NAME_GENRE_TRANSLATE,
    backup_file_name
)

log.info('Load genres')

genre_translate = load_json(FILE_NAME_GENRE_TRANSLATE)
log.info(
    f'Current genres: {len(genre_translate)}. '
    f'Null genres: {sum(1 for v in genre_translate.values() if v is None)}'
)

if genre_translate:
    number = 0

    log.info('Load merge')

    merge_genre_translate = load_json(FILE_NAME_MERGE_GENRE_TRANSLATE)
    log.info(f'Current merged genres: {len(merge_genre_translate)}')

    for k, v in merge_genre_translate.items():
        if v is not None and k in genre_translate and genre_translate.get(k) is None:
            log.info(f'Merge: {k!r} -> {v!r}')
            genre_translate[k] = v
            number += 1

    log.info(f'New merged: {number}')
    log.info('Save merged genres')

    save_json(genre_translate, FILE_NAME_GENRE_TRANSLATE)

else:
    log.info('Empty genres. Skip.')

log.info('Finish!')
