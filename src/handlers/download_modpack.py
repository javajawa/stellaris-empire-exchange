#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

from __future__ import annotations

from typing import Dict, List, Optional, Set

import glob
import http.server
import io
import os
import random
import shutil
import textwrap
import urllib.parse

import clauswitz
import importer


def download_user_empires(self: http.server.BaseHTTPRequestHandler):
    # Parse the query parameters to get the config for the download.
    query = urllib.parse.urlparse(self.path).query
    data = urllib.parse.parse_qs(query)

    # There must be an `empire_count`
    if "empire_count" not in data:
        self.send_error(400, "Missing empire count")
        return

    # There must be an `empire_count`
    if "sources" not in data:
        self.send_error(400, "No sources selected")
        return

    # Extract the input data
    count: int = int(data["empire_count"][0])
    balance: bool = (data.get("balance_authors") or ["off"])[0] == "on"
    sources: List[str] = data.get("sources") or []

    # Create the mod pack
    mod = clauswitz.ModPack("Random Empires Modpack", "random-empires", "1.0")
    mod.add_tag("Species")
    mod.stellaris_versions = "2.7.*"

    # Select the empires for the modpack
    files = select_empires(count, sources, balance)

    # Log for debugging
    self.log_message("Input: %d, %s, %s", count, balance, sources)
    self.log_message("Output: %s", files)

    # Add all the empires to the mod pack
    for filename in files:
        add_empire_to_modpack(mod, filename)

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


def select_empires(count: int, sources: List[str], balance_authors: bool) -> List[str]:
    # Find all possible empires
    files: List[str] = []

    for source in sources:
        files = files + glob.glob(f"{source}/**/*.txt")

    if balance_authors:
        return author_balanced_empires(count, files, sources)
    else:
        return random_empires(count, files)


def random_empires(count: int, files: List[str]) -> List[str]:
    # Select [count] of them at random.
    files = random.sample(files, min(count, len(files)))

    return files


def author_balanced_empires(
    count: int, files: List[str], sources: List[str]
) -> List[str]:
    # Select everything if we have more available than the count.
    if len(files) <= count:
        return files

    # Split out the list by author
    author_map = make_author_map(files)

    # Create a list of authors
    author_list: List[str] = [a for a in author_map.keys()]
    selected: Set[str] = set()
    selected_names: Set[str] = set()

    # Build the list of empires.
    # On each pass, work through the author list in a random
    # order, selecting up to one empire each.
    while True:
        random.shuffle(author_list)

        # Attempt to add an empire for each Author
        for author in author_list:

            # For this author, shuffle their empire list
            empires = shuffle_empires(author_map[author], sources)

            # Then add the first valid empire in the shuffled list.
            for empire in empires:
                empire_name = os.path.basename(empire)

                # Having two empires with the same key breaks things.
                if empire_name in selected_names:
                    continue

                selected.add(empire)
                selected_names.add(empire_name)
                break

            # If we have enough empires, stop.
            if len(selected) >= count:
                return list(selected)


def make_author_map(files: List[str]) -> Dict[str, List[str]]:
    # Split out the list by author
    author_map: Dict[str, List[str]] = {}

    for filename in files:
        author = os.path.basename(os.path.dirname(filename))

        if author not in author_map:
            author_map[author] = []

        author_map[author].append(filename)

    return author_map


def shuffle_empires(empires: List[str], sources: List[str]) -> List[str]:
    # We shuffle the list of empires but
    # make sure that they are loaded in source order.
    output: List[str] = []

    for source in sources:
        sublist = [x for x in empires if x.startswith(source + "/")]
        random.shuffle(sublist)
        output = output + sublist

    dangling = [x for x in empires if x not in output]
    random.shuffle(dangling)

    return output + dangling


def add_empire_to_modpack(mod: clauswitz.ModPack, filename: str) -> None:
    # Prepare a file for all the species info
    bios = mod.get_file_writer("species.txt")

    with open(filename, "rb") as empire_file:
        empire = importer.parse(empire_file)

        if isinstance(empire, list) and len(empire):
            empire = empire[0]  # type: ignore

        if isinstance(empire, tuple) and isinstance(empire[1], list):
            empire = empire[1]

        bio: Optional[str] = None
        name = importer.get_value(empire, "key")
        author = importer.get_value(empire, "author")
        species = importer.get_value(empire, "species")

        if isinstance(species, list):
            bio = importer.get_value(species, "species_bio")

        # Write the file contents into the mod pack
        writer = mod.get_file_writer(f"prescripted_countries/10_{author}.txt")
        empire_file.seek(0, io.SEEK_SET)
        shutil.copyfileobj(empire_file, writer)

        # Write the species info into the data file.
        header = f"{name} by {author}"
        bios.write(header.encode("utf-8"))
        bios.write(b"\n" + (b"=" * len(header)) + b"\n\n")
        bios.write(
            textwrap.fill(bio, 60).encode("utf-8")
            if bio
            else b"[No Description Provided]"
        )
        bios.write(b"\n\n")
