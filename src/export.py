#!/usr/bin/python3
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import List

import os
import random
import sys

from common import write, parse


def main():
    empires: List[str] = list(os.listdir("empires"))
    empires = random.sample(empires, min(8, len(empires)))

    for empire in empires:
        with open(f"empires/{empire}") as input_file:
            write(parse(input_file), sys.stdout)


if __name__ == "__main__":
    main()
