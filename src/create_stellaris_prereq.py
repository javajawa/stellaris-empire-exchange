#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

"""
Functions:

    create_prereq       Creates all the required files and folders
    create_folders      Creates the mod folders and required subfolders
    create_reqfiles     Creates the required files for a mod to function.
    create_thumbnail    Creates a thumbnail file.
    zip_stellaris_mod   Turns the mod into a zip
"""

from __future__ import annotations

import os
import shutil


def create_thumbnail(
    target_folder: str,  # String - path to where this mod should be generated
    modname_short: str,  # String - name of the mod, will be used to make the mod's folder
    thumbnail_file: str,  # String - path to thumbnail file if one should be included
):
    # Should we make the thumbnail?
    if not len(thumbnail_file):
        return

    (_, suffix) = os.path.splitext(thumbnail_file)
    suffix_good = suffix == ".png"

    file_exists = os.path.isfile(thumbnail_file)

    if not suffix_good:
        return

    if not file_exists:
        return

    # Copies the thumbnail file to the correct folder
    filename = os.path.join(target_folder, "mod", modname_short, "thumbnail.png")

    shutil.copyfile(thumbnail_file, filename)
