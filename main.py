#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import time

from timeit import default_timer
from threading import Thread

# pip install simple-wait
from simple_wait import wait

from common import get_logger, get_games_list
from db import db_create_backup, Dump
from generate_games import generate_games as create_generate_games
from generate_genres import create as create_generate_genres
from genre_translate_file import create as create_genre_translate
from parsers import get_parsers, print_parsers
from parsers.base_parser import BaseParser

from third_party.add_notify_telegram import add_notify
from third_party.atomic_counter import AtomicCounter
from third_party.seconds_to_str import seconds_to_str


# Test
USE_FAKE_PARSER = False
if USE_FAKE_PARSER:
    class FakeParser(BaseParser):
        @classmethod
        def get_site_name(cls):
            return "_test_"

        def _parse(self) -> list[str]:
            if self.game_name == "С_умлаутом":
                return ["Файтинг̆", "Файтинг"]
            return ["RGB-bar", "Action-bar"]

    # Monkey Patch
    def get_parsers():
        return [FakeParser()]

    # Monkey Patch
    def get_games_list():
        return ["Foo", "Bar", "С_умлаутом"]


log = get_logger()
counter = AtomicCounter()

MAX_TIMEOUT: int = 10  # 10 seconds
TIMEOUT_EVERY_N_GAMES: int = 50  # Every 50 games
TIMEOUT_BETWEEN_N_GAMES: int = 3 * 60  # 3 minutes

PAUSES: list[tuple[str, int]] = [
    ("1 минута", 60),
    ("5 минут", 5 * 60),
    ("10 минут", 10 * 60),
    ("15 минут", 15 * 60),
]


def run_parser(parser: BaseParser, games: list[str], max_num_request: int = 5):
    try:
        site_name: str = parser.get_site_name()
        timeout: int = 3  # 3 seconds
        number: int = 0

        for game_name in games:
            if Dump.exists(site_name, game_name):
                continue

            try:
                number += 1
                num_request: int = 0

                while True:
                    num_request += 1
                    try:
                        message = f"#{number}. Поиск жанров для {game_name!r} ({site_name})"
                        if num_request > 1:
                            message = f"{message}. Попытки {num_request}/{max_num_request}"
                        log.info(message)

                        genres: list[str] = parser.get_game_genres(game_name)
                        log.info(
                            f"#{number}. Найдено жанров {game_name!r} ({site_name}): {genres}"
                        )

                        Dump.add(site_name, game_name, genres)
                        counter.inc()

                        time.sleep(timeout)
                        break

                    except:
                        log.exception(
                            f"#{number}. Ошибка при запросе {num_request}/{max_num_request} ({site_name})"
                        )
                        if num_request >= max_num_request:
                            text: str = f"Попытки закончились для {game_name!r} ({site_name})"
                            log.info(f"#{number}. {text}")

                            # Добавляем пустой список жанров, для пропуска игры
                            Dump.add(site_name, game_name, genres=[])

                            # Отправка сообщения в telegram
                            add_notify(log.name, text)
                            break

                        pause_text, pause_secs = PAUSES[num_request - 1]
                        log.info(f"#{number}. Пауза на {pause_text}")
                        time.sleep(pause_secs)

                        timeout += 1
                        if timeout > MAX_TIMEOUT:
                            timeout = MAX_TIMEOUT

                if number % TIMEOUT_EVERY_N_GAMES == 0:
                    log.info(
                        f"#{number}. Пауза за каждые {TIMEOUT_EVERY_N_GAMES} игр: {TIMEOUT_BETWEEN_N_GAMES} секунд"
                    )
                    time.sleep(TIMEOUT_BETWEEN_N_GAMES)

            except:
                log.exception(f"#{number}. Ошибка с игрой {game_name!r} ({site_name})")

    except:
        log.exception(f"Ошибка:")


if __name__ == "__main__":
    parsers = get_parsers()
    print_parsers(parsers, log=lambda *args, **kwargs: log.info(*args, **kwargs))

    while True:
        try:
            log.info(f"Запуск")
            t: float = default_timer()

            db_create_backup()

            games: list[str] = get_games_list()
            log.info(f"Всего игр: {len(games)}")

            threads: list[Thread] = [
                Thread(target=run_parser, args=[parser, games])
                for parser in parsers
            ]
            log.info(f"Всего парсеров/потоков: {len(threads)}")

            counter.value = 0

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            log.info(
                f"Добавлено игр: {counter.value}. Игр в базе: {Dump.select().count()}. "
                f"Пройдено времени: {seconds_to_str(default_timer() - t)}"
            )
            log.info(f"Завершено.\n")

            create_genre_translate.run()
            create_generate_genres.run()
            create_generate_games.run()

            wait(hours=1)

        except:
            log.exception("")
            wait(minutes=15)

        finally:
            log.info("")
