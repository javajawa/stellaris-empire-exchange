# -*- coding: utf-8 -*-

# Selection of functions to generate a mod from a user_empire_designs.txt file

# All elements from this is required
import create_stellaris_prereq
# Copyfile to copy files around
from shutil import copyfile
# Cleanup
from shutil import rmtree
# os for path.isdir and mkdir
import os
# For tempfolder
import tempfile

def create_empire_mod(target_folder,            # String - path to where this mod should be generated
                      ued_file,                 # String - path to the source user_empire_designs.txt file
                      modname_long,             # String - name of the mod
                      modname_short,            # String - name of the mod, used in filenames
                      mod_versionno = '',       # String - version number of the mod (optional)
                      thumbnail_file = '',      # String - path to thumbnail file if one should be included
                      perform_cleanup = True    # bool   - specify False to prevent deleting temporary files 
                      ):
    # Creates a single mod
    # This mod takes a single user_empire_designs.txt file and creates the folder structure to use it
    # Returns the name of the zipfile created
    
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
    
    # Turn the mod folder into a zip
    mod_zipfile = create_stellaris_prereq.zip_stellaris_mod(target_folder, modname_short)

    # Cleanup created files
    if perform_cleanup:
        create_stellaris_prereq.cleanup_directory(target_folder, modname_short)
	
    return mod_zipfile
    # END create_empire_mod
    
def create_empire_mod_temp(target_folder,            # String - path to where this mod should be generated
                           ued_file,                 # String - path to the source user_empire_designs.txt file
                           modname_long,             # String - name of the mod
                           modname_short,            # String - name of the mod, used in filenames
                           mod_versionno = '',       # String - version number of the mod (optional)
                           thumbnail_file = ''      # String - path to thumbnail file if one should be included
                           ):
    # Like create_empire_mod but does so into a temp folder
    temp_folder = tempfile.mkdtemp()
    
    # Do all operations as though it were using the temp folder
    mod_zipfile = create_empire_mod(temp_folder,ued_file,
                                    modname_long,modname_short,mod_versionno,
                                    thumbnail_file,True)
    
    # Copy file to original target_folder
    new_filename = target_folder + '/' + os.path.split(temp_folder)[1] + '.zip'
    copyfile(mod_zipfile, new_filename)
    
    rmtree(temp_folder)
    
    return new_filename
    
    
def insert_empire_file(target_folder,               # String - path to where this mod should be generated
                       ued_file,                    # String - path to the source user_empire_designs.txt file
                       modname_short                # String - name of the mod, used in filenames
                       ):
    # Inserts the empire file into the correct folder
    
    # Definitions:
    mod_dir = target_folder + '/mod/'
    modname_dir = mod_dir + modname_short + '/'
    # Folder and file for the actual empire name
    empires_folder = modname_dir +'prescripted_countries/'
    empires_filename = '01_{0}_countries.txt'.format(modname_short)
    empires_filepath = empires_folder + empires_filename
    
    # Make the empires_folder
    if not(os.path.isdir(empires_folder)):
        os.mkdir(empires_folder)
    
    # Copy the file around
    copyfile(ued_file,empires_filepath)
	
	# END insert_empire_file