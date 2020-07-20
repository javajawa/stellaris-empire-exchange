#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from http.server import BaseHTTPRequestHandler


def logout_handler(self: BaseHTTPRequestHandler) -> None:
    self.send_response(302)
    self.send_header("Set-Cookie", "user=; expires=Thu, Jan 01 1970 00:00:00 UTC")
    self.send_header("Set-Cookie", "auth=; expires=Thu, Jan 01 1970 00:00:00 UTC")
    self.send_header("Location", "/")
    self.end_headers()
