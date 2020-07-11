#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import Any, IO, List, Tuple, Union

ClausDatum = Union[str, bool, Tuple[str, Any]]
ClausObject = List[ClausDatum]


def parse(handle: Union[IO[bytes], IO[str]]) -> ClausObject:
    output: ClausObject = []

    while True:
        line = handle.readline()

        if isinstance(line, bytes):
            line = line.decode("utf-8")

        if line == "":
            break

        line = line.strip()

        if line == "}":
            break

        if "=" not in line:
            output.append(line.strip('"'))

            continue

        key, value = line.split("=", 1)
        n_value: Union[ClausDatum, ClausObject]

        if value == "{":
            n_value = parse(handle)
        elif value in ["yes", "no"]:
            n_value = value == "yes"
        else:
            n_value = value.strip('"')

        key = key.strip('"')
        output.append((key, n_value,))

    return output


def write(data: ClausObject, handle: IO[str], depth: int = 0) -> None:
    for item in data:
        handle.write("\t" * depth)

        if not isinstance(item, tuple):
            write_literal(item, handle)
            handle.write("\n")
            continue

        key, value = item

        handle.write(f'"{key}"' if " " in key else key)
        handle.write("=")

        if isinstance(value, list):
            if value:
                handle.write("{\n")
                write(value, handle, depth + 1)
                handle.write("\t" * depth)
                handle.write("}\n")
            else:
                handle.write("{}\n")

        else:
            write_literal(value, handle)
            handle.write("\n")


def write_literal(value: Union[bool, str, float, int], handle: IO[str]) -> None:
    if isinstance(value, bool):
        handle.write("yes" if value else "no")
    elif isinstance(value, (int, float)):
        handle.write(str(value))
    elif value in ["male", "female", "always"]:
        handle.write(value)
    else:
        handle.write(f'"{value}"')
