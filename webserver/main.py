#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from flask import Flask, jsonify

from config import PORT
from db import Game


app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


@app.route("/api/games")
def get_games():
    return jsonify([game.to_dict() for game in Game.select()])


@app.route("/api/game/<name>")
def get_game(name: str):
    game = Game.get_by(name)
    return jsonify(game.to_dict())


if __name__ == '__main__':
    app.run(port=PORT)
