#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import json
import logging
import sys
import unicodedata

from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import DIR_LOGS
from third_party.parse_played_games import parse_played_games


def get_uniques(items: list) -> list:
    return list(set(items))


def get_current_datetime_str(fmt="%Y-%m-%d_%H%M%S") -> str:
    return datetime.now().strftime(fmt)


def load_json(file_name: str | Path) -> dict | list:
    try:
        return json.load(open(file_name, encoding="utf-8"))
    except:
        return dict()


def save_json(data: dict | list, file_name: str | Path):
    json.dump(
        data,
        open(file_name, "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=4
    )


def get_games_list() -> list[str]:
    rs = requests.get("https://gist.github.com/gil9red/2f80a34fb601cd685353")
    rs.raise_for_status()

    root = BeautifulSoup(rs.content, "html.parser")
    href = root.select_one(".file-actions > a")["href"]

    raw_url = urljoin(rs.url, href)

    rs = requests.get(raw_url)
    content_gist = rs.text

    platforms = parse_played_games(content_gist)

    all_games = []
    for categories in platforms.values():
        for games in categories.values():
            all_games += games

    return sorted(set(all_games))


def get_logger(name: str = "dump.txt", dir_logs: Path = DIR_LOGS, encoding="utf-8"):
    dir_logs.mkdir(parents=True, exist_ok=True)
    file = dir_logs / name

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s] %(levelname)-8s %(message)s")

    fh = RotatingFileHandler(
        file, maxBytes=10_000_000, backupCount=5, encoding=encoding
    )
    fh.setFormatter(formatter)
    log.addHandler(fh)

    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)

    return log


def process_umlauts(text: str) -> str:
    # Замена "и" с умлаутом на один символ "й"
    replace = {
        "й": "й",
        "Й": "Й",
    }
    for k, v in replace.items():
        text = text.replace(k, v)

    # Дополнительная чистка умлаутом
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    return text


if __name__ == "__main__":
    items = get_games_list()
    print(f'Games ({len(items)}): {", ".join(items[:5])}...')
    # Games (743): 35MM, 60 Seconds!, A Bird Story, A Plague Tale: Innocence, A Story About My Uncle...

    assert process_umlauts("Файтинг̆") == "Файтинг"
