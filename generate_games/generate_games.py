#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re

from pathlib import Path

from common import load_json, save_json, get_logger, process_list
from db import Dump, Game
from genre_translate_file.load import FILE_NAME_GENRE_TRANSLATE

log = get_logger("generate_games.txt")


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


def fill_dlc(game_by_genres: dict[str, list[str]]) -> None:
    log.info("Заполнение жанров DLC игр")

    not_defined_dlc: list[str] = [
        name
        for name, genres in game_by_genres.items()
        if (
            # Поиск игр с названием типа (DLC)
            re.search(r"\(\w+\)", name)
            # Игры нет в БД
            and not Game.get_by(name)
            # У игры нет жанра
            and not genres
        )
    ]
    log.info(f"Не имеют жанры: {len(not_defined_dlc)}")

    for name_dlc in not_defined_dlc:
        variants: list[str] = []
        for name in game_by_genres:
            if name_dlc == name:
                continue

            if (
                re.sub(r"\W", "", name_dlc)
                .upper()
                .startswith(re.sub(r"\W", "", name).upper())
            ):
                variants.append(name)

        if variants:
            # Выбираем игры с наибольшим количеством символов
            name = max(variants, key=len)
            genres: list[str] = game_by_genres[name]
            if genres:  # Если у игры есть жанры, то добавляем их в DLC
                log.info(f"{name!r} -> {name_dlc!r} = {genres}")
                game_by_genres[name_dlc] = game_by_genres[name]


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

    created: int = 0
    updated: int = 0
    total: int = len(db_dump_game_by_genres)

    for db_dump_game, db_dump_genres in db_dump_game_by_genres.items():
        is_new_in_db: bool = db_dump_game not in db_game_by_genres
        if is_new_in_db:
            log.info("")
            log.info(
                f"Добавлена игра {db_dump_game!r} с жанрами ({len(db_dump_genres)}): {db_dump_genres}"
            )
            created += 1

        need_log: bool = is_new_in_db  # NOTE: Меньше логов для существующих игр

        # Заполнение жанров из файла захаркоденных жанров или высчитывается из жанров дампа
        if db_dump_game not in file_game_by_genres_hardcored:
            new_genres: list[str] = []
            for x in db_dump_genres:
                tr_genres = genre_translate.get(x)
                if not tr_genres:  # null, [], ""
                    continue

                if isinstance(tr_genres, str):
                    new_genres.append(tr_genres)
                elif isinstance(tr_genres, list):
                    new_genres.extend(tr_genres)
                else:
                    if need_log:
                        log.warning(f"Неподдерживаемый тип жанров {tr_genres} из {x!r}")

            new_genres = do_genres_compression(new_genres, need_log=need_log)
            new_genres = remove_partial_duplicates(new_genres, need_log=need_log)

            if need_log:
                log.info(
                    f"Завершение трансляции жанров ({len(new_genres)}): {new_genres}"
                )
        else:
            new_genres: list[str] = file_game_by_genres_hardcored[db_dump_game]
            if need_log:
                log.info(
                    f"Жанры из явно заданного списка ({len(new_genres)}): {new_genres}"
                )

        new_genres = process_list(new_genres)

        # Текущие игры в базе данных таблицы Game
        # NOTE: В db_game_genres список жанров уже обработаны через process_list
        db_game_genres: list[str] = db_game_by_genres.get(db_dump_game, [])

        if not is_new_in_db and new_genres and db_game_genres != new_genres:
            log.info(
                f"Изменение жанров игры {db_dump_game!r} ({len(db_game_genres)}):"
                f" {db_game_genres} -> {new_genres}"
            )
            updated += 1

        # Если новая игра в файле, или если она уже была создана, но появились новые жанры
        if (
            db_dump_game not in file_game_by_genres
            or (db_dump_game in file_game_by_genres and new_genres)
        ):
            file_game_by_genres[db_dump_game] = new_genres

    log.info(
        f"Завершение поиска игр. Всего игр: {total}, "
        f"новые: {created}, обновлено: {updated}."
    )

    fill_dlc(file_game_by_genres)

    if created or updated:
        log.info(f"Сохранение в {FILE_NAME_GAMES}")
        save_json(file_game_by_genres, FILE_NAME_GAMES)
    else:
        log.info("Сохранять нет необходимости")

    for db_dump_game, db_dump_genres in file_game_by_genres.items():
        Game.add_or_update(db_dump_game, db_dump_genres)

    log.info("Завершено!\n")


if __name__ == "__main__":
    run()
