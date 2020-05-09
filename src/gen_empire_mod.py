#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: nospell ts=4 expandtab

"""
Selection of functions to generate a mod from a user_empire_designs.txt file
"""

from __future__ import annotations

from typing import Dict, Set, Union
from io import BytesIO

import os
import shutil
import zipfile


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
    # The supported version of stellaris.
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

    def add_thumbnail(self: ModPack, thumbnail: Union[BytesIO, str]) -> None:
        """
        Adds a thumbnail to the mod pack

        :param thumbnail: Either a BytesIO of the raw thumbnail data, or
                          the path to the thumbnail file.
        """

        raise Exception("Not yet implemented")

    def normpath(self: ModPack, file_name: str) -> str:
        """
        Normalises a path name to be OS-compliant, and remove relative
        part components.

        Throws an exception if the path is not beneath the current directory.

        :param file_name: The filename
        :return: The normalised filename
        """

        file_path = os.path.normpath(file_name)

        if not file_path or file_path.startswith("."):
            raise Exception(f"Invalid Path: {file_path}")

        return file_path

    def has_file(self: ModPack, file_name: str) -> bool:
        """
        Check if a file already exists in the modpack

        :param file_name: The file name/path in the mod pack
        """

        path = self.normpath(file_name)

        return path in self.files_to_add or path in self.files_to_write

    def add_file(self: ModPack, dest_file: str, source_file: str) -> bool:
        path = self.normpath(dest_file)

        if self.has_file(path):
            return False

        if not os.path.exists(source_file):
            raise Exception(f"File {source_file} does not exist")

        self.files_to_add[path] = source_file

        return True

    def get_file_writer(self: ModPack, dest_file: str) -> BytesIO:
        path = self.normpath(dest_file)

        if path in self.files_to_add:
            raise Exception(f"Can not create file {path} that has been added")

        if path not in self.files_to_write:
            self.files_to_write[path] = BytesIO()

        return self.files_to_write[path]

    def get_metadata(self: ModPack) -> str:
        return "\n".join(
            [
                # Element 1 - Name
                f'name="{self.name}"',
                # Element 2 - Version
                f'version="{self.version}"',
                # Element 3 - path
                f'path="mod/{self.short_name}"',
                # Element 4 - supported version
                f'supported_version="{self.stellaris_versions}"'
                # Element 5 - dependencies
                "dependencies={",
                "\n".join([f'\t"{dep}"' for dep in self.dependencies]),
                "}",
                # Element 6 - tags
                "tags={",
                "\n".join([f'\t"{tag}"' for tag in self.tags]),
                "}",
                "",
            ]
        )

    def write_to_folder(self: ModPack, dest_folder: str) -> None:
        """
        Writes the mod folder and description file to dest_folder.
        """

        mod_folder: str = os.path.join(dest_folder, self.short_name)
        mod_file: str = os.path.join(dest_folder, f"{self.short_name}.mod")

        os.makedirs(mod_folder, exist_ok=True)

        with open(mod_file, "w", encoding="utf-8") as mod_handle:
            mod_handle.write("\ufeff")
            mod_handle.write(self.get_metadata())

        with open(
            os.path.join(mod_folder, "descriptor.mod"), "w", encoding="utf-8"
        ) as mod_handle:
            mod_handle.write("\ufeff")
            mod_handle.write(self.get_metadata())

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

    def write_to_zip(self: ModPack, destination: str) -> None:
        """
        Writes the mod folder and description file to a zip file in destnation.
        """

        with zipfile.ZipFile(
            destination, "w", compression=zipfile.ZIP_LZMA
        ) as zip_file:
            zip_file.comment = f"{self.name} v{self.version}".encode("utf-8")

            zip_file.writestr(f"{self.short_name}.mod", self.get_metadata())
            zip_file.writestr(
                os.path.join(self.short_name, "descriptor.mod"), self.get_metadata()
            )

            for (file_name, source) in self.files_to_add.items():
                path = os.path.join(self.short_name, file_name)
                zip_file.write(source, path)

            for (file_name, contents) in self.files_to_write.items():
                path = os.path.join(self.short_name, file_name)
                zip_file.writestr(path, contents.getvalue())


if __name__ == "__main__":
    mod = ModPack("Test Mod", "test-mod", "0.1")
    mod.add_file("example/text.txt", "requirements.txt")
    mod.write_to_folder("mods")
    mod.write_to_zip("test.zip")
