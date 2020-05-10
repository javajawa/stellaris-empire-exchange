#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import List

import glob
import json
import clauswitz
import http.server

import importer


def page_ajax_list(self: http.server.BaseHTTPRequestHandler, folder: str):
    """Sends an AJAX fragment listing available files in a folder"""

    # Get the list of files that are in the file.
    files = glob.glob(f"{folder}/**/*.txt")
    output: List = []

    for filename in files:
        # Parse the Empire in the file.
        with open(filename, "r") as handle:
            obj = clauswitz.parse_data(handle)

        # Extract the empire data out of the wrapper object.
        if isinstance(obj, list) and len(obj) == 1:
            if isinstance(obj[0], tuple):
                obj = obj[0][1]

        # Get the fields we want in the fragment.
        name = importer.get_value(obj, "key")
        author = importer.get_value(obj, "author")
        ethics = importer.get_values(obj, "ethic")

        ethics = [ethic.replace("ethic_", "").replace("_", " ") for ethic in ethics]

        # Add to the output list
        output.append({"author": author, "name": name, "ethics": ethics})

    # Convert the list to JSON for JS client.
    json_data = json.dumps(output).encode("utf-8")

    # Send the response
    self.send_response(200)
    self.send_header("Content-Type", "text/json")
    self.send_header("Content-Length", str(len(json_data)))
    self.end_headers()

    self.wfile.write(json_data)
