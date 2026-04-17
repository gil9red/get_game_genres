#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from get_game_genres.generate_games.generate_games import FILE_NAME_GAMES_HARDCORED
from get_game_genres.common import load_json, save_json


data: dict = load_json(FILE_NAME_GAMES_HARDCORED)
if data:
    new_data: dict = {
        k: data[k] for k in sorted(data)
    }
    save_json(new_data, FILE_NAME_GAMES_HARDCORED)
