#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import importlib.util
import sys
import time

from inspect import isclass
from pathlib import Path

from config import IGNORE_SITE_NAMES
from parsers.base_parser import BaseParser


# Текущая папка
DIR_PARSERS = Path(__file__).parent.resolve()


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


def print_parsers(parsers: list, log=print):
    max_width = len(max([x.get_site_name() for x in parsers], key=len))
    fmt_str = '    {:<%d} : {}' % max_width
    items = [
        fmt_str.format(parser.get_site_name(), parser.__class__)
        for parser in parsers
    ]

    log(f'Parsers ({len(parsers)}):\n' + "\n".join(items))


TEST_GAMES = [
    'Hellgate: London',
    'The Incredible Adventures of Van Helsing',
    'Dark Souls: Prepare to Die Edition',
    'Twin Sector',
    'Call of Cthulhu: Dark Corners of the Earth',
]


def _common_test(get_game_genres, sleep=1, max_number=None):
    if max_number is None:
        max_number = len(TEST_GAMES)

    for name in TEST_GAMES[:max_number]:
        print(f'Search {name!r}...')
        print(f'    Genres: {get_game_genres(name)}\n')

        time.sleep(sleep)


if __name__ == '__main__':
    parsers = get_parsers()
    print_parsers(parsers)
    """
    Parsers (13):
        ag_ru                  : <class 'ag_ru.AgRuParser'>
        gamebomb_ru            : <class 'gamebomb_ru.GamebombRuParser'>
        gameguru_ru            : <class 'gameguru_ru.GameguruRuParser'>
        gamespot_com           : <class 'gamespot_com.GamespotComParser'>
        igromania_ru           : <class 'igromania_ru.IgromaniaRuParser'>
        iwgs_games             : <class 'iwgs_games.IwgsGamesParser'>
        mobygames_com          : <class 'mobygames_com.MobygamesComParser'>
        playground_ru          : <class 'playground_ru.PlaygroundRuParser'>
        spong_com              : <class 'spong_com.SpongComParser'>
        squarefaction_ru       : <class 'squarefaction_ru.SquarefactionRuParser'>
        stopgame_ru            : <class 'stopgame_ru.StopgameRuParser'>
        store_steampowered_com : <class 'store_steampowered_com.StoreSteampoweredComParser'>
        vgtimes_ru             : <class 'vgtimes_ru.VGTimesRuParser'>
    """
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
        vgtimes_ru               : ['Вид от третьего лица', 'Футуризм (Будущее)', 'Хоррор на выживание', 'Шутер', 'Экшен']
    """
