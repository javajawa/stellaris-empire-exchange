#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple, Union

import base64
import cgi
import http.server
import os
import ssl
import urllib.parse

import bcrypt  # type: ignore

from handlers import (
    download_user_empires,
    page_file,
    page_ajax_list,
    process_upload,
    send_username,
)

RouteWithNoArg = Tuple[Callable[[http.server.BaseHTTPRequestHandler], None], bool]
RouteWithOneArg = Tuple[
    Callable[[http.server.BaseHTTPRequestHandler, str], None], bool, str
]
RouteWithTwoArg = Tuple[
    Callable[[http.server.BaseHTTPRequestHandler, str, str], None], bool, str, str
]

ROUTING: Dict[str, Union[RouteWithNoArg, RouteWithOneArg, RouteWithTwoArg]] = {
    "/": (page_file, False, "html/welcome.html", "text/html"),
    "/style.css": (page_file, False, "html/style.css", "text/css"),
    "/event-image.jpg": (page_file, False, "html/event-image.jpg", "image/jpg"),
    "/event-header.jpg": (page_file, False, "html/event-header.jpg", "image/jpg"),
    "/upload": (page_file, True, "html/upload.html", "text/html"),
    "/upload.js": (page_file, True, "html/upload.js", "application/javascript"),
    "/generate": (download_user_empires, True),
    "/ajax-approved": (page_ajax_list, True, "approved"),
    "/ajax-pending": (page_ajax_list, True, "pending"),
    "/username": (send_username, True, "$username"),
}


class StellarisHandler(http.server.BaseHTTPRequestHandler):
    server_version = "StellarisEmpireSharer"

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

        self.protocol_version = "HTTP/1.1"

    def do_GET(self: StellarisHandler):
        """Serve a GET request."""

        # Get the actual request path, excluding the query string.
        path: str = urllib.parse.urlparse(self.path).path

        # See if we have a route to the current request
        if path not in ROUTING:
            self.send_error(404, "Path not found {path}")
            return

        username: Optional[bytes] = None
        handler: Callable
        need_auth: bool
        params: List[str] = []
        [handler, need_auth, *params] = ROUTING[path]

        if need_auth:
            # Get the currently logged in user.
            username = self.auth()

            # A user must be logged in for everything other than the home page.
            if not username and path != "/":
                self.send_auth_challenge()
                return

        if username:
            params = [
                username.decode("utf-8") if x == "$username" else x for x in params
            ]

        # Call the current request handler.
        handler(self, *params) # type: ignore

    def do_POST(self: StellarisHandler):
        username = self.auth()

        if not username:
            self.send_auth_challenge()
            return

        if self.path != "/do-upload":
            self.send_error(405, "Can not post to {self.path}")
            return

        content_type = str(self.headers["content-type"]).strip()

        if ";" not in content_type:
            self.send_error(415, f"Invalid Content-Type: {content_type}")
            return

        [content_type, boundary] = content_type.split(";")

        if content_type.strip() != "multipart/form-data":
            self.send_error(415, f"Invalid Content-Type: {content_type}")
            return

        bound_bytes: bytes = boundary.strip().replace("boundary=", "").encode("ascii")

        length = str(self.headers["content-length"]).strip()
        length_bytes = length.encode("ascii")

        msg = cgi.parse_multipart(
            self.rfile, {"boundary": bound_bytes, "CONTENT-LENGTH": length_bytes}
        )

        process_upload(self, username.decode("utf-8"), msg)

    def auth(self) -> Optional[bytes]:
        """Checks if a user is authorised"""

        auth: bytes = self.headers["authorization"]  # type: ignore

        if not auth:
            print("No auth header")
            return None

        try:
            auth = base64.b64decode(auth[6:])
            [user, password] = auth.split(b":", 1)
        except Exception as ex:
            print("Invalid auth header " + str(ex))
            return None

        if not user or not password:
            return None

        # Open up the current user database.
        with open("users.txt", "r+b") as user_file:
            for line in user_file:
                if line.startswith(b"#") or b":" not in line:
                    continue

                [file_user, hashed] = line.strip(b"\n").split(b":", 1)

                if file_user == user.lower():
                    return user if bcrypt.checkpw(password, hashed) else None

            # If not matched, add a new user to the file.
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
            user_file.write(user.lower() + b":" + hashed + b"\n")

        return user

    def send_auth_challenge(self) -> None:
        self.send_response(401)
        self.send_header(
            "WWW-Authenticate",
            'basic realm="Stellaris Empire Exchange -- Pick a username and password"'
            + 'charset="utf-8"',
        )
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "5")
        self.end_headers()

        self.wfile.write(b"Hello")


def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    os.chdir("..")

    for folder in ["approved", "pending"]:
        if not os.path.exists(folder):
            os.mkdir(folder)

    httpd = http.server.ThreadingHTTPServer(("", 8000), StellarisHandler)
    address = httpd.socket.getsockname()
    print(f"Serving HTTP on {address}…")

    if os.path.exists("ssl.cert"):
        httpd.socket = ssl.wrap_socket(
            httpd.socket, certfile="ssl.cert", server_side=True
        )

    httpd.serve_forever()


if __name__ == "__main__":
    main()
