#!/usr/bin/env python3
#credit to https://github.com/AndrewJHart/plex_media_sorter
import os
import glob
import shutil
import json

from guessit import guessit


# base & source paths
base_path = '/mnt/usb1/'
source_path = os.path.join(base_path, 'tmp/')


# destination paths
movies_path = 'Movies/'
shows_path = 'Shows/'
ufc_path = 'UFC/'
games_path ='Games/'
comis_path = 'Comics/'

# tuple of globs to handle various levels
# of nesting with downloaded files
paths = (
    '%s**/**/*' % source_path,
    '%s**/*' % source_path,
    '%s*' % source_path
)

# mask for allowed extensions
allowed_extensions = (
    'mkv',
    'mp4',
    'avi',
    'idx',
    'sub',
    'srt'
)

# immutable list/tuple of filenames to ignore or skip
# some of these qre required because they bypass allowed
# extensions e.g. rarbg.com.mp4
excluded_filenames = (
    '.part',
    'sample',
    'sample.avi',
    'sample.mkv',
    'sample.mp4',
    'etrg.mp4',
    'rarbg.com.mp4',
    'rarbg.com.txt',
    'rarbg.txt',
    'index.txt',
    'txt',
    'nfo'
)

# todo whitelist allowed types
allowed_types = ()


# ----------------
# helper functions

"""
helper utility that returns a filename only
from a full path containing path & filename.
Performs 1 split & always returns last value in list
in: '/path/to/movies/movie_name_folder/movie_name.movie'
                                       ----------------
out: 'move_name.movie'
"""
get_filename_from_path = lambda f: f.rsplit('/', 1)[1]


"""
helper utility that returns a path only from
a full path containing both path & filename.
Performs 1 split & returns first value in results list
in: '/path/to/movies/movie_name_folder/movie_name.movie'
     ---------------------------------
                                            
out: '/path/to/movies/movie_name_folder'
"""
get_path_from_filename = lambda f: f.rsplit('/', 1)[0]


"""
helper utility that tries to return the movie filename
by splitting up the path & using the folder name as filename.
Performs 2 splits resulting in list of 3 slots & always returns
the middle slot at position 1
in: '/path/to/movies/movie_name_folder/movie_name.movie'
                      ---------------
out: 'move_name_folder'
"""
build_filename_from_path = lambda f: f.rsplit('/', 2)[1]


"""
helper utility that will extract the file
extension from the provided filename. Because we use
reverse split this function will work properly for 
both single filenames & full path + filename strings.
in: 'movie_name.movie'
in: '/path/to/movies/movie_name_folder/movie_name.movie'
                                                  -----
out: 'movie'
"""
get_extension_from_filename = lambda f: f.rsplit('.', 1)[1]


# ----------------------
# entry point for script

def main():
    """
    The main loop
    uses configured paths & globs to find any files in them - 
    iterating over the found files & gathering metadata
    to perform best guess as to where a media file should
    be moved.
    """
    # display some welcome text to the user
    print('\n\n')
    print(' ====================================================')
    print(' = LETS GET TO SORTING & MOVING YOUR MEDIA FILES :) =')
    print(' ====================================================')
    print('\n')

    # iterate over paths tuple & look for files
    for path in paths:
        # iterate over the glob matches
        for name in glob.glob(path):
            # wrap in try/catch
            #delete empty paths
            if os.path.isdir(name):
                remove_non_media(name)
                continue

            try:
                print('\n<---------------------->\n')
                print('Found: \n %s' % get_filename_from_path(name))
                extension = get_extension_from_filename(name)

                print('This is the extension:%s'% extension)
                # get media metadata for this file
                metadata = guessit(name)

                # get & check media type from metadata
                # first check extensions against banned list
                media_type = get_media_type(metadata)
                
                #check if extension is allow if not delete the file
                if extension.lower() not in allowed_extensions:
                    print('\nFound an excluded file type:%s' % get_filename_from_path(name))
                    remove_non_media(name)
                    continue

                # if 1st return val is true move media
                if media_type:
                    print ('\nType: %s ..' % media_type)
                    move_media_by_type(media_type, name, metadata)
                    continue

                else:
                    print ('\nRemoving %s ..' % name)

                    # remove unneeded files & continue
                    remove_non_media(name)


            except Exception as e:
                raise Exception(e)


