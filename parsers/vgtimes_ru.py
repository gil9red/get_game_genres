#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from parsers.base_parser import BaseParser


class VGTimesRuParser(BaseParser):
    base_url = 'https://vgtimes.ru/'
    was_first_request = False

    def _parse(self) -> list[str]:
        # На первый запрос заходим на основную страницу
        if not self.was_first_request:
            self.send_get(self.base_url)
            self.was_first_request = True

        url_search = f'{self.base_url}engine/ajax/search.php'
        data = {
            'action': 'search2',
            'query': self.game_name,
            'ismobile': '',
            'what': 1,
        }

        rs_json = self.send_post(url_search, data=data, return_json=True)
        rs_html = rs_json['games_result']

        root = self.parse_html(rs_html)
        for game_el in root.select('.game_search'):
            title = game_el.select_one('.title').text.strip()
            if not self.is_found_game(title):
                continue

            return game_el.select_one('.genre').text.strip().split(', ')

        self.log_info(f'Not found game {self.game_name!r}')
        return []


def get_game_genres(game_name: str, *args, **kwargs) -> list[str]:
    return VGTimesRuParser(*args, **kwargs).get_game_genres(game_name)


if __name__ == '__main__':
    from common import _common_test
    _common_test(get_game_genres)
    """
    Search 'Hellgate: London'...
        Genres: ['Вид от первого лица', 'Вид от третьего лица', 'Постапокалиптика', 'Ролевая игра', 'Футуризм (Будущее)', 'Шутер', 'Экшен']
    
    Search 'The Incredible Adventures of Van Helsing'...
        Genres: []
    
    Search 'Dark Souls: Prepare to Die Edition'...
        Genres: ['Вид от третьего лица', 'Ролевая игра', 'Фэнтези / средневековье', 'Экшен']
    
    Search 'Twin Sector'...
        Genres: ['Вид от первого лица', 'Футуризм (Будущее)', 'Экшен']
    
    Search 'Call of Cthulhu: Dark Corners of the Earth'...
        Genres: ['Вид от первого лица', 'Стелс', 'Хоррор', 'Экшен']    
    """
