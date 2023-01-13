#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import re


def smart_comparing_names(name_1: str, name_2: str) -> bool:
    """
    Функция для сравнивания двух названий игр.
    Возвращает True, если совпадают, иначе -- False.

    """

    # Приведение строк к одному регистру
    name_1 = name_1.lower()
    name_2 = name_2.lower()

    def remove_postfix(text: str) -> str:
        for postfix in ('dlc', 'expansion'):
            if text.endswith(postfix):
                return text[:-len(postfix)]
        return text

    # Удаление символов кроме буквенных, цифр и _: "the witcher®3:___ вася! wild hunt" -> "thewitcher3___васяwildhunt"
    def clear_name(name: str) -> str:
        return re.sub(r'\W', '', name)

    name_1 = clear_name(name_1)
    name_1 = remove_postfix(name_1)

    name_2 = clear_name(name_2)
    name_2 = remove_postfix(name_2)

    return name_1 == name_2
