#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import List, Optional, Union

import re
import io

from clauswitz.parser import ClausObject, ClausDatum, parse, write


def parse_user_empires(data: str) -> ClausObject:
    # Normalise line endings.
    data = data.replace("\r", "")

    # Solve phrases without equal sign
    data = re.sub(r"([A-Za-z0-9_.\-]+){", r"\1={", data)
    data = re.sub(r"=\s*{", r"={", data, 0, re.MULTILINE)
    data = re.sub(r"\n={", r"={", data, 0, re.MULTILINE)
    data = re.sub(r"={(.)", r"={\n\1", data, 0, re.MULTILINE)

    # Hack for random empty objects start of the line
    data = re.sub(r"^\s*{\s*\}", r"", data, 0, re.MULTILINE)

    return parse(io.StringIO(data))


def store(empire: ClausObject, folder: str = "pending"):
    name = get_value(empire, "key")
    filename = f"{folder}/{name}.txt"

    with open(filename, "w") as handle:
        handle.write(f'"{name}"={{\n')
        write(empire, handle, 1)
        handle.write("}\n")


def is_valid_empire(data: ClausObject):
    if not has_value(data, "key"):
        return False

    if not has_value(data, "origin"):
        return False

    if not has_value(data, "empire_flag"):
        return False

    if not has_value(data, "ruler"):
        return False

    if not has_value(data, "civics"):
        return False

    if not has_value(data, "spawn_enabled"):
        return False

    if not has_value(data, "spawn_as_fallen"):
        return False

    return True


def get_values(data: ClausObject, key: str) -> List[ClausDatum]:
    tuples = [t for t in data if isinstance(t, tuple)]

    return [t[1] for t in tuples if t[0] == key]


def has_value(data: ClausObject, key: str) -> bool:
    return len(get_values(data, key)) == 1


def get_value(data: ClausObject, key: str) -> Optional[ClausDatum]:
    candidates = get_values(data, key)

    if not candidates:
        return None

    if len(candidates) > 1:
        raise Exception("Multiple values")

    return candidates[0]


def add_value(data: ClausObject, key: str, value: Union[bool, str]):
    data.append((key, value))


def is_value(value: ClausDatum, key: str) -> bool:
    return isinstance(value, tuple) and value[0] == key


def remove_values(data: ClausObject, key: str) -> None:
    data[:] = filter(lambda x: not is_value(x, key), data)
