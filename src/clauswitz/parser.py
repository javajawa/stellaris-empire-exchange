#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import Any, IO, List, Tuple, Union

ClausDatum = Union[str, Tuple[str, Any]]
ClausObject = List[ClausDatum]


def parse(handle: IO) -> ClausObject:
    output: ClausObject = []

    while True:
        line = handle.readline()

        if line == "":
            break

        line = line.strip()

        if line == "}":
            break

        if "=" not in line:
            output.append(line.strip('"'))

            continue

        key, value = line.split("=", 1)

        if value == "{":
            value = parse(handle)
        elif value == "yes":
            value = True
        elif value == "no":
            value = False
        else:
            value = value.strip('"')

        key = key.strip('"')
        output.append((key, value,))

    return output


def write(data: ClausObject, handle: IO, depth: int = 0):
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


def write_literal(value: Union[bool, str, float, int], handle: IO):
    if isinstance(value, bool):
        handle.write("yes" if value else "no")
    elif isinstance(value, (int, float)):
        handle.write(value)
    elif value in ["male", "female"]:
        handle.write(value)
    else:
        handle.write(f'"{value}"')
