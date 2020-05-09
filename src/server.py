#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import List

import cgi
import glob
import http.server
import json
import os
import random
import shutil
import ssl
import urllib.parse

import importer
from clauswitz import parser


class StellarisHandler(http.server.BaseHTTPRequestHandler):
    server_version = "StellarisEmpireSharer"

    def do_GET(self: StellarisHandler):
        """Serve a GET request."""

        # Get the actual request path, excluding the query string.
        path: str = urllib.parse.urlparse(self.path).path

        # Route the request to the handling function
        if path == "/":
            self.page_file("html/upload.html", "text/html")
        elif path == "/upload.js":
            self.page_file("html/upload.js", "application/javascript")
        elif path == "/generate":
            self.download_user_empires()
        elif path == "/ajax-approved":
            self.page_ajax_list("approved")
        elif path == "/ajax-pending":
            self.page_ajax_list("pending")
        else:
            self.send_error(404)

    def page_file(self: StellarisHandler, filename: str, mime: str):
        """Sends an on-disk file to the client, with the given mime type"""

        # 404 if the file is not found.
        if not os.path.exists(filename):
            self.send_error(404)
            return

        with open(filename, "rb") as contents:
            # stat(2) the file handle to get the file size.
            stat = os.fstat(contents.fileno())

            # Send the HTTP headers.
            self.success_headers(mime, stat.st_size)

            # Send the file to the client
            shutil.copyfileobj(contents, self.wfile)

    def page_ajax_list(self: StellarisHandler, folder: str):
        """Sends an AJAX fragment listing available files in a folder"""

        # Get the list of files that are in the file.
        files = glob.glob(f"{folder}/**/*.txt")
        output: List = []

        for filename in files:
            # Parse the Empire in the file.
            with open(filename, "r") as handle:
                obj = parser.parse(handle)

            # Extract the empire data out of the wrapper object.
            if isinstance(obj, list) and len(obj) == 1:
                if isinstance(obj[0], tuple):
                    obj = obj[0][1]

            # Get the fields we want in the fragment.
            name = importer.get_value(obj, "key")
            author = importer.get_value(obj, "author")
            ethics = importer.get_values(obj, "ethic")

            # Add to the output list
            output.append({"author": author, "name": name, "ethics": ethics})

        # Convert the list to JSON for JS client.
        jsondata = json.dumps(output).encode("utf-8")

        # Send the response
        self.success_headers("text/json", len(jsondata))
        self.wfile.write(jsondata)

    def download_user_empires(self: StellarisHandler):
        # Parse the query parameters to get the config for the download.
        query = urllib.parse.urlparse(self.path).query
        data = urllib.parse.parse_qs(query)

        # There must be an `empire_count`
        if "empire_count" not in data:
            self.send_error(400)
            return

        #
        count: int = int(data["empire_count"][0])
        unmod: bool = "include_unmoderated" in data

        # Find all possible empires
        files = glob.glob(f"approved/**/*.txt")
        if unmod:
            files = files + glob.glob("pending/**/*.txt")

        # Select [count] of them at random.
        files = random.sample(files, min(count, len(files)))

        # Record the Content-Length
        length: int = sum([os.stat(f).st_size for f in files])

        self.send_header(
            "Content-Disposition", 'attachment; filename="user_empire_designs.txt"'
        )
        self.success_headers("text/plain", length)

        # Concatenate the files into the output
        for filename in files:
            with open(filename, "rb") as handle:
                shutil.copyfileobj(handle, self.wfile)

    def do_POST(self: StellarisHandler):
        if self.path != "/do-upload":
            self.send_error(405)
            return

        ctype = str(self.headers["content-type"]).strip()

        if ";" not in ctype:
            self.send_error(415)
            return

        [ctype, boundary] = ctype.split(";")

        if ctype.strip() != "multipart/form-data":
            self.send_error(415)
            return

        bound_bytes: bytes = boundary.strip().replace("boundary=", "").encode("ascii")

        length = str(self.headers["content-length"]).strip()
        length_bytes = length.encode("ascii")

        msg = cgi.parse_multipart(
            self.rfile, {"boundary": bound_bytes, "CONTENT-LENGTH": length_bytes}
        )

        if "select" not in msg or "file" not in msg or "username" not in msg:
            self.send_error(415)
            return

        self.process_upload(msg)

    def process_upload(self: StellarisHandler, msg):
        # Extract the username, create folders
        username = msg["username"][0]
        username = username.replace("/", "_")
        username = username.replace(".", "_")

        if not username:
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

        report: str = "Attempt Upload " + ", ".join(msg["select"]) + ".\n\n"

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

        report_bytes: bytes = report.encode("utf-8")

        self.success_headers("text/plain", len(report_bytes), code=201)
        self.wfile.write(report_bytes)

    def success_headers(self: StellarisHandler, mime: str, length: int, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(length))
        self.end_headers()


def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    os.chdir("..")

    for folder in ["approved", "pending"]:
        if not os.path.exists(folder):
            os.mkdir(folder)

    httpd = http.server.HTTPServer(("", 8000), StellarisHandler)
    address = httpd.socket.getsockname()
    print(f"Serving HTTP on {address}…")

    if os.path.exists("ssl.cert"):
        httpd.socket = ssl.wrap_socket(
            httpd.socket, certfile="ssl.cert", server_side=True
        )

    httpd.serve_forever()


if __name__ == "__main__":
    main()
