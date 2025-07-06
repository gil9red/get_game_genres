#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from parsers.base_parser import BaseParser


class IgromaniaRuParser(BaseParser):
    def _parse(self) -> list[str]:
        url = f"https://www.igromania.ru/api/v2/search/games/?q={self.game_name}"

        data: dict = self.send_get(url, return_json=True)

        # Example result:
        # {'count': 1, 'next': None, 'previous': None, 'results': [
        #   {'id': 3238, 'like_count': 168,
        #   'slug': 'Call_of_Cthulhu_Dark_Corners_of_the_Earth.html',
        #   'name': 'Call of Cthulhu: Dark Corners of the Earth',
        #   'image': {'thumb': 'https://newcdn.igromania.ru//c/81c5d198953204fa849dbfad6414f85e/400x510/newcdn
        #       .igromania.ru/mnt/games/5/2/8/a/e/c/3238/e2a6833f2c7d1e60_original.jpg', 'origin':
        #       'https://newcdn.igromania.ru/mnt/games/5/2/8/a/e/c/3238/e2a6833f2c7d1e60_original.jpg'},
        #   'release_date': {'string': '27 марта 2006', 'date': '2006-03-27',
        #       'is_precise': True, 'precision_class': 'day'},
        #   'rating': None, 'mark': 0.0,
        #   'genres': [
        #       {'id': 41, 'name': 'Хоррор (ужасы)', 'slug': 'khorror-uzhasy', 'position': 0},
        #       {'id': 7, 'name': 'Экшен', 'slug': 'ekshen', 'position': 0},
        #       {'id': 3, 'name': 'Приключение', 'slug': 'prikliuchenie', 'position': 28}
        #   ],
        #   'platforms': [
        #       {'id': 58, 'name': 'PC', 'slug': 'pc', 'position': 1},
        #       {'id': 96, 'name': 'Xbox', 'slug': 'xbox', 'position': 46}],
        #   'favorite': False}
        # ]}

        for game in data["results"]:
            title = game["name"]
            if not self.is_found_game(title):
                continue

            # Сойдет первый, совпадающий по имени, вариант
            return [genre["name"] for genre in game["genres"]]

        self.log_info(f"Not found game {self.game_name!r}")
        return []


def get_game_genres(game_name: str, *args, **kwargs) -> list[str]:
    return IgromaniaRuParser(*args, **kwargs).get_game_genres(game_name)


if __name__ == "__main__":
    from parsers import _common_test

    _common_test(get_game_genres)

    # Search 'Hellgate: London'...
    #     Genres: ['Ролевая игра', 'Экшен']
    #
    # Search 'The Incredible Adventures of Van Helsing'...
    #     Genres: ['Ролевая игра', 'Экшен']
    #
    # Search 'Dark Souls: Prepare to Die Edition'...
    #     Genres: ['Ролевая игра', 'Экшен']
    #
    # Search 'Twin Sector'...
    #     Genres: ['Приключение', 'Экшен']
    #
    # Search 'Call of Cthulhu: Dark Corners of the Earth'...
    #     Genres: ['Приключение', 'Хоррор (ужасы)', 'Экшен']
