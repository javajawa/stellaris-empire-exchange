#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import List

import glob
import http.server
import io
import os
import random
import shutil
import urllib.parse

from clauswitz import ModPack


def download_user_empires(self: http.server.BaseHTTPRequestHandler):
    # Parse the query parameters to get the config for the download.
    query = urllib.parse.urlparse(self.path).query
    data = urllib.parse.parse_qs(query)

    # There must be an `empire_count`
    if "empire_count" not in data:
        self.send_error(400, "Missing empire count")
        return

    # Extract the input data
    count: int = int(data["empire_count"][0])
    unmod: bool = "include_unmoderated" in data

    # Create the mod pack
    mod = ModPack("Random Empires Modpack", "random-empires", "1.0")
    mod.add_tag("Species")
    mod.stellaris_versions = "2.7.*"

    # Add all the empires to the mod pack
    files = select_empires(count, unmod)

    for filename in files:
        author = os.path.basename(os.path.dirname(filename)).replace(" ", "_")
        writer = mod.get_file_writer(f"prescripted_countries/10_{author}.txt")

        with open(filename, "rb") as handle:
            shutil.copyfileobj(handle, writer)

    # Hide all the other default empires
    for filename in [
        "00_top_countries",
        "88_megacorp_prescripted_countries",
        "89_humanoids_prescripted_countries",
        "90_syndaw_prescripted_countries",
        "91_utopia_prescripted_countries",
        "92_plantoids_prescripted_countries",
        "93_lithoids_prescripted_countries",
        "99_prescripted_countries",
    ]:
        mod.get_file_writer(f"prescripted_countries/{filename}.txt")

    zip_buffer = io.BytesIO()
    mod.write_to_zip(zip_buffer)

    self.send_response(200)
    self.send_header("Content-Type", "application/zip")
    self.send_header("Content-Length", str(zip_buffer.tell()))
    self.send_header("Content-Disposition", 'attachment; filename="empires-mod.zip"')
    self.end_headers()

    # Concatenate the files into the output
    zip_buffer.seek(0, io.SEEK_SET)
    shutil.copyfileobj(zip_buffer, self.wfile)


def select_empires(count: int, unmod: bool) -> List[str]:
    # Find all possible empires
    files = glob.glob(f"approved/**/*.txt")

    if unmod:
        files = files + glob.glob("pending/**/*.txt")

    # Select [count] of them at random.
    files = random.sample(files, min(count, len(files)))

    return files
