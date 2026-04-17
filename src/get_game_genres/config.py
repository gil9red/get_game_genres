#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from pathlib import Path

USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.00"
)

DIR: Path = Path(__file__).resolve().parent

DIR_BACKUP: Path = DIR / "backup"
DIR_ERRORS: Path = DIR / "errors"
DIR_LOGS: Path = DIR / "logs"

DB_DIR_NAME: Path = DIR / "database"
DB_DIR_NAME.mkdir(parents=True, exist_ok=True)

DB_FILE_NAME: str = str(DB_DIR_NAME / "games.sqlite")

NEED_LOGS: bool = True
LOG_FORMAT: str = "[%(asctime)s] %(levelname)-8s %(message)s"

PORT: int = 5501
