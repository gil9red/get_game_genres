#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
from urllib.parse import urljoin

from parsers.base_parser import BaseParser


class StopgameRuParser(BaseParser):
    def _parse(self) -> list[str]:
        url = f"https://stopgame.ru/ajax/search/games/?term={self.game_name}&offset=0&sort=relevance"
        data: dict = self.send_get(url, return_json=True)

        for game in filter(lambda obj: obj["type"] == "game", data["results"]):
            if not self.is_found_game(game["title"]):
                continue

            url_game = urljoin(url, game["url"])

            self.log_debug(f"Загрузка {url_game!r}")
            soup = self.send_get(url_game, return_html=True)

            # Сойдет первый, совпадающий по имени, вариант
            return [
                self.get_norm_text(a)
                for a in soup.select('a[class *= "_tag_"]')
            ]

        self.log_info(f"Not found game {self.game_name!r}")
        return []


def get_game_genres(game_name: str, *args, **kwargs) -> list[str]:
    return StopgameRuParser(*args, **kwargs).get_game_genres(game_name)


if __name__ == "__main__":
    from parsers import _common_test

    _common_test(get_game_genres)

    # Search 'Hellgate: London'...
    #     Genres: ['Мультиплеер', 'Научная фантастика', 'Одиночная', 'От первого лица', 'От третьего лица', 'Ролевая', 'Хоррор', 'Шутер', 'Экшн']
    #
    # Search 'The Incredible Adventures of Van Helsing'...
    #     Genres: ["Hack & Slash/Beat 'em up", 'Кооперативная', 'Мультиплеер', 'Одиночная', 'Ролевая', 'Сверху/Изометрия', 'Фэнтези', 'Экшн']
    #
    # Search 'Dark Souls: Prepare to Die Edition'...
    #     Genres: []
    #
    # Search 'Twin Sector'...
    #     Genres: ['Головоломка', 'Научная фантастика', 'Одиночная', 'От первого лица', 'Приключение', 'Шутер', 'Экшн']
    #
    # Search 'Call of Cthulhu: Dark Corners of the Earth'...
    #     Genres: ['Выживание', 'Детектив/Тайна', 'Одиночная', 'От первого лица', 'Приключение', 'Стелс', 'Хоррор', 'Шутер', 'Экшн']
