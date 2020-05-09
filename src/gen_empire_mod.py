#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

"""
Selection of functions to generate a mod from a user_empire_designs.txt file
"""

from __future__ import annotations

from typing import List

import os
import shutil
import tempfile

# All elements from this is required
import create_stellaris_prereq


def create_empire_mod(
    target_folder: str,
    ued_file: str,
    modname_long: str,
    modname_short: str,
    mod_versionno: str = "",
    thumbnail_file: str = "",
    perform_cleanup: bool = True,
):
    """Creates a single mod

    This mod takes a single user_empire_designs.txt file and creates the
    folder structure to use it
    Returns the name of the zip file created

    :param target_folder:   path to where this mod should be generated
    :param ued_file:        path to the source user_empire_designs.txt file
    :param modname_long:    name of the mod
    :param modname_short:   name of the mod, used in filenames
    :param mod_versionno:   version number of the mod (optional)
    :param thumbnail_file:  path to thumbnail file if one should be included
    :param perform_cleanup: whether to prevent deleting temporary files
    """

    # Define prerequisites: No dependencies
    list_dependencies: List[str] = []

    # Tags: Just changing species
    list_tags = ["Species"]

    # Requires Stellaris Version: 2.*
    supported_version = "2.*"

    # Create prerequisites
    create_stellaris_prereq.create_prereq(
        target_folder,
        modname_long,
        modname_short,
        mod_versionno,
        list_dependencies,
        list_tags,
        supported_version,
        thumbnail_file,
    )

    # Create folders and insert file
    insert_empire_file(target_folder, ued_file, modname_short)

    # Turn the mod folder into a zip
    mod_zipfile = create_stellaris_prereq.zip_stellaris_mod(
        target_folder, modname_short
    )

    # Cleanup created files
    if perform_cleanup:
        create_stellaris_prereq.cleanup_directory(target_folder)

    return mod_zipfile


def create_empire_mod_temp(
    target_folder: str,
    ued_file: str,
    modname_long: str,
    modname_short: str,
    mod_versionno: str = "",
    thumbnail_file: str = "",
):
    """
    # Like create_empire_mod but does so into a temp folder

    :param target_folder:  path to where this mod should be generated
    :param ued_file:       path to the source user_empire_designs.txt file
    :param modname_long:   name of the mod
    :param modname_short:  name of the mod, used in filenames
    :param mod_versionno:  version number of the mod (optional)
    :param thumbnail_file: path to thumbnail file if one should be included
    """

    # Create a temporary folder
    temp_folder = tempfile.mkdtemp()

    # Do all operations as though it were using the temp folder
    mod_zipfile = create_empire_mod(
        temp_folder,
        ued_file,
        modname_long,
        modname_short,
        mod_versionno,
        thumbnail_file,
        True,
    )

    # Copy file to original target_folder
    new_filename = target_folder + "/" + os.path.split(temp_folder)[1] + ".zip"
    shutil.copyfile(mod_zipfile, new_filename)

    shutil.rmtree(temp_folder)

    return new_filename


def insert_empire_file(target_folder: str, ued_file: str, modname_short: str):
    """
    Inserts the empire file into the correct folder

    :param target_folder: path to where this mod should be generated
    :param ued_file:      path to the source user_empire_designs.txt file
    :param modname_short: name of the mod, used in filenames
    """

    # Definitions:
    mod_dir = target_folder + "/mod/"
    modname_dir = mod_dir + modname_short + "/"

    # Folder and file for the actual empire name
    empires_folder = modname_dir + "prescripted_countries/"
    empires_filename = f"01_{modname_short}_countries.txt"
    empires_filepath = empires_folder + empires_filename

    # Make the empires_folder
    if not os.path.isdir(empires_folder):
        os.mkdir(empires_folder)

    # Copy the file around
    shutil.copyfile(ued_file, empires_filepath)
