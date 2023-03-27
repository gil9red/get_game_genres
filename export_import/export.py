#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from pathlib import Path

from playhouse.shortcuts import model_to_dict

from common import save_json
from db import Dump


DIR = Path(__file__).parent.resolve() / 'data'
DIR.mkdir(parents=True, exist_ok=True)

FILE_NAME_EXPORT_JSON = DIR / 'games.json'


def run():
    items = [model_to_dict(dump) for dump in Dump.select()]
    print(len(items))

    save_json(items, FILE_NAME_EXPORT_JSON)


if __name__ == '__main__':
    run()
