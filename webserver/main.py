#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from flask import Flask, jsonify

from config import PORT
from db import Game, Genre


app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


@app.route("/api/games")
def get_games():
    return jsonify([game.to_dict() for game in Game.select()])


@app.route("/api/game/<path:name>")
def get_game(name: str):
    game = Game.get_by(name)
    return jsonify(game.to_dict() if game else None)


@app.route("/api/genres")
def get_genres():
    return jsonify([genre.to_dict() for genre in Genre.select()])


@app.route("/api/genre/<path:name>")
def get_genre(name: str):
    genre = Genre.get_by(name)
    return jsonify(genre.to_dict() if genre else None)


if __name__ == '__main__':
    app.run(port=PORT)
