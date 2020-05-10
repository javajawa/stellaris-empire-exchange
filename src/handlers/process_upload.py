#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import List
from clauswitz import ClausObject

import http.server
import os

import importer


def process_upload(self: http.server.BaseHTTPRequestHandler, username: str, msg: dict):
    if "select" not in msg or "file" not in msg or "username" not in msg:
        self.send_error(415)
        return

    for folder in ["approved", "pending"]:
        if not os.path.exists(f"{folder}/{username}"):
            os.mkdir(f"{folder}/{username}")

    # Extract and load the user_empire_designs.txt data.
    upload = msg["file"][0].decode("utf-8")
    empires = importer.parse_user_empires(upload)

    # Get the list of empires we want to import
    wanted: List[str] = [t.strip().strip('"') for t in msg["select"]]

    report = do_import(empires, wanted, username)

    report_bytes: bytes = report.encode("utf-8")

    self.send_response(201)
    self.send_header("Refresh", "5; url=/")
    self.send_header("Content-Type", "text/plain")
    self.send_header("Content-Length", str(len(report_bytes)))
    self.end_headers()

    self.wfile.write(report_bytes)


def do_import(empires: ClausObject, wanted: List[str], username: str) -> str:
    report: str = "Attempt Upload " + ", ".join(wanted) + ".\n\n"

    for name, empire in empires:
        if name not in wanted:
            continue

        if not isinstance(empire, list):
            continue

        if not importer.is_valid_empire(empire):
            report += f"{name} does not appear to be a valid empire?\n"
            continue

        importer.add_value(empire, "author", username)
        importer.store(empire, f"pending/{username}")
        report += f"Stored {name}\n"

    report += "\nPage will refresh in 5 seconds..."

    return report
