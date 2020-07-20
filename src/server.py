#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple, Union

import cgi
import os
import ssl
import urllib.parse

import bcrypt  # type: ignore

from http.server import ThreadingHTTPServer
from http.server import BaseHTTPRequestHandler as Handler
from http.cookies import SimpleCookie, Morsel

from handlers import (
    download_user_empires,
    logout_handler,
    page_file,
    page_ajax_list,
    process_upload,
    send_username,
)

HandlerWithNoArg = Callable[[Handler], None]
HandlerWithOneArg = Callable[[Handler, str], None]
HandlerWithTwoArgs = Callable[[Handler, str, str], None]
HandlerWithThreeArgs = Callable[[Handler, str, str, str], None]

Handlers = Union[
    HandlerWithNoArg, HandlerWithOneArg, HandlerWithTwoArgs, HandlerWithThreeArgs
]

RouteWithNoArg = Tuple[HandlerWithNoArg, bool]
RouteWithOneArg = Tuple[HandlerWithOneArg, bool, str]
RouteWithTwoArg = Tuple[Union[HandlerWithTwoArgs, HandlerWithThreeArgs], bool, str, str]
RouteWithThreeArg = Tuple[
    Union[HandlerWithTwoArgs, HandlerWithThreeArgs], bool, str, str, str
]

Route = Union[RouteWithNoArg, RouteWithOneArg, RouteWithTwoArg, RouteWithThreeArg]

PostData = Dict[str, List[Union[str, bytes]]]

PostRoute = Union[
    Tuple[Callable[[Handler, PostData], None], bool],
    Tuple[Callable[[Handler, PostData, str], None], bool],
]


ROUTING: Dict[str, Route] = {
    "/": (page_file, False, "html/welcome.html", "text/html"),
    "/logout": (logout_handler, False),
    "/upload": (page_file, True, "html/upload.html", "text/html"),
    "/download": (page_file, False, "html/download.html", "text/html"),
    "/generate": (download_user_empires, False),
    "/username": (send_username, False, "$user"),
    "/sources-list": (page_file, False, "sources.json", "application_json"),
    "/common.js": (page_file, False, "html/common.js", "application/javascript"),
    "/upload.js": (page_file, False, "html/upload.js", "application/javascript"),
    "/sources.js": (page_file, False, "html/sources.js", "application/javascript"),
    "/style.css": (page_file, False, "html/style.css", "text/css"),
    "/menu.png": (page_file, False, "images/menu.png", "image/png"),
}

PREFIX_ROUTING: Dict[str, Route] = {
    "/ethic/": (page_file, False, "2", "image/png", "images/"),
    "/event-": (page_file, False, "1", "image/jpg", "images/"),
    "/ajax/": (page_ajax_list, False, "2"),
}


