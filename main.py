#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import time

from timeit import default_timer
from threading import Thread

from config import IGNORE_SITE_NAMES
from common import get_logger, get_games_list
from db import db_create_backup, Dump
from generate_games import generate_games as create_generate_games
from generate_genres import create as create_generate_genres
from genre_translate_file import create as create_genre_translate
from parsers import get_parsers, print_parsers
from parsers.base_parser import BaseParser
from third_party.atomic_counter import AtomicCounter
from third_party.seconds_to_str import seconds_to_str
from third_party.wait import wait


# Test
USE_FAKE_PARSER = False
if USE_FAKE_PARSER:
    class FakeParser:
        @classmethod
        def get_site_name(cls): return "<test>"

        @staticmethod
        def get_game_genres(game_name):
            if game_name == 'Foo':
                raise Exception('Error')

            return ['RGB-bar', 'Action-bar']

    # Monkey Patch
    def get_parsers():
        return [FakeParser]

    def get_games_list(): return ['Foo', 'Bar', 'Zet']


log = get_logger()
counter = AtomicCounter()

MAX_TIMEOUT = 10                  # 10 seconds
TIMEOUT_EVERY_N_GAMES = 50        # Every 50 games
TIMEOUT_BETWEEN_N_GAMES = 3 * 60  # 3 minutes

PAUSES = [
    ('15 minutes', 15 * 60),
    ('30 minutes', 30 * 60),
    ('45 minutes', 45 * 60),
    ('1 hour',     60 * 60),
]


def run_parser(parser: BaseParser, games: list[str], max_num_request: int = 5):
    try:
        site_name = parser.get_site_name()
        timeout = 3  # 3 seconds
        number = 0

        for game_name in games:
            if Dump.exists(site_name, game_name):
                continue

            try:
                number += 1
                num_request = 0

                while True:
                    num_request += 1
                    try:
                        if num_request == 1:
                            log.info(f'#{number}. Search genres for {game_name!r} ({site_name})')
                        else:
                            log.info(f'#{number}. Search genres for {game_name!r} ({site_name}). '
                                     f'Attempts {num_request}/{max_num_request}')

                        genres = parser.get_game_genres(game_name)
                        log.info(f'#{number}. Found genres {game_name!r} ({site_name}): {genres}')

                        Dump.add(site_name, game_name, genres)
                        counter.inc()

                        time.sleep(timeout)
                        break

                    except:
                        log.exception(f'#{number}. Error on request {num_request}/{max_num_request} ({site_name})')
                        if num_request >= max_num_request:
                            log.info(f'#{number}. Attempts ended for {game_name!r} ({site_name})')
                            break

                        pause_text, pause_secs = PAUSES[num_request - 1]
                        log.info(f'#{number}. Pause: {pause_text} secs')
                        time.sleep(pause_secs)

                        timeout += 1
                        if timeout > MAX_TIMEOUT:
                            timeout = MAX_TIMEOUT

                if number % TIMEOUT_EVERY_N_GAMES == 0:
                    log.info(
                        f'#{number}. Pause for every {TIMEOUT_EVERY_N_GAMES} games: {TIMEOUT_BETWEEN_N_GAMES} secs'
                    )
                    time.sleep(TIMEOUT_BETWEEN_N_GAMES)

            except:
                log.exception(f'#{number}. Error by game {game_name!r} ({site_name})')

    except:
        log.exception(f'Error:')


if __name__ == "__main__":
    parsers = get_parsers()
    print_parsers(parsers, log=lambda *args, **kwargs: log.info(*args, **kwargs))

    while True:
        try:
            log.info(f'Started')
            t = default_timer()

            db_create_backup()

            games = get_games_list()
            log.info(f'Total games: {len(games)}')

            threads = []
            for parser in parsers:
                threads.append(
                    Thread(target=run_parser, args=[parser, games])
                )
            log.info(f'Total parsers/threads: {len(threads)}')
            log.info(f'Ignore parsers ({len(IGNORE_SITE_NAMES)}): {", ".join(IGNORE_SITE_NAMES)}')

            counter.value = 0

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            log.info(f'Finished. Added games: {counter.value}. Total games: {Dump.select().count()}. '
                     f'Elapsed time: {seconds_to_str(default_timer() - t)}')

            create_genre_translate.run()
            create_generate_genres.run()
            create_generate_games.run()

            wait(hours=1)

        except:
            log.exception('')
            wait(minutes=15)

        finally:
            log.info('')
