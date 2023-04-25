import os
import shutil
import subprocess
import sys

# from cv2 import cv2
import cv2
from dateutil.parser import parse
from rembg import remove
from screeninfo import get_monitors


def create_folder(path: str, new_folder: str, side=''):  # Creating new folder for storing new data
    """
    Create a folder inside a given path.
    :param path: Given path
    :param new_folder: Desired name of a new one
    :param side: If exist specific suffix "side"
    :return: String with the folder's name (the folder has been created)
    """
    if not os.path.exists(path + new_folder + side):
        m = path + new_folder + side + '/'
        os.makedirs(m)
        return m
    else:
        return str(path + new_folder + side + '/')


def is_date(string, fuzzy=True):
    ##############################################################
    # https://stackoverflow.com/a/25341965                       #
    ##############################################################
    try:
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False


def collect_files(path: str, extension='.jpg', delete_empty_folders=False):
    """
    Collect files from nested folders to a root one.
    :param path: Path to search
    :param extension: Files extension
    :param delete_empty_folders: Delete empty folders
    :return:
    """
    for dir_path, dir_names, files in os.walk(path):
        for file in files:
            if file.endswith(extension):
                src = dir_path + '/' + file
                dst = path + file
                shutil.move(src, dst)
    if delete_empty_folders:
        deleting_empty_folders(path)


def deleting_empty_folders(path):
    """
    Deleting all empty folder in the given path
    :param path: Path, str
    :return:
    """
    folders = list(os.walk(path))[1:]
    for folder in folders:
        if not folder[2]:
            try:
                os.rmdir(folder[0])
            except OSError:
                pass


def get_screen_settings():
    """
    Get a monitor resolution
    :return: Width and height
    """
    for m in get_monitors():
        if str(m).endswith('is_primary=True)'):
            return int(str(m).split('width=')[-1][:4]), int(str(m).split('height=')[-1][:4])


def delete_background(initial_image):
    """
    Delete background on an image using rembg (https://github.com/danielgatis/rembg)
    :param initial_image: CV2 image. If given as str - open in cv2
    :return: Image with erased background
    """
    if type(initial_image) is str:  # If the input is str read an image
        initial_image = cv2.imread(initial_image)
    return remove(initial_image)


def open_file(path_to_file):
    """
    Run a file. Works on different platforms
    :param path_to_file: Path to a file
    :return:
    """
    if sys.platform == "win32":
        os.startfile(path_to_file)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, path_to_file])