def get_media_type(metadata):
    """
    Sorts the type of media (e.g. movie/episode/etc..)
    @param  {dict}  `metadata`  metadata on particular media
    @return [dict or False]     returns dict of type info or False if none
    """

    return metadata.get('type') if 'unknown' not in metadata['type'] else False


def move_media_by_type(media_type, filename, metadata):
    """
    moves media of filename to the proper directory based on type
    @param [str] `media_type`  string value representing type of media
    @param [str] `filemame`    string representing the current filename
    """ 


    subtitle_language = str(metadata.get('subtitle_language'))
    print('subtitle_language:%s' % subtitle_language)
    # extra filename from full path
    name = get_filename_from_path(filename)
    extension = get_extension_from_filename(name)

    tmp_path, tmp_filename = None, None

   
    if extension in allowed_extensions and name.lower() not in excluded_filenames:
        #plex sucks at naming subtitles, guessit also sucks at detecting subtitles
        #so we detect extension and then use guessit to label it correctly for plex

        #DELETE NONENGLISH SUBTITLES should delete all non english subs and 
        #leave only english
        if 'srt' in extension and subtitle_language=='None':

            dest_path = make_folder(metadata, media_type)
            #check if episode and add episode name, season exists already from make_folder
            if media_type == 'episode':
                #TV Shows/Show_Name/Season XX/Show_Name SxxEyy.[Language_Code].ext
                srt_show_name= metadata.get('title') + ' S' + str(metadata.get('season')).zfill(2) + 'E' + str(metadata.get('episode')).zfill(2) + '.en' +'.srt'
                dest_path += '/' + srt_show_name
            else:
                #Example formatting of Movie subtitle plex expects Avatar (2009).en.srt
                dest_path += '/' + get_filename_from_path(dest_path)+ '.en' + '.srt'
                

            print('\nThis subtitle has a name that plex does not recognize.. Moving %s to %s' % (name, dest_path))
            # double check for multiple files of the same name
            if os.path.exists(dest_path):
                #lazzzzzzy
                if os.path.exists(dest_path+'.'):
                    shutil.move(filename, dest_path+'.'+'.')
                else:    
                    shutil.move(filename, dest_path+'.')

            else:
                shutil.move(filename, dest_path)
            return

        if ('srt' in extension) and (subtitle_language!='en'):
            print('\n Non-english subtitle detected deleting:%s' % (name))
            os.remove(filename)
            return

        if 'srt' in extension:

            dest_path = make_folder(metadata, media_type)
            #check if episode and add episode name, season exists already from make_folder
            if media_type == 'episode':
                #TV Shows/Show_Name/Season XX/Show_Name SxxEyy.[Language_Code].ext
                srt_show_name= metadata.get('title') + ' S' + str(metadata.get('season')).zfill(2) + 'E' + str(metadata.get('episode')).zfill(2) + '.en' +'.srt'
                dest_path += '/' + srt_show_name
            else:
                #Example formatting of Movie subtitle plex expects Avatar (2009).en.srt
                dest_path += '/' + get_filename_from_path(dest_path)+ '.en' + '.srt'
            #Example formatting of subtitle plex expects Avatar (2009).en.srt
            print('\nThis subtitle has a name that plex does not recognize.. Moving %s to %s' % (name, dest_path))

            # rename the subs to the episode name with srt extension
            if os.path.exists(dest_path):
                #lazzzzzzy
                if os.path.exists(dest_path+'.'):
                    shutil.move(filename, dest_path+'.'+'.')
                else:    
                    shutil.move(filename, dest_path+'.')

            else:
                shutil.move(filename, dest_path)
            return


        if media_type == 'unknown':
            print('This is unknown.. a folder maybe? skipping..')
            return

        #to distinguish episode from subs, subtitle lagnauge must be None
        elif media_type == 'episode' and subtitle_language == 'None':
            dest_path = os.path.join(base_path, shows_path)
            #make folder structure
            dest_path = make_folder(metadata, media_type)

            print('moving %s %s from %s to %s' % (media_type, filename, name, dest_path))

            # move the file
            try:
                # copy to tv shows directory
                shutil.move(filename, dest_path)

            except Exception as e:
                print('There was an error moving the episode %s' % (filename))

            return

        #to distinguish movies from subs, subtitle lagnauge must be None
        elif media_type == 'movie' and subtitle_language == 'None':
            # cache destination path
            dest_path = os.path.join(base_path, movies_path)
            
            #make folder
            dest_path = make_folder(metadata, media_type)

            print('moving %s %s to %s' % (media_type, name, dest_path))

            # move the file
            try:
                shutil.move(filename, dest_path)
            except Exception as e:
                return

        else:
            print('\nNot a media file %s or unknown media. Unable to determine type..' % (name,))
    else:
        # TRASH
        remove_non_media(filename)
        pass  

    return

