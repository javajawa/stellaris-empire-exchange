#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

import datetime
import http.server
import os
import shutil
import time


def page_file(self: http.server.BaseHTTPRequestHandler, filename: str, mime: str):
    """Sends an on-disk file to the client, with the given mime type"""

    # 404 if the file is not found.
    if not os.path.exists(filename):
        filename = "html/" + filename

    if not os.path.exists(filename):
        self.send_error(404, "File not found on disk")
        return

    mod_date: int = 0

    if "If-Modified-Since" in self.headers:
        mod_date = int(
            datetime.datetime.strptime(
                str(self.headers["If-Modified-Since"]), "%a, %d %b %Y %H:%M:%S GMT"
            ).timestamp()
        )

    with open(filename, "rb") as contents:
        # stat(2) the file handle to get the file size.
        stat = os.fstat(contents.fileno())

        self.log_message("Dates: %s vs %s", stat.st_mtime, mod_date)
        if int(stat.st_mtime) <= mod_date:
            self.send_response(304)
            self.send_header("Last-Modified", self.date_time_string(int(stat.st_mtime)))
            self.send_header("Cache-Control", "public; max-age=3600")
            self.send_header("Expires", self.date_time_string(int(time.time() + 3600)))
            self.end_headers()

            return

        # Send the HTTP headers.
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(stat.st_size))
        self.send_header("Last-Modified", self.date_time_string(int(stat.st_mtime)))
        self.send_header("Cache-Control", "public; max-age=3600")
        self.send_header("Expires", self.date_time_string(int(time.time() + 3600)))

        self.end_headers()

        # Send the file to the client
        shutil.copyfileobj(contents, self.wfile)
