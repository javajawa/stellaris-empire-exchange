#!/usr/bin/env python3
# vim: nospell ts=4 expandtab

from __future__ import annotations

import cgi
import glob
import http.server
import json
import os
import shutil
import ssl

import importer
import common


class StellarisHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP request handler with GET/HEAD/POST commands.
    This serves files from the current directory and any of its
    subdirectories. The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.
    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.
    """

    server_version = "StellarisEmpireSharer"

    def do_GET(self):
        """Serve a GET request."""

        if self.path == "/":
            self.page_index()
            return

        if self.path == "/ajax-approved":
            self.page_ajax_list("approved")
            return

        if self.path == "/ajax-pending":
            self.page_ajax_list("pending")
            return

        self.send_error(404)

    def page_index(self: StellarisHandler):
        with open("upload.html", "rb") as contents:
            stat = os.fstat(contents.fileno())

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", str(stat.st_size))
            self.end_headers()

            shutil.copyfileobj(contents, self.wfile)

    def page_ajax_list(self: StellarisHandler, folder: str):
        files = glob.glob(f"{folder}/**/*.txt")
        output = []

        for filename in files:
            with open(filename, "r") as handle:
                obj = common.parse(handle)

            if isinstance(obj, list) and len(obj) == 1:
                obj = obj[0]

            if isinstance(obj, tuple):
                obj = obj[1]

            name = importer.get_value(obj, "key")
            author = importer.get_value(obj, "author")
            ethics = importer.get_values(obj, "ethic")

            output.append({"author": author, "name": name, "ethics": ethics})

        jsondata = json.dumps(output).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/json")
        self.send_header("Content-Length", str(len(jsondata)))
        self.end_headers()

        self.wfile.write(jsondata)

    def do_POST(self):
        if self.path != "/do-upload":
            self.send_error(405)
            return

        ctype = self.headers["content-type"].strip()

        if ";" not in ctype:
            self.send_error(415)
            return

        [ctype, boundary] = ctype.split(";")

        if ctype.strip() != "multipart/form-data":
            self.send_error(415)
            return

        boundary = boundary.strip().replace("boundary=", "").encode("ascii")

        length = self.headers["content-length"].strip()
        length = int(length)

        msg = cgi.parse_multipart(
            self.rfile, {"boundary": boundary, "CONTENT-LENGTH": length}
        )

        if "select" not in msg or "file" not in msg or "username" not in msg:
            self.send_error(415)
            return

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
        wanted = [t.strip().strip('"') for t in msg["select"]]

        report = "Attempt Upload " + ", ".join(msg["select"]) + ".\n\n"

        for name, empire in empires:
            if name not in wanted:
                continue

            if not importer.is_valid_empire(empire):
                report += f"{name} does not appear to be a valid empire?\n"
                continue

            importer.add_value(empire, "author", username)
            importer.store(empire, f"pending/{username}")
            report += f"Stored {name}\n"

        report = report.encode("utf-8")

        self.send_response(201)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", len(report))
        self.end_headers()

        self.wfile.write(report)


def main():
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
