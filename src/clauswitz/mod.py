#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

"""
Selection of functions to generate a mod from a user_empire_designs.txt file
"""

from __future__ import annotations

from typing import Dict, Set, Union
from io import BytesIO, StringIO

import os
import shutil
import zipfile

from clauswitz import parser


def normalise_path(file_name: str) -> str:
    """
    Normalises a path name to be OS-compliant, and remove relative
    part components.

    Raises a ValueError if the path is not beneath the current directory,
    either through being an absolute path, or

    # TODO: On Windows, the absolute path check is incorrect.

    :param file_name: The filename

    :return: The normalised filename
    """

    file_path = os.path.normpath(file_name)

    if not file_path or file_path.startswith(".") or file_path.startswith("/"):
        raise ValueError(f"Invalid Path: {file_path}")

    return file_path


class ModPack:
    """
    Describes and builds a ModPack.
    """

    # The display name of the mod.
    name: str
    # The short name / folder name of the mod
    short_name: str
    # The version number of the mod.
    version: str
    # The supported version of Stellaris.
    stellaris_versions: str = "*"

    # List of the mods this mod depends on.
    dependencies: Set[str]
    # List of tags for this mod in mod lists (e.g. Steam).
    tags: Set[str]

    # List of existing files to add to the mod pack
    # { dest filename => source filename }
    files_to_add: Dict[str, str]

    # List of files to add to the mod pack from in memory
    # { dest_filename => buffer }
    files_to_write: Dict[str, BytesIO]

    def __init__(self: ModPack, name: str, short_name: str, version: str):
        self.name = name
        self.short_name = short_name
        self.version = version

        self.dependencies = set()
        self.tags = set()

        self.files_to_add = dict()
        self.files_to_write = dict()

    def add_dependency(self: ModPack, dependency: str) -> None:
        """
        Adds a dependcent to the Mod's tag list.

        This will tell the launcher that another mod is required for this
        mod to work.

        :param dependency: The other mod to list.
        """

        self.dependencies.add(dependency)

    def add_tags(self: ModPack, tag: str) -> None:
        """
        Adds a tag to the Mod's tag list.

        Used in the Steam workshop.

        :param tag: The new tag to add.
        """

        self.tags.add(tag)

    def add_thumbnail(self: ModPack, thumbnail: Union[bytes, str]) -> None:
        """
        Adds a thumbnail to the mod pack

        :param thumbnail: Either a BytesIO of the raw thumbnail data, or
                          the path to the thumbnail file.
        """

        if self.has_file("thumbnail.png"):
            raise FileExistsError("Already have a thumbnail")

        if isinstance(thumbnail, str):
            if os.path.exists(thumbnail):
                self.add_file("thumbnail.png", thumbnail)
                return

            thumbnail = thumbnail.encode("utf-8")

        self.get_file_writer("thumbnail.png").write(thumbnail)

    def has_file(self: ModPack, file_name: str) -> bool:
        """
        Check if a file already exists in the modpack

        :param file_name: The file name/path in the mod pack
        """

        path = normalise_path(file_name)

        return path in self.files_to_add or path in self.files_to_write

    def add_file(self: ModPack, destination_file: str, source_file: str) -> bool:
        """
        Marks a file, which currently exists on disk, to be added to the mod.

        The source file must exist, however its contents will not be read until
        the mod is built. If the file is deleted in the meantime, the behaviour
        is not defined.

        If the source file does not exist, a FileNotFoundError is raised.
        If destination file is not inside the mod pack (e.g. absolute path or
        too many /../ elements, throws a

        Returns true if the source file exists, and the destination file was
        not already in the mod pack.

        :param destination_file: The location of the file in the mod pack.
        :param source_file:      The location of the file currently on disk.

        :return: Whether the file was added.
        """

        # Ensure the destination path is valid
        path = normalise_path(destination_file)

        # Ensure the source file exists
        if not os.path.exists(source_file) and os.path.isfile(source_file):
            raise FileNotFoundError(f"File {source_file} does not exist")

        # Check if there is a duplicate file.
        if self.has_file(path):
            return False

        self.files_to_add[path] = source_file

        return True

    def get_file_writer(self: ModPack, destination_file: str) -> BytesIO:
        """
        Creates a in-memory File writer for a destination_file in the mod pack.

        If this method has previously been called for the same file, then the
        same writer will be returned, allowing for appending. If you need to
        ensure this is a new file, use ModPack.has_file to check.

        This function will raise a FileExistsError if a call to add_file
        has been made with the same destination. It will raise a ValueError
        if the destination path is not a valid relative path to the mod root
        (e.g. is an absolute path or has too many /../ elements).

        :param destination_file: The file to get or create a writer for.

        :return:
        """

        # Ensure the path is valid.
        path = normalise_path(destination_file)

        # If this file has already been added as a copy of and external file,
        # we can't also have it as an in-memory stream.
        if path in self.files_to_add:
            raise FileExistsError(f"Can not create file {path}, as it has been added")

        # If we don't already have a in-memory file with this name, create it.
        if path not in self.files_to_write:
            self.files_to_write[path] = BytesIO()

        # Return the stream
        return self.files_to_write[path]

    def get_metadata(self: ModPack) -> StringIO:
        """
        Gets the mod metadata, for writing to the .mod files.

        :return: The mod's metadata.
        """

        output = StringIO()
        parser.write(
            [
                ("name", self.name),
                ("version", self.version),
                ("path", f"mod/{self.short_name}"),
                ("supported_version", self.stellaris_versions),
                ("dependencies", list(self.dependencies)),
                ("tags", list(self.tags)),
            ],
            output,
        )

        return output

    def write_to_folder(self: ModPack, dest_folder: str) -> None:
        """
        Writes the mod folder and description file to dest_folder.
        """

        mod_folder: str = os.path.join(dest_folder, self.short_name)
        mod_file: str = os.path.join(dest_folder, f"{self.short_name}.mod")

        os.makedirs(mod_folder, exist_ok=True)
        metadata = self.get_metadata()

        with open(mod_file, "w", encoding="utf-8") as mod_handle:
            mod_handle.write("\ufeff")
            shutil.copyfileobj(metadata, mod_handle)

        with open(
            os.path.join(mod_folder, "descriptor.mod"), "w", encoding="utf-8"
        ) as mod_handle:
            mod_handle.write("\ufeff")
            shutil.copyfileobj(metadata, mod_handle)

        for (file_name, source) in self.files_to_add.items():
            dest = os.path.join(mod_folder, file_name)
            dest_dir = os.path.dirname(dest)

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            shutil.copyfile(source, dest)

        for (file_name, content) in self.files_to_write.items():
            dest = os.path.join(mod_folder, file_name)
            dest_dir = os.path.dirname(dest)

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            with open(dest, "wb", encoding="utf-8") as dest_handle:
                dest_handle.write(content.getvalue())

    def write_to_zip(self: ModPack, destination: Union[BytesIO, str]) -> None:
        """
        Writes the mod folder and description file to a zip file in destination.
        """

        with zipfile.ZipFile(
            destination, "w", compression=zipfile.ZIP_LZMA
        ) as zip_file:
            zip_file.comment = f"{self.name} v{self.version}".encode("utf-8")

            metadata = self.get_metadata().getvalue()
            zip_file.writestr(f"{self.short_name}.mod", metadata)
            zip_file.writestr(os.path.join(self.short_name, "descriptor.mod"), metadata)

            for (file_name, source) in self.files_to_add.items():
                path = os.path.join(self.short_name, file_name)
                zip_file.write(source, path)

            for (file_name, contents) in self.files_to_write.items():
                path = os.path.join(self.short_name, file_name)
                zip_file.writestr(path, contents.getvalue())


if __name__ == "__main__":
    mod = ModPack("Test Mod", "test-mod", "0.1")
    print(mod.get_metadata())
    mod.add_tags("Hello")
    print(mod.get_metadata())
    mod.add_file("example/text.txt", "requirements.txt")
    mod.write_to_folder("mods")
    mod.write_to_zip("test.zip")
