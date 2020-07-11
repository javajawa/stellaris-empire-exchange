#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple, Union

import base64
import cgi
import os
import ssl
import urllib.parse

import bcrypt  # type: ignore

from http.server import ThreadingHTTPServer
from http.server import BaseHTTPRequestHandler as Handler

from handlers import (
    download_user_empires,
    page_file,
    page_ajax_list,
    process_upload,
    send_username,
)

RouteWithNoArg = Tuple[Callable[[Handler], None], bool]
RouteWithOneArg = Tuple[Callable[[Handler, str], None], bool, str]
RouteWithTwoArg = Tuple[Callable[[Handler, str, str], None], bool, str, str]

Route = Union[RouteWithNoArg, RouteWithOneArg, RouteWithTwoArg]

ROUTING: Dict[str, Route] = {
    "/": (page_file, False, "html/welcome.html", "text/html"),
    "/upload": (page_file, True, "html/upload.html", "text/html"),
    "/generate": (download_user_empires, True),
    "/username": (send_username, True, "$user"),
    "/sources-list": (page_file, True, "sources.json", "application_json"),
    "/upload.js": (page_file, True, "html/upload.js", "application/javascript"),
    "/sources.js": (page_file, True, "html/sources.js", "application/javascript"),
    "/style.css": (page_file, False, "html/style.css", "text/css"),
    "/menu.png": (page_file, False, "html/menu.png", "image/png"),
}

PREFIX_ROUTING: Dict[str, Route] = {
    "/ethic/": (page_file, False, "2", "image/png"),
    "/event-": (page_file, False, "1", "image/jpg"),
    "/ajax/": (page_ajax_list, True, "2"),
}


class StellarisHandler(Handler):
    server_version = "StellarisEmpireSharer"

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

        self.protocol_version = "HTTP/1.1"

    def do_GET(self: StellarisHandler):
        """Serve a GET request."""

        # Get the actual request path, excluding the query string.
        path: str = urllib.parse.urlparse(self.path).path

        # See if we have a route to the current request
        route: Optional[Route] = self.route(path)

        if not route:
            self.send_error(404, f"Path not found {path}")
            return

        username: Optional[bytes] = None
        handler: Callable
        need_auth: bool
        params: List[str] = []
        [handler, need_auth, *params] = route

        if need_auth:
            # Get the currently logged in user.
            username = self.auth()

            # A user must be logged in for everything other than the home page.
            if not username and path != "/":
                self.send_auth_challenge()
                return

        # Sub in path elements in params.
        segments = path.split("/")
        params = [segments[int(x)] if x.isnumeric() else x for x in params]

        # Sub in username in params
        user = username.decode("utf-8") if username else ""
        params = [user if x == "$user" else x for x in params]

        # Call the current request handler.
        handler(self, *params)  # type: ignore

    def route(self: StellarisHandler, path: str) -> Optional[Route]:
        if path in ROUTING:
            return ROUTING[path]

        for prefix in PREFIX_ROUTING:
            if path.startswith(prefix):
                return PREFIX_ROUTING[prefix]

        return None

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

    for folder in ["approved", "pending", "historical"]:
        if not os.path.exists(folder):
            os.mkdir(folder)

    httpd = ThreadingHTTPServer(("", 8080), StellarisHandler)
    address = httpd.socket.getsockname()
    print(f"Serving HTTP on {address}…")

    if os.path.exists("ssl.cert"):
        httpd.socket = ssl.wrap_socket(
            httpd.socket, certfile="ssl.cert", server_side=True
        )

    httpd.serve_forever()


if __name__ == "__main__":
    main()
