#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from pathlib import Path


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.00"
)

DIR = Path(__file__).resolve().parent

DIR_BACKUP = DIR / "backup"
DIR_ERRORS = DIR / "errors"
DIR_LOGS = DIR / "logs"

DB_DIR_NAME = DIR / "database"
DB_DIR_NAME.mkdir(parents=True, exist_ok=True)

DB_FILE_NAME = str(DB_DIR_NAME / "games.sqlite")

NEED_LOGS = True
LOG_FORMAT = "[%(asctime)s] %(levelname)-8s %(message)s"

# TODO: Перенести в parsers/.deprecated
IGNORE_SITE_NAMES = [
    "metacritic_com",  # NOTE: Не работает то ли, из-за версии HTTP/2, то ли из-за российского IP
]

PORT = 5501
