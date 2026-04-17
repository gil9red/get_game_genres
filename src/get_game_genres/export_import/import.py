#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import peewee
from playhouse.shortcuts import dict_to_model

from get_game_genres.common import load_json
from get_game_genres.db import Dump
from get_game_genres.export_import.export import FILE_NAME_EXPORT_JSON


items: list[dict] = load_json(FILE_NAME_EXPORT_JSON)
print("Количество дампов в файле:", len(items))
print("Количество дампов в базе:", Dump.select().count())

for x in items:
    try:
        dump = dict_to_model(Dump, x)
        dump.save(force_insert=True)
        print(f"Импорт {x}")

    except peewee.IntegrityError as e:
        # Ignore error "UNIQUE constraint failed: dump.id"
        pass

print("Текущее количество дампов:", Dump.select().count())
