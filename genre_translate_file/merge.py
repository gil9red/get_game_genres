#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import shutil
from pathlib import Path

from common import get_current_datetime_str, load_json, save_json, get_logger
from genre_translate_file.load import FILE_NAME_GENRE_TRANSLATE

# Инструкция:
# Из <genre_translate.json> скопировать в <merge_genre_translate.json> жанры, что еще не
# определены и в значение указать стандартизированное название жанра
# При выполнении скрипта значения из <merge_genre_translate.json> обновят <genre_translate.json>

DIR = Path(__file__).parent.resolve()
FILE_NAME_MERGE_GENRE_TRANSLATE = str(DIR / "data" / "merge_genre_translate.json")

FILE_NAME_BACKUP = DIR / "backup"
FILE_NAME_BACKUP.mkdir(parents=True, exist_ok=True)

log = get_logger("merge_genre_translate")

log.info("Запуск.")

backup_file_name = FILE_NAME_BACKUP / f"{get_current_datetime_str()}_{FILE_NAME_GENRE_TRANSLATE.name}"
log.info(f"Сохранение бекапа в: {backup_file_name}")
shutil.copy(
    FILE_NAME_GENRE_TRANSLATE,
    backup_file_name
)

log.info("Загрузка жанров")

genre_translate: dict = load_json(FILE_NAME_GENRE_TRANSLATE)
log.info(
    f"Жанров: {len(genre_translate)}. "
    f"Не заданных жанров: {sum(1 for v in genre_translate.values() if v is None)}"
)

if genre_translate:
    number = 0

    log.info("Загрузка файла слияния")

    merge_genre_translate: dict = load_json(FILE_NAME_MERGE_GENRE_TRANSLATE)
    log.info(f"Текущие жанры для слияния: {len(merge_genre_translate)}")

    for k, v in merge_genre_translate.items():
        if v is not None and k in genre_translate and genre_translate.get(k) is None:
            log.info(f"Слияние: {k!r} -> {v!r}")
            genre_translate[k] = v
            number += 1

    log.info(f"Всего добавлено жанров: {number}")

    log.info(f"Сохранение в {FILE_NAME_GENRE_TRANSLATE}")
    save_json(genre_translate, FILE_NAME_GENRE_TRANSLATE)

else:
    log.info("Жанров нет. Пропуск.")

log.info("Завершено!\n")