class StellarisHandler(Handler):
    server_version = "StellarisEmpireSharer"
    protocol_version = "HTTP/1.1"

    def do_GET(self: StellarisHandler) -> None:
        """Serve a GET request."""

        # Get the actual request path, excluding the query string.
        path: str = urllib.parse.urlparse(self.path).path

        # See if we have a route to the current request
        route: Optional[Route] = self.route(path)

        if not route:
            self.send_error(404, f"Path not found {path}")
            return

        username: Optional[str] = None
        handler: Handlers
        needs_auth: bool
        params: List[str] = []
        [handler, needs_auth, *params] = route

        # Get the currently logged in user.
        username = self.auth()

        # A user must be logged in for everything other than the home page.
        if not username and needs_auth:
            self.send_auth_challenge()
            return

        # Sub in path elements in params.
        segments = path.split("/")
        params = [segments[int(x)] if x.isnumeric() else x for x in params]

        # Sub in username in params
        user = username or ""
        params = [user if x == "$user" else x for x in params]

        # Call the current request handler.
        handler(self, *params)

    def route(self: StellarisHandler, path: str) -> Optional[Route]:
        if path in ROUTING:
            return ROUTING[path]

        for prefix in PREFIX_ROUTING:
            if path.startswith(prefix):
                return PREFIX_ROUTING[prefix]

        return None

    def do_POST(self: StellarisHandler) -> None:
        # Get the actual request path, excluding the query string.
        path: str = urllib.parse.urlparse(self.path).path
        route: Optional[PostRoute] = POST_ROUTING.get(path)

        # See if we have a route to the current request
        if not route:
            self.send_error(405, "Can not post to {self.path}")
            return

        [handler, needs_auth] = route
        post = self.get_post_data()

        if not post:
            return

        if not needs_auth:
            handler(self, post)  # type: ignore

            return

        username = self.auth()

        if not username:
            self.send_auth_challenge()
            return

        handler(self, post, username.encode("utf-8"))  # type: ignore

    def get_post_data(self) -> Optional[PostData]:
        content_type = str(self.headers["content-type"]).strip()

        if ";" not in content_type:
            self.send_error(415, f"Invalid Content-Type: {content_type}")
            return None

        [content_type, boundary] = content_type.split(";")

        if content_type.strip() != "multipart/form-data":
            self.send_error(415, f"Invalid Content-Type: {content_type}")
            return None

        bound_bytes: bytes = boundary.strip().replace("boundary=", "").encode("ascii")

        length = str(self.headers["content-length"]).strip()
        length_bytes = length.encode("ascii")

        return cgi.parse_multipart(
            self.rfile, {"boundary": bound_bytes, "CONTENT-LENGTH": length_bytes}
        )

    def auth(self) -> Optional[str]:
        """Checks if a user is authorised"""

        cookies: SimpleCookie[str] = SimpleCookie(self.headers["cookie"])

        user_cookie: Optional[Morsel[str]] = cookies.get("user")
        auth_cookie: Optional[Morsel[str]] = cookies.get("auth")

        user: Optional[str] = user_cookie.value if user_cookie else None
        auth: Optional[str] = auth_cookie.value if auth_cookie else None

        if not user or not auth:
            return None

        check_user = user.lower().encode("utf-8")

        # Open up the current user database.
        with open("users.txt", "r+b") as user_file:
            for line in user_file:
                if line.startswith(b"#") or b":" not in line:
                    continue

                [file_user, hashed] = line.strip(b"\n").split(b":", 1)

                if file_user == check_user:
                    return (
                        user if bcrypt.checkpw(hashed, auth.encode("utf-8")) else None
                    )

        return None

    def send_auth_challenge(self) -> None:
        page_file(self, "html/login.html", "text/html", status=403)


def login(self: Handler, post: PostData) -> None:
    username = str(post.get("username", [""])[0])
    password = str(post.get("password", [""])[0])
    ret_path = str(post.get("return", [""])[0]) or self.headers["referer"] or "/upload"

    self.send_response(302, "Found")
    self.send_header("Content-Length", "0")
    self.send_header("Location", ret_path)

    if not username or not password:
        self.end_headers()
        return

    match_user = username.lower().encode("utf-8")

    with open("users.txt", "r+b") as user_file:
        for line in user_file:
            if line.startswith(b"#") or b":" not in line:
                continue

            [file_user, hashed] = line.strip(b"\n").split(b":", 1)

            if file_user == match_user:
                if bcrypt.checkpw(password.encode("utf-8"), hashed):
                    token = bcrypt.hashpw(hashed, bcrypt.gensalt()).decode("utf-8")

                    self.send_header("Set-Cookie", f"user={username}")
                    self.send_header("Set-Cookie", f"auth={token}")

                self.end_headers()
                return

        # If not matched, add a new user to the file.
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user_file.write(username.lower().encode("utf-8") + b":" + hashed + b"\n")

        token = bcrypt.hashpw(hashed, bcrypt.gensalt()).decode("utf-8")

        self.send_header("Set-Cookie", f"user={username}")
        self.send_header("Set-Cookie", f"auth={token}")

        self.end_headers()


def main() -> None:
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


POST_ROUTING: Dict[str, PostRoute] = {
    "/login": (login, False),
    "/do-upload": (process_upload, True),
}

if __name__ == "__main__":
    main()
