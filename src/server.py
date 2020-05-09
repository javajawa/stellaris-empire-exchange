#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import Dict, Tuple

import cgi
import http.server
import os
import ssl
import urllib.parse

from server import download_user_empires, page_file, page_ajax_list, process_upload


ROUTING: Dict[str, Tuple[callable, ...]] = {
    "/": (page_file, "html/upload.html", "text/html"),
    "/upload.js": (page_file, "html/upload.js", "application/javascript"),
    "/generate": (download_user_empires,),
    "/ajax-approved": (page_ajax_list, "approved"),
    "/ajax-pending": (page_ajax_list, "pending"),
}


class StellarisHandler(http.server.BaseHTTPRequestHandler):
    server_version = "StellarisEmpireSharer"

    def do_GET(self: StellarisHandler):
        """Serve a GET request."""

        # Get the actual request path, excluding the query string.
        path: str = urllib.parse.urlparse(self.path).path

        if path not in ROUTING:
            self.send_error(404)

        func: callable = ROUTING[path][0]
        func(self, *ROUTING[path][1:])


    def do_POST(self: StellarisHandler):
        if self.path != "/do-upload":
            self.send_error(405)
            return

        content_type = str(self.headers["content-type"]).strip()

        if ";" not in content_type:
            self.send_error(415)
            return

        [content_type, boundary] = content_type.split(";")

        if content_type.strip() != "multipart/form-data":
            self.send_error(415)
            return

        bound_bytes: bytes = boundary.strip().replace("boundary=", "").encode("ascii")

        length = str(self.headers["content-length"]).strip()
        length_bytes = length.encode("ascii")

        msg = cgi.parse_multipart(
            self.rfile, {"boundary": bound_bytes, "CONTENT-LENGTH": length_bytes}
        )

        process_upload(self, msg)


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
