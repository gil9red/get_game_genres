#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import logging
import importlib.util
import sys

from logging.handlers import RotatingFileHandler
from inspect import isclass
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from parsers.base_parser import BaseParser

from common import DIR_LOGS, IGNORE_SITE_NAMES
from third_party.parse_played_games import parse_played_games


DIR = Path(__file__).parent.resolve()
DIR_PARSERS = DIR / 'parsers'


def module_from_file(file_path: Path) -> 'ModuleType':
    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if module_name not in sys.modules:
        sys.modules[module_name] = module

    return module


def get_parsers() -> list[BaseParser]:
    items = []

    for file_name in DIR_PARSERS.glob('*.py'):
        module = module_from_file(file_name)
        for attr in dir(module):
            cls = getattr(module, attr)
            if not isclass(cls) or not issubclass(cls, BaseParser) or cls is BaseParser:
                continue

            parser: BaseParser = cls.instance()
            if parser.get_site_name() not in IGNORE_SITE_NAMES:
                items.append(parser)

    return items


def get_games_list() -> list[str]:
    rs = requests.get('https://gist.github.com/gil9red/2f80a34fb601cd685353')
    rs.raise_for_status()

    root = BeautifulSoup(rs.content, 'html.parser')
    href = root.select_one('.file-actions > a')['href']

    raw_url = urljoin(rs.url, href)

    rs = requests.get(raw_url)
    content_gist = rs.text

    platforms = parse_played_games(content_gist)

    games = []
    for categories in platforms.values():
        games += categories['FINISHED_GAME'] + categories['FINISHED_WATCHED']

    return sorted(set(games))


def get_logger(name='dump.txt', encoding='utf-8'):
    Path(DIR_LOGS).mkdir(parents=True, exist_ok=True)

    file = DIR_LOGS + '/' + name

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] %(levelname)-8s %(message)s')

    fh = RotatingFileHandler(file, maxBytes=10_000_000, backupCount=5, encoding=encoding)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setFormatter(formatter)
    log.addHandler(sh)

    return log


def print_parsers(parsers: list, log=print):
    max_width = len(max([x.get_site_name() for x in parsers], key=len))
    fmt_str = '    {:<%d} : {}' % max_width
    items = [
        fmt_str.format(parser.get_site_name(), parser.__class__)
        for parser in parsers
    ]

    log(f'Parsers ({len(parsers)}):\n' + "\n".join(items))


if __name__ == "__main__":
    items = get_games_list()
    print(f'Games ({len(items)}): {", ".join(items[:5])}...')
    # Games (743): 35MM, 60 Seconds!, A Bird Story, A Plague Tale: Innocence, A Story About My Uncle...

    print()

    parsers = get_parsers()
    print_parsers(parsers)
    # Parsers (14):
    #     ag_ru                  : <class 'ag_ru.AgRu_Parser'>
    #     gamebomb_ru            : <class 'gamebomb_ru.GamebombRu_Parser'>
    #     gamefaqs_gamespot_com  : <class 'gamefaqs_gamespot_com.GamefaqsGamespotCom_Parser'>
    #     gameguru_ru            : <class 'gameguru_ru.GameguruRu_Parser'>
    #     gamer_info_com         : <class 'gamer_info_com.GamerInfoCom_Parser'>
    #     gamespot_com           : <class 'gamespot_com.GamespotCom_Parser'>
    #     igromania_ru           : <class 'igromania_ru.IgromaniaRu_Parser'>
    #     iwantgames_ru          : <class 'iwantgames_ru.IwantgamesRu_Parser'>
    #     metacritic_com         : <class 'metacritic_com.MetacriticCom_Parser'>
    #     mobygames_com          : <class 'mobygames_com.MobygamesCom_Parser'>
    #     playground_ru          : <class 'playground_ru.PlaygroundRu_Parser'>
    #     spong_com              : <class 'spong_com.SpongCom_Parser'>
    #     stopgame_ru            : <class 'stopgame_ru.StopgameRu_Parser'>
    #     store_steampowered_com : <class 'store_steampowered_com.StoreSteampoweredCom_Parser'>

    print()

    game = 'Dead Space'
    print(f'Search genres for {game!r}:')

    for parser in parsers:
        parser._need_logs = False

        try:
            result = parser.get_game_genres(game)
        except Exception as e:
            result = e

        print(f"    {parser.get_site_name():<25}: {result}")
    """
        ag_ru                    : ['Шутеры', 'Экшены']
        gamebomb_ru              : ['Боевик-приключения', 'Шутер']
        gameguru_ru              : ['Хоррор', 'Шутер', 'Экшен']
        gamespot_com             : ['3D', 'Action', 'Adventure', 'Survival']
        igromania_ru             : ['FPS', 'Хоррор', 'Экшен']
        iwgs_games               : []
        mobygames_com            : ['Action']
        playground_ru            : ['Космос', 'Научная фантастика', 'От третьего лица', 'Ужасы', 'Экшен']
        spong_com                : ['Adventure: Survival Horror']
        squarefaction_ru         : ['Action', 'Survival Horror', 'TPS']
        stopgame_ru              : ['action']
        store_steampowered_com   : []
    """
