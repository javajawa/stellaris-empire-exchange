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

from typing import List, Optional

import os
import shutil


def create_prereq(
    target_folder: str,
    modname_long: str,
    modname_short: str,
    supported_version: str,
    dependencies: List[str],
    tags: List[str],
    mod_versionno: str = "1.0",
    thumbnail_file: Optional[str] = None,
):
    """
    Creates all the prerequisites

    :param target_folder:     Path to where this mod should be generated.
    :param modname_long:      Name of the mod.
    :param modname_short:     Name of the mod's folder.
    :param supported_version: Supported version of Stellaris.
    :param dependencies:      List of mod names this mod depends on.
    :param tags:              List of Steam Workshop tags.
    :param mod_versionno:     Version number of the mod.
    :param thumbnail_file:    Path to a thumbnail to include.
    """

    # Make target folders first
    create_folders(target_folder, modname_short)

    # Then make files
    create_reqfiles(
        target_folder,
        modname_long,
        modname_short,
        mod_versionno,
        supported_version,
        dependencies,
        tags,
    )

    # Add thumbnail
    if thumbnail_file:
        create_thumbnail(target_folder, modname_short, thumbnail_file)


def create_folders(target_folder: str, modname_short: str):
    """
    Make the mandatory folders for the mods

    :param target_folder: Path to where this mod should be generated.
    :param modname_short: Name of the mod's folder.
    """

    # Folders to make
    mod_dir = target_folder + "/mod/"
    modname_dir = mod_dir + modname_short + "/"

    # Make folders  if that folder doesn't exist
    if not os.path.isdir(mod_dir):
        os.mkdir(mod_dir)

    if not os.path.isdir(modname_dir):
        os.mkdir(modname_dir)


def create_reqfiles(
    target_folder: str,
    modname_long: str,
    modname_short: str,
    mod_versionno: str,
    supported_version: str,
    dependencies: List[str],
    tags: List[str],
):
    """
    Creates the prerequisite files
    This is only 'modname.mod' and 'descriptor.mod'
    Both are being kept identical.
    Thus, create modname.mod, copy to descriptor.mod

    :param target_folder:     Path to where this mod should be generated.
    :param modname_long:      Name of the mod.
    :param modname_short:     Name of the mod's folder.
    :param mod_versionno:     Version number of the mod.
    :param supported_version: Supported version of Stellaris.
    :param dependencies:      List of mod names this mod depends on.
    :param tags:              List of Steam Workshop tags.
    """

    mod_dir = target_folder + "/mod/"
    modname_dir = mod_dir + modname_short + "/"
    modname_file = mod_dir + modname_short + ".mod"
    descrip_file = modname_dir + "descriptor.mod"

    # Open Modname
    # Replace any contents
    modname_f = open(modname_file, "w")

    # If there are any issues, close file
    try:
        # Element 1 - name
        name_str = 'name="{0}"\n'.format(modname_long)
        modname_f.write(name_str)

        # Element 1b - mod version
        if mod_versionno:
            version_str = 'version="{0}"\n'.format(mod_versionno)
            modname_f.write(version_str)

        # Element 2 - path
        path_str = 'path="mod/{0}"\n'.format(modname_short)
        modname_f.write(path_str)

        # Element 3 - dependencies (Optional)
        modname_f.write("dependencies={\n")
        for i_item in dependencies:
            modname_f.write('\t"{0}"\n'.format(i_item))

        modname_f.write("}\n")

        # Element 4 - tags
        modname_f.write("tags={\n")
        for tag in tags:
            modname_f.write('\t"{0}"\n'.format(tag))

        modname_f.write("}\n")

        # Element 5 - supported version
        buffer_str = f'supported_version="{supported_version}"\n'
        modname_f.write(buffer_str)

    finally:
        modname_f.close()

    # Copy modname_file to descrip_file
    shutil.copyfile(modname_file, descrip_file)


def create_thumbnail(
    target_folder,  # String - path to where this mod should be generated
    modname_short,  # String - name of the mod, will be used to make the mod's folder
    thumbnail_file,  # String - path to thumbnail file if one should be included
):
    # Should we make the thumbnail?
    file_provided = len(thumbnail_file) > 0
    if file_provided:
        (_, suffix) = os.path.splitext(thumbnail_file)
        suffix_good = suffix == ".png"

        file_exists = os.path.isfile(thumbnail_file)
    else:
        file_exists = False
        suffix_good = False

    if file_provided and file_exists and suffix_good:
        # Copies the thumbnail file to the correct folder
        mod_dir = target_folder + "/mod/"
        modname_dir = mod_dir + modname_short + "/"
        mod_thumbnail_filename = modname_dir + "thumbnail.png"

        shutil.copyfile(thumbnail_file, mod_thumbnail_filename)

    # END create_thumbnail


def zip_stellaris_mod(
    target_folder,  # String - path to where this mod should be generated
    modname_short,  # String - name of the mod, will be used to make the mod's folder
):
    # Definitions
    # Zipfile to create without extension
    mod_zipfile = target_folder + "/" + modname_short
    # Mod directory (the one we want to zip up)
    mod_dir = target_folder + "/mod/"

    shutil.make_archive(mod_zipfile, "zip", mod_dir, ".")

    mod_zipefile_true = mod_zipfile + ".zip"

    return mod_zipefile_true


def cleanup_directory(
    target_folder: str,  # path to where this mod should be generated
):
    # Cleans up the directory
    # Deletes mod directory, which contains the modname.mod file and all other files.
    # Warning; this may cleanup unreleated files.
    mod_dir = os.path.join(target_folder, "mod")

    if os.path.isdir(mod_dir):
        shutil.rmtree(mod_dir)
