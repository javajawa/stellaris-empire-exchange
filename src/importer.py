#!/usr/bin/python3
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import List, Optional

import re
import io

from common import ClausObject, ClausDatum, parse, write


def main(filename: str):
    with open(filename) as handle:
        data = handle.read()

    empires = parse_user_empires(data)

    for name, empire in empires:
        if not isinstance(empire, list):
            raise Exception

        if not is_valid_empire(empire):
            continue

        store(empire)
        print("Imported %s" % name)


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
        handle.write('"%s"={\n' % name)
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


def add_value(data: ClausObject, key: str, value: str):
    data.append((key, value))


if __name__ == "__main__":
    main("user_empire_designs.txt")
