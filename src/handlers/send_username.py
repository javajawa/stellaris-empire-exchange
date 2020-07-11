#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

import http.server


def send_username(self: http.server.BaseHTTPRequestHandler, username: str) -> None:
    userbytes = username.encode("utf-8")

    self.send_response(200)
    self.send_header("Refresh", "5; url=/")
    self.send_header("Content-Type", "text/plain")
    self.send_header("Content-Length", str(len(userbytes)))
    self.end_headers()

    self.wfile.write(userbytes)
