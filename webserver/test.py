#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import unittest
import uuid

from urllib.parse import quote

import requests

from config import PORT
from db import Game, Genre


URL_BASE = f'http://127.0.0.1:{PORT}'
URL_GAMES = f'{URL_BASE}/api/games'
URL_GAME = f'{URL_BASE}/api/game'
URL_GENRES = f'{URL_BASE}/api/genres'
URL_GENRE = f'{URL_BASE}/api/genre'


class TestCase(unittest.TestCase):
    @staticmethod
    def compare_name_func(x: dict) -> str:
        return x['name']

    def test_api_games(self):
        rs = requests.get(URL_GAMES)
        rs_json: list[dict] = rs.json()
        rs_json.sort(key=self.compare_name_func)

        items: list[dict] = [
            g.to_dict()
            for g in Game.select()
        ]
        items.sort(key=self.compare_name_func)

        self.assertEqual(rs_json, items)

    def test_api_game(self):
        rs = requests.get(URL_GAMES)
        rs_json: list[dict] = rs.json()
        for game in rs_json:
            name = game['name']

            url = f'{URL_GAME}/{quote(name)}'
            rs = requests.get(url)
            try:
                rs_json = rs.json()
            except Exception:
                raise Exception(f'Ошибка с {name!r} результат с сервера: {rs.text!r}')

            self.assertEqual(game, rs_json, f'Ошибка с {name!r} результат с сервера: {rs.text!r}')

    def test_api_game_is_not_found(self):
        name = uuid.uuid4().hex
        url = f'{URL_GAME}/{quote(name)}'
        rs = requests.get(url)
        self.assertIsNone(rs.json())

    def test_api_genres(self):
        rs = requests.get(URL_GENRES)
        rs_json: list[dict] = rs.json()
        rs_json.sort(key=self.compare_name_func)

        items: list[dict] = [
            g.to_dict()
            for g in Genre.select()
        ]
        items.sort(key=self.compare_name_func)

        self.assertEqual(rs_json, items)

    def test_api_genre(self):
        rs = requests.get(URL_GENRES)
        rs_json: list[dict] = rs.json()
        for genre in rs_json:
            name = genre['name']

            url = f'{URL_GENRE}/{quote(name)}'
            rs = requests.get(url)
            try:
                rs_json = rs.json()
            except Exception:
                raise Exception(f'Ошибка с {name!r} результат с сервера: {rs.text!r}')

            self.assertEqual(genre, rs_json, f'Ошибка с {name!r} результат с сервера: {rs.text!r}')

    def test_api_genre_is_not_found(self):
        name = uuid.uuid4().hex
        url = f'{URL_GENRE}/{quote(name)}'
        rs = requests.get(url)
        self.assertIsNone(rs.json())


if __name__ == '__main__':
    unittest.main()
