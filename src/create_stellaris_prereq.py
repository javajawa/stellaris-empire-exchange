# -*- coding: utf-8 -*-

# os to use mkdir, path.splitext and path.isfile
import os
# Copyfile to copy files around
from shutil import copyfile
# Zipping commands
from shutil import make_archive
# Cleanup
from shutil import rmtree

# Functions:
#   create_prereq       Creates all the required files and folders
#   create_folders      Creates the mod folders and required subfolders
#   create_reqfiles     Creates the required files for a mod to function.
#   create_thumbnail    Creates a thumbnail file.
#   zip_stellaris_mod   Turns the mod into a zip

def create_prereq(target_folder,            # String - path to where this mod should be generated
                  modname_long,             # String - name of the mod
                  modname_short,            # String - name of the mod, will be used to make the mod's folder
                  mod_versionno = '',       # String - version number of the mod (optional)
                  list_dependancies = [],   # List of Strings - Mod dependancies
                  list_tags = [],           # List of Strings - the Steam Workshop tags
                  supported_version = '',   # String - supported version of Stellaris
                  thumbnail_file = ''       # String - path to thumbnail file if one should be included
                  ):
    # Creates all the prerequisites
    # Actually calls it's subfunctions
    
    # Make target folders first
    create_folders(target_folder, modname_short)
    
    # Then make files
    create_reqfiles(target_folder, modname_long, modname_short,mod_versionno,
                    list_dependancies, list_tags, supported_version )
    
    # Add thumbnail
    create_thumbnail(target_folder, modname_short, thumbnail_file)
    
    # END create_prereq
    
def create_folders(target_folder,           # String - path to where this mod should be generated
                   modname_short            # String - name of the mod, will be used to make the mod's folder
                   ):
    # Make the mandatory folders for the mods
    # Folders to make
    mod_dir = target_folder + '/mod/'
    modname_dir = mod_dir + modname_short + '/'
    
    # Make folders  if that folder doesn't exist
    if not(os.path.isdir(mod_dir)):
        os.mkdir(mod_dir)
    
    if not(os.path.isdir(modname_dir)):
        os.mkdir(modname_dir)
        
    # END create_folders
    
def create_reqfiles(target_folder,            # String - path to where this mod should be generated
                    modname_long,             # String - name of the mod
                    modname_short,            # String - name of the mod, will be used to make the mod's folder
                    mod_versionno = '',       # String - version number of the mod (optional)
                    list_dependancies = [],   # List of Strings - Mod dependancies
                    list_tags = [],           # List of Strings - the Steam Workshop tags
                    supported_version = ''    # String - supported version(s) of Stellaris
                    ):
    # Creates the prerequisite files
    # This is only 'modname.mod' and 'descriptor.mod'
    # Both are being kept identical.
    # Thus, create modname.mod, copy to descriptor.mod
    mod_dir = target_folder + '/mod/'
    modname_dir = mod_dir + modname_short + '/'
    modname_file = mod_dir + modname_short + '.mod'
    descrip_file = modname_dir + 'descriptor.mod'
    
    # Open Modname
    # Replace any contents
    modname_f = open(modname_file, "w")
    # If there are any issues, close file
    try:
        # Element 1 - name
        name_str = 'name="{0}"\n'.format(modname_long)
        modname_f.write(name_str)
        
        # Element 1b - mod version
        if len(mod_versionno) > 0:
            version_str = 'version="{0}"\n'.format(mod_versionno)
            modname_f.write(version_str)
        
        # Element 2 - path
        path_str = 'path="mod/{0}"\n'.format(modname_short)
        modname_f.write(path_str)
        
        # Element 3 - dependancies (Optional)
        if len(list_dependancies) > 0:
            modname_f.write('dependancies={\n')
            for i_item in list_dependancies:
                modname_f.write('\t"{0}"\n'.format(i_item))
                
            modname_f.write('}\n')
        
        # Element 4 - tags
        if len(list_tags) > 0:
            modname_f.write('tags={\n')
            for i_item in list_tags:
                modname_f.write('\t"{0}"\n'.format(i_item))
                
            modname_f.write('}\n')
                
        # Element 5 - supported version
        if len(supported_version) > 0:
            supported_version_str = 'supported_version="{0}"\n'.format(supported_version)
            modname_f.write(supported_version_str)
        
        
    finally:
        modname_f.close()
    
    # Copy modname_file to descrip_file
    copyfile(modname_file,descrip_file)
    
    # END create_reqfiles
    
def create_thumbnail(target_folder,             # String - path to where this mod should be generated
                     modname_short,             # String - name of the mod, will be used to make the mod's folder
                     thumbnail_file             # String - path to thumbnail file if one should be included
                     ):
    # Should we make the thumbnail?
    file_provided = (len(thumbnail_file) > 0)
    if file_provided:
        (a, suffix) = os.path.splitext(thumbnail_file)
        suffix_good = (suffix == '.png')
        
        file_exists = os.path.isfile(thumbnail_file)
    else:
        file_exists = False
        suffix_good = False
        
    if file_provided and file_exists and suffix_good:
        # Copies the thumbnail file to the correct folder
        mod_dir = target_folder + '/mod/'
        modname_dir = mod_dir + modname_short + '/'
        mod_thumbnail_filename = modname_dir + 'thumbnail.png'
        
        copyfile(thumbnail_file, mod_thumbnail_filename)
    
    # END create_thumbnail
    
def zip_stellaris_mod(target_folder,            # String - path to where this mod should be generated
                      modname_short             # String - name of the mod, will be used to make the mod's folder
                      ):
    # Definitions
    # Zipfile to create without extension
    mod_zipfile = target_folder + '/' + modname_short
    # Mod directory (the one we want to zip up)
    mod_dir = target_folder + '/mod/'
    
    make_archive(mod_zipfile,'zip',mod_dir,'.')
    
    mod_zipefile_true = mod_zipfile + '.zip'
    
    return mod_zipefile_true

def cleanup_directory(target_folder,            # String - path to where this mod should be generated
                      modname_short             # String - name of the mod, will be used to make the mod's folder
                      ):
    # Cleans up the directory
    # Deletes mod directory, which contains the modname.mod file and all other files.
    # Warning; this may cleanup unreleated files.
    mod_dir = target_folder + '/mod/'
    
    if os.path.isdir(mod_dir):
        rmtree(mod_dir)