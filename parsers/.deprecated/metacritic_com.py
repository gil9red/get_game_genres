#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
from parsers.base_parser import BaseParser


PATTERN_GAME = re.compile(',type:"game-title",.+?,title:"(?P<title>.+?)",.+?,genres:\[(?P<genres>.+?)],')
PATTERN_GAME_GENRES = re.compile('name:"(?P<title>.+?)"')


class MetacriticComParser(BaseParser):
    def _parse(self) -> list[str]:
        url = f"https://www.metacritic.com/search/{self.game_name}/"
        rs = self.send_get(url)

        for m in PATTERN_GAME.finditer(rs.text):
            title: str = m.group("title")
            if not self.is_found_game(title):
                continue

            genres_value: str = m.group("genres")
            genres: list[str] = PATTERN_GAME_GENRES.findall(genres_value)

            # Сойдет первый, совпадающий по имени, вариант
            return genres

        self.log_info(f"Not found game {self.game_name!r}")
        return []


def get_game_genres(game_name: str, *args, **kwargs) -> list[str]:
    return MetacriticComParser(*args, **kwargs).get_game_genres(game_name)


if __name__ == "__main__":
    from parsers import _common_test

    _common_test(get_game_genres)

    # Search 'Hellgate: London'...
    #     Genres: ['Western RPG']
    #
    # Search 'The Incredible Adventures of Van Helsing'...
    #     Genres: ['Action RPG']
    #
    # Search 'Dark Souls: Prepare to Die Edition'...
    #     Genres: ['Action RPG']
    #
    # Search 'Twin Sector'...
    #     Genres: ['Linear Action Adventure']
    #
    # Search 'Call of Cthulhu: Dark Corners of the Earth'...
    #     Genres: ['Survival']
