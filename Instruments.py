import os
import glob
import shutil
import subprocess
import sys
import random
import re
# from cv2 import cv2
import cv2
from dateutil.parser import parse
from numba import njit
from rembg import remove
from screeninfo import get_monitors
from collections import defaultdict


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


def get_newest_file(dir_path, extension='.json'):
    """
    Get the newest type of file in the specified directory.
    :param dir_path: The path to the directory
    :param extension: The extension of the file looking for. Default '.json'
    :return: The path to the newest type of file
    """
    # Get list of all files in the directory
    all_files = glob.glob(os.path.join(dir_path, '*' + extension))
    if not all_files:  # If there are no such files, return None
        return None

    # Get the newest file
    return max(all_files, key=os.path.getmtime)


def get_newest_file_global(root_dir, suffix):
    """
    Get the newest file that contains the given suffix in the specified directory and its subdirectories.

    :param root_dir: The root directory to start the search
    :param suffix: The suffix to look for in filenames
    :return: The path to the newest file that contains the suffix, or None if no such file is found
    """
    newest_file = None
    newest_time = 0

    # Walk through the directory, including subdirectories
    for dir_path, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if suffix in filename:
                full_path = os.path.join(dir_path, filename)
                m_time = os.path.getmtime(full_path)
                if m_time > newest_time:
                    newest_time = m_time
                    newest_file = full_path

    return newest_file


def recursive_default_dict():
    return defaultdict(recursive_default_dict)


def random_color() -> str:
    """
    Generate a random color in hexadecimal RGB format.

    :return: A string representing the random color in hexadecimal format (e.g., '#FFFFFF').
    :rtype: str
    """
    return f"#{''.join([f'{random.randint(0, 255):02X}' for _ in range(3)])}"


def row_to_excel_col(row_num):
    """
    Convert a row number to an Excel column letter.

    :param row_num: Row number.
    :return: Excel column letter.
    """
    col = ''
    while row_num:
        remainder = (row_num - 1) % 26
        col = chr(65 + remainder) + col
        row_num = (row_num - 1) // 26
    return col


def remove_pattern(s: str, pattern: str = r"^\d+_\d+_") -> str:
    """
    Remove a specified pattern from the start of a given string.

    The default pattern is set to remove leading integers in the format 'n_m_' from the string, where 'n' and 'm' are integers. This pattern can be overridden by providing a different regular expression pattern.

    :param s: The string from which to remove the pattern.
    :param pattern: The regular expression pattern to remove from the start of the string. Default is '^\d+_\d+_'.
    :type s: str
    :type pattern: str
    :return: The modified string with the specified pattern removed if it was present at the start, otherwise the original string.
    :rtype: str

    Example:
    >>> remove_pattern("123_456_name")
    'name'
    >>> remove_pattern("example_pattern_text", r"^example_pattern_")
    'text'
    """
    if re.match(pattern, s):
        return re.sub(pattern, '', s)
    return s


def map_name(s: str) -> str:
    """
    Special case for the Antient paper.
    Map a given string from the format 'f n-m' to specific names based on the value of 'n'.

    :param s: The string to be mapped.
    :type s: str
    :return: The mapped name based on the specified rules.
    :rtype: str

    Example:
    >>> map_name("f 1-5")
    'SFC-10'
    >>> map_name("f 2-10")
    'TOCNF-Fe3+ Chem'
    """
    mapping = {
        1: "SFC-10",
        2: "TOCNF-Fe3+ Chem",
        3: "CNF-ROD",
        4: "GDE-LignoCNF",
        5: "TOCNF-Fe3+ Phys"
    }

    # Extract 'n' from the string
    match = re.match(r"f (\d+)-\d+", s)
    if match:
        n = int(match.group(1))
        return mapping.get(n, s)  # Return the mapped name or the original string if 'n' is not found in mapping

    return s  # Return original string if it doesn't match the pattern
