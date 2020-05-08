# -*- coding: utf-8 -*-

# Selection of functions to generate a mod from a user_empire_designs.txt file

# All elements from this is required
import create_stellaris_prereq
# Copyfile to copy files around
from shutil import copyfile
# os for path.isdir and mkdir
import os

def create_empire_mod(target_folder,            # String - path to where this mod should be generated
                      ued_file,                 # String - path to the source user_empire_designs.txt file
                      modname_long,             # String - name of the mod
                      modname_short,            # String - name of the mod, used in filenames
                      mod_versionno = '',       # String - version number of the mod (optional)
                      thumbnail_file = ''       # String - path to thumbnail file if one should be included
                      ):
    # Creates a single mod
    # This mod takes a single user_empire_designs.txt file and creates the folder structure to use it
    
    # Define prerequisites
    #   No depenancies
    list_dependancies = []
    #   Minimal Tags
    list_tags = ['Species']
    #   supported_version
	#      This is 2.* because that seems like the best option
    supported_version = '2.*'
    
    # Create prerequisites
    create_stellaris_prereq.create_prereq(target_folder, modname_long, modname_short, mod_versionno,
                                          list_dependancies, list_tags, supported_version, thumbnail_file)
    
    # Create folders and insert file
    insert_empire_file(target_folder, ued_file, modname_short)
	
	# END create_empire_mod
    
def insert_empire_file(target_folder,               # String - path to where this mod should be generated
                       ued_file,                    # String - path to the source user_empire_designs.txt file
                       modname_short                # String - name of the mod, used in filenames
                       ):
    # Inserts the empire file into the correct folder
    
    # Definitions:
    mod_dir = target_folder + '/' + modname_short + '/'
    # Folder and file for the actual empire name
    empires_folder = mod_dir +'prescripted_countries/'
    empires_filename = '01_{0}_countries.txt'.format(modname_short)
    empires_filepath = empires_folder + empires_filename
    
    # Make the empires_folder
    if not(os.path.isdir(empires_folder)):
        os.mkdir(empires_folder)
    
    # Copy the file around
    copyfile(ued_file,empires_filepath)
	
	# END insert_empire_file