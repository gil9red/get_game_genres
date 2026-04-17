#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re

from pathlib import Path

from get_game_genres.common import load_json, save_json, get_logger, process_list
from get_game_genres.db import Dump, Game
from get_game_genres.genre_translate_file.load import FILE_NAME_GENRE_TRANSLATE
from get_game_genres.third_party.add_notify_telegram import add_notify

log = get_logger("generate_games.py.txt")


DIR: Path = Path(__file__).parent.resolve()

FILE_NAME_GAMES: Path = DIR / "game_by_genres.json"
FILE_NAME_GAMES_HARDCORED: Path = DIR / "game_by_genres__hardcored.json"

# Example: "Action", "Adventure" -> "Action-adventure"
GENRE_COMPRESSION: list[tuple[str, str, str]] = [
    ("Action", "Adventure", "Action-adventure"),
    ("Action", "RPG", "Action/RPG"),
    ("First-person", "Shooter", "FPS"),
    ("First-person", "FPS", "FPS"),
    ("Shooter", "FPS", "FPS"),
    ("Third-person", "Shooter", "TPS"),
    ("Third-person", "TPS", "TPS"),
    ("Shooter", "TPS", "TPS"),
    ("Survival", "Horror", "Survival horror"),
    ("RTS", "Strategy", "RTS"),
    ("TBS", "Strategy", "TBS"),
]


def do_genres_compression(genres: list[str], need_log: bool = True) -> list[str]:
    genres = process_list(genres)
    to_remove = set()

    for src_1, src_2, target in GENRE_COMPRESSION:
        if src_1 in genres and src_2 in genres:
            to_remove.add(src_1)
            to_remove.add(src_2)
            genres.append(target)

            if need_log:
                log.info(f"Сжатие жанров {src_1!r} и {src_2!r} -> {target!r}")

    for x in to_remove:
        genres.remove(x)

    return process_list(genres)


def remove_partial_duplicates(genres: list[str], need_log: bool = True) -> list[str]:
    genres = genres.copy()

    # Example: ['Action-adventure', 'Action/RPG', 'Adventure', 'RPG'] ->
    #          -> {('action', 'adventure'): 'Action-adventure', ('action', 'rpg'): 'Action/RPG'}
    words_by_complex_genre: dict[tuple[str], str] = dict()
    for genre in genres:
        words: list[str] = [
            word.lower() for word in map(str.strip, re.split(r"\W", genre)) if word
        ]
        if len(words) > 1:
            words_by_complex_genre[tuple(words)] = genre

    # Example: ['Action-adventure', 'Action/RPG', 'Adventure', 'RPG'] ->
    #          -> ['Action-adventure', 'Action/RPG']
    to_remove = []
    for words, complex_genre in words_by_complex_genre.items():
        for genre in genres:
            if genre.lower() in words:
                if need_log:
                    log.info(
                        f"Удаление частичного дубликата {genre!r} из {complex_genre!r}"
                    )
                to_remove.append(genre)

    for genre in to_remove:
        genres.remove(genre)

    return genres


def process_genres(
    genres: list[str],
    genre_translate: dict[str, str | list[str] | None],
) -> list[str]:
    lower_genre_translate: dict[str, str | list[str] | None] = {
        k.lower(): v for k, v in genre_translate.items()
    }

    new_genres: list[str] = []
    for genre in genres:
        tr_genres = lower_genre_translate.get(genre.lower())
        if not tr_genres:  # Example: null, [], ""
            continue

        if isinstance(tr_genres, str):
            new_genres.append(tr_genres)
        elif isinstance(tr_genres, list):
            new_genres.extend(tr_genres)
        else:
            log.warning(f"Неподдерживаемый тип жанров {tr_genres} из {genre!r}")

    new_genres = do_genres_compression(new_genres, need_log=False)
    new_genres = remove_partial_duplicates(new_genres, need_log=False)
    new_genres = process_list(new_genres)

    return new_genres