def make_folder(metadata, media_type):
    folderpath = ''
    title = str(metadata.get('title'))
    year = str(metadata.get('year'))
    season = str(metadata.get('season'))
    episode = str(metadata.get('episode'))

    # print(title)
    # print(year)
    # print(season)
    # print(episode)
    if not title == 'None':
        folderpath += title

    if media_type == 'movie':
        #make top level folder for movie
        folderpath = os.path.join(base_path, movies_path, folderpath)


    if year !='None':
        folderpath += ' ' + '(' + year + ')'


    #make top level folder for tv show
    if media_type =='episode':
        folderpath = os.path.join(base_path, shows_path, folderpath)


    if media_type == 'episode' and season!='None':
        folderpath += '/S' + season.zfill(2)
        #make folder for season
        folderpath = os.path.join(base_path, shows_path, folderpath)
        
    if not os.path.exists(folderpath):
        os.makedirs(folderpath)
        #print(folderpath)

    return folderpath




def remove_non_media(filename):
    """
    Simple wrapper around os.remove() for single files or empty
     directories with a few additional checks to ensure files 
    that are being removed should be removed.
    @param  {str}  `filename`  string representing the current filename
    """
    #dir_list = os.listdir(filename)

    if os.path.isdir(filename) and len(os.listdir(filename))==0:
        print("Deleting Empty Directory %s" % (filename,))
        os.rmdir(filename)

        return

    # attempt to remove the files that are non-media or subtitles
    try:
        # extra filename from full path
        name = get_filename_from_path(filename)

        extension = get_extension_from_filename(name)

        if os.path.isfile(filename):
            if extension in allowed_extensions:
            	print('allowed extension')
                # double check that we aren't somehow removing a valid file
                                
            else:
                print('%s is TRASH' % (name,))

                # remove the file
                os.remove(filename)

    except Exception as e:
        # os.remove will not remove directories nor do we want it to
        # in this use case - will need to run a cleanup script afterwards
        print("error deleting file, swallowing exception. Original error %s" % e)


def cleanup(path):
    """
    @todo Complete & test; Do not use this yet - unfinished!
    removes the folder & any leftover files within a dir
     that has already been processed. We currently have 
    no state or model to use as indicator of what has been
     handled so its important that this function is invoked 
    in proper order after the media files have been moved.
    """
    if os.path.isfile(path):
        # we need the outermost folder; return
        return

    if os.path.isdir(path):
        # iterate over files within folder & ensure safe to rm
        for filename in glob.glob(path):
            # ensure the extension is allowed to be removed
            extension = get_extension_from_filename(filename)

            if extension in allowed_extensions:
                return
            else:
                shutil.rmtree(path)


    pass


if __name__ == '__main__': 
    main()
