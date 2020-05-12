#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

import http.server
import os
import shutil


def page_file(self: http.server.BaseHTTPRequestHandler, filename: str, mime: str):
    """Sends an on-disk file to the client, with the given mime type"""

    # 404 if the file is not found.
    if not os.path.exists(filename):
        self.send_error(404, "File not found on disk")
        return

    with open(filename, "rb") as contents:
        # stat(2) the file handle to get the file size.
        stat = os.fstat(contents.fileno())

        # Send the HTTP headers.
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(stat.st_size))
        self.send_header("Cache-Control", "public; max-age=3600")
        self.end_headers()

        # Send the file to the client
        shutil.copyfileobj(contents, self.wfile)