def run() -> None:
    log.info("Запуск генератора игр.")

    file_game_by_genres_hardcored: dict[str, list[str]] = load_json(
        FILE_NAME_GAMES_HARDCORED
    )
    log.info(f"Явно заданные игры из файла: {len(file_game_by_genres_hardcored)}")

    log.info("Загрузка кэша...")

    file_game_by_genres: dict[str, list[str]] = load_json(FILE_NAME_GAMES)
    log.info(f"Данных из файла игр: {len(file_game_by_genres)}")

    db_dump_game_by_genres: dict[str, list[str]] = Dump.dump()
    log.info(f"Данных дампа из базы: {len(db_dump_game_by_genres)}")

    db_game_by_genres: dict[str, list[str]] = Game.dump()
    log.info(f"Данных из базы: {len(db_game_by_genres)}")

    genre_translate: dict[str, str | list[str] | None] = load_json(
        FILE_NAME_GENRE_TRANSLATE
    )
    log.info(f"Данных из файла трансляций: {len(genre_translate)}")

    log.info("Завершение загрузки кэша.")
    log.info("")

    log.info("Поиск игр...")

    game_by_genres: dict[str, list[str]] = dict()
    games_not_found_genres: list[str] = []

    for db_dump_game, db_dump_genres in db_dump_game_by_genres.items():
        new_genres: list[str]
        # Заполнение жанров из файла захаркоденных жанров
        if db_dump_game in file_game_by_genres_hardcored:
            new_genres = file_game_by_genres_hardcored[db_dump_game]
        else:
            # Получение жанров из дампа
            new_genres = process_genres(db_dump_genres, genre_translate)

            if any(tag in db_dump_game.upper() for tag in ["(DLC)", "(MOD)"]):
                variant_names: list[str] = []
                for other_name in game_by_genres:
                    if (
                        re.sub(r"\W", "", db_dump_game)
                        .upper()
                        .startswith(re.sub(r"\W", "", other_name).upper())
                    ):
                        variant_names.append(other_name)

                if variant_names:
                    # Выбираем игры с наибольшим количеством символов
                    other_name: str = max(variant_names, key=len)
                    genres: list[str] = game_by_genres[other_name]
                    if genres:  # Если у игры есть жанры, то добавляем их в DLC
                        new_genres = game_by_genres[other_name]

            if not new_genres:
                games_not_found_genres.append(db_dump_game)
                log.warning(f"Не найдены жанры в {db_dump_game!r}")

        game_by_genres[db_dump_game] = new_genres

    if games_not_found_genres:
        lines: list[str] = ["Не найдены жанры в:"]
        for game in games_not_found_genres:
            lines.append(game)
            file_game_by_genres_hardcored[game] = []
        lines.append(
            f"\nИнформация добавлена в файл: {FILE_NAME_GAMES_HARDCORED.name!r}"
        )
        text: str = "\n".join(lines)

        log.info(f"Отправка уведомления:\n{text}")
        add_notify(name="get_game_genres [generate_games]", message=text)

        file_game_by_genres_hardcored: dict = {
            k: file_game_by_genres_hardcored[k] for k in sorted(file_game_by_genres_hardcored)
        }
        save_json(file_game_by_genres_hardcored, FILE_NAME_GAMES_HARDCORED)

    # Считаем разницу
    new_games: set[str] = set(game_by_genres) - set(file_game_by_genres)
    changed_values: dict[str, tuple[list[str], list[str]]] = {
        game: (file_game_by_genres[game], game_by_genres[game])
        for game in set(file_game_by_genres) & set(game_by_genres)
        if file_game_by_genres[game] != game_by_genres[game]
    }

    # Вывод информации
    for game in new_games:
        genres: list[str] = game_by_genres[game]
        log.info(f"Добавлена игра {game!r} с жанрами ({len(genres)}): {genres}")

    for game, (old, new) in changed_values.items():
        log.info(
            f"Изменение жанров игры {game!r}:"
            f" {old} ({len(old)}) -> {new} ({len(new)})"
        )

    # Статистика
    created: int = len(new_games)
    updated: int = len(changed_values)
    total: int = len(game_by_genres)

    log.info("")
    log.info(
        f"Завершение поиска игр. Всего игр: {total}, "
        f"новые: {created}, обновлено: {updated}."
    )

    if created or updated:
        log.info(f"Сохранение в {FILE_NAME_GAMES}")
        save_json(game_by_genres, FILE_NAME_GAMES)
    else:
        log.info("Сохранять нет необходимости")

    # Лишним не будет синхронизация из файла в БД
    for db_dump_game, db_dump_genres in game_by_genres.items():
        Game.add_or_update(db_dump_game, db_dump_genres)

    log.info("Завершено!\n")


if __name__ == "__main__":
    run()
