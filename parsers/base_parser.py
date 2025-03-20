#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import logging
import unicodedata
import sys

from abc import ABCMeta, abstractmethod
from logging.handlers import RotatingFileHandler
from pathlib import Path

from bs4 import BeautifulSoup
import requests

from common import get_uniques, get_current_datetime_str, process_umlauts
from config import USER_AGENT, DIR_ERRORS, DIR_LOGS, NEED_LOGS, LOG_FORMAT
from parsers import dump
from third_party.get_valid_filename import get_valid_filename
from third_party.smart_comparing_names import smart_comparing_names


class Singleton(ABCMeta):
    _instances = dict()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)

        return cls._instances[cls]


class BaseParser(metaclass=Singleton):
    _site_name = ""

    def __init__(
        self,
        need_logs: bool = NEED_LOGS,
        dir_errors: Path = DIR_ERRORS,
        dir_logs: Path = DIR_LOGS,
        log_format: str = LOG_FORMAT,
    ):
        self.session = requests.session()
        self.session.headers["User-Agent"] = USER_AGENT

        self._dir_errors = dir_errors
        self._dir_logs = dir_logs

        self.game_name = ""
        self._need_logs = need_logs

        self._log = self._get_logger(log_format)

    @classmethod
    def instance(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def parse_html(cls, data: str | bytes) -> BeautifulSoup:
        return BeautifulSoup(data, "html.parser")

    @classmethod
    def process_response(
        cls,
        rs: requests.Response,
        return_html: bool = False,
        return_json: bool = False,
    ) -> BeautifulSoup | requests.Response | dict | list:
        if return_html:
            return cls.parse_html(rs.content)

        if return_json:
            return rs.json()

        return rs

    def send_get(
            self,
            url: str,
            return_html: bool = False,
            return_json: bool = False,
            **kwargs
    ) -> requests.Response | BeautifulSoup | dict | list:
        rs = self.session.get(url, **kwargs)
        self._on_check_response(rs)
        return self.process_response(
            rs, return_html=return_html, return_json=return_json
        )

    def send_post(
        self,
        url: str,
        data=None,
        json=None,
        return_html: bool = False,
        return_json: bool = False,
        **kwargs,
    ) -> requests.Response | BeautifulSoup:
        rs = self.session.post(url, data=data, json=json, **kwargs)
        self._on_check_response(rs)
        return self.process_response(
            rs, return_html=return_html, return_json=return_json
        )

    def _save_error_response(self, rs: requests.Response):
        self._dir_errors.mkdir(parents=True, exist_ok=True)

        safe_name = get_valid_filename(self.game_name)
        file_name = (
            self._dir_errors
            / f"{self.get_site_name()}_{safe_name}_{get_current_datetime_str()}.dump"
        )
        self.log_debug(f"Сохранение дампа в {file_name}")

        data = dump.dump_all(rs, request_prefix=b"> ", response_prefix=b"< ")
        with open(file_name, "wb") as f:
            f.write(data)

    def _on_check_response(self, rs: requests.Response):
        if rs.ok:
            return

        self.log_warn(
            f"Случилось что-то плохое...: статус HTTP: {rs.status_code}\n{rs.text}"
        )
        self._save_error_response(rs)

    def log_debug(self, msg, *args, **kwargs):
        self._need_logs and self._log.debug(msg, *args, **kwargs)

    def log_info(self, msg, *args, **kwargs):
        self._need_logs and self._log.info(msg, *args, **kwargs)

    def log_warn(self, msg, *args, **kwargs):
        self._need_logs and self._log.warning(msg, *args, **kwargs)

    def log_error(self, msg, *args, **kwargs):
        self._need_logs and self._log.error(msg, *args, **kwargs)

    def log_exception(self, msg, *args, **kwargs):
        self._need_logs and self._log.exception(msg, *args, **kwargs)

    @classmethod
    def get_site_name(cls) -> str:
        if not cls._site_name:
            import inspect
            cls._site_name = Path(inspect.getfile(cls)).stem
        return cls._site_name

    @abstractmethod
    def _parse(self) -> list[str]:
        pass

    def is_found_game(self, game_name: str) -> bool:
        return smart_comparing_names(self.game_name, game_name)

    def get_game_genres(self, game_name: str) -> list[str]:
        self.game_name = game_name
        self.log_info(f"Поиск {game_name!r}...")

        try:
            genres = self._parse()
            genres = [process_umlauts(x.strip()) for x in genres if x]
            genres = get_uniques(genres)
            genres.sort()

        except SystemExit as e:
            raise e

        except BaseException as e:
            self.log_exception("Ошибка при парсинге:")
            raise e

        self.log_info(f"Жанров: {genres}")
        return genres

    def _get_logger(self, log_format: str, encoding: str = "utf-8"):
        dir_logs = self._dir_logs / "parsers"
        dir_logs.mkdir(parents=True, exist_ok=True)

        site = self.get_site_name()

        name = "parser_" + site
        file = dir_logs / (site + ".txt")

        log = logging.getLogger(name)
        log.setLevel(logging.DEBUG)

        formatter = logging.Formatter(log_format)

        fh = RotatingFileHandler(
            file, maxBytes=10_000_000, backupCount=5, encoding=encoding
        )
        fh.setFormatter(formatter)
        log.addHandler(fh)

        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setFormatter(formatter)
        log.addHandler(sh)

        return log

    @classmethod
    def get_norm_text(cls, node) -> str:
        if not node:
            return ""

        text = node.get_text(strip=True)

        # NFKD ™ превратит в TM, что исказит текст, лучше удалить
        text = text.replace("™", "").replace("©", "").replace("©", "®")

        # https://ru.wikipedia.org/wiki/Юникод#NFKD
        # unicodedata.normalize для удаления \xa0 и подобных символов-заменителей
        return unicodedata.normalize("NFKD", text)
