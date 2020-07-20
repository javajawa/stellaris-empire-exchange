#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import IO

import io
import os
import re
import shutil
import time

from http.server import BaseHTTPRequestHandler

INCLUDE_SNIPPET = re.compile("\\s*<!--include (?P<file>.*)-->\\s*")


def page_file(
    self: BaseHTTPRequestHandler,
    filename: str,
    mime: str,
    folder: str = "",
    status: int = 200,
) -> None:
    """Sends an on-disk file to the client, with the given mime type"""

    filename = folder + filename

    # 404 if the file is not found.
    if not os.path.exists(filename):
        self.send_error(404, f"File not {filename} found on disk")
        return

    reference = str(self.headers.get("If-None-Match", [""])[0])

    with open(filename, "rb") as contents:
        # stat(2) the file handle to get the file size.
        stat = os.fstat(contents.fileno())
        _hash = str(hash(stat))

        if (status == 200) and (_hash == reference):
            send_304(self, stat, _hash)

            return

        if mime == "text/html":
            do_replacement(self, contents, mime, stat, status)

            return

        # Send the HTTP headers.
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(stat.st_size))
        self.send_header("Last-Modified", self.date_time_string(int(stat.st_mtime)))
        self.send_header("Cache-Control", "public; max-age=3600")
        self.send_header("Expires", self.date_time_string(int(time.time() + 3600)))

        self.end_headers()

        # Send the file to the client
        shutil.copyfileobj(contents, self.wfile)


def send_304(self: BaseHTTPRequestHandler, stat: os.stat_result, hash: str) -> None:
    self.send_response(304)
    self.send_header("Last-Modified", self.date_time_string(int(stat.st_mtime)))
    self.send_header("E-Tag", hash)
    self.send_header("Cache-Control", "public; max-age=3600")
    self.send_header("Expires", self.date_time_string(int(time.time() + 3600)))
    self.end_headers()


def do_replacement(
    self: BaseHTTPRequestHandler,
    contents: IO[bytes],
    mime: str,
    stat: os.stat_result,
    status: int,
) -> None:
    output = io.BytesIO()
    stream = io.TextIOWrapper(contents, encoding="utf-8")

    for line in stream:
        match = INCLUDE_SNIPPET.search(line)

        if not match:
            output.write(line.encode("utf-8"))
            continue

        filename = match.group("file")

        if match.start() > 0:
            _slice = slice(0, match.start())
            output.write(line[_slice].encode("utf-8"))

        with open(filename, "rb") as include:
            shutil.copyfileobj(include, output)

        if match.end() < len(line):
            _slice = slice(match.end())
            output.write(line[_slice].encode("utf-8"))

    data = output.getbuffer()

    # Send the HTTP headers.
    self.send_response(status)
    self.send_header("Content-Type", mime)
    self.send_header("Content-Length", str(data.nbytes))
    self.send_header("Last-Modified", self.date_time_string(int(stat.st_mtime)))
    self.send_header("Cache-Control", "public; max-age=3600")
    self.send_header("Expires", self.date_time_string(int(time.time() + 3600)))

    self.end_headers()

    self.wfile.write(data)
