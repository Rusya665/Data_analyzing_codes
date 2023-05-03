# Files name changing. The main rule: each raw image file name is supposed to be in the format 'yyyy-mm-dd(
# -n)_name.arw', where: 1) yyyy-mm-dd has to correspond to the folder name, i.e. the folder name (date) must be the
# same as the picture DateTime from the EXIF, if not, a warning message will appear. 2) (-n) is the specific format
# which appears only if the folder already contains some properly  named files, in other words, preventing name
# overlapping and allowing multiple photo-sessions per day for the same samples.
import os
import time
from datetime import datetime

import exifread


def _path_check(directory):
    """
    Check if the directory ends with a forward slash, if not, append it.

    :param directory: A string representing a directory path.
    :return: A string representing a directory path ending with a forward slash.
    """
    if directory.endswith('/'):
        return directory
    else:
        return directory + '/'


# Specify a path to a folder with folders with raw images
path_given = 'path/to/your/folder'
path = _path_check(path_given)
folders = os.listdir(path)

start_time = time.time()
# The list of folders which will not be touched by this script
forbidden_list = []
do_list_sample = ['2023-04-21']


def _create_folder(a_folder):  # Creating new folder for storing new data
    """
    Create a new folder to store the renamed image files.

    :param a_folder: A string representing a directory path.
    :return: A string representing a directory path.
    """
    if not os.path.exists(a_folder):
        m = a_folder
        os.makedirs(m)
        return m
    else:
        return str(a_folder)


def log_file_folder(glob_path):
    """
    Create a logs folder to store the log files.

    :param glob_path: A string representing a global folder path.
    :return: A string representing a directory path.
    """
    if 'Photos' not in glob_path:
        return str(glob_path)
    else:
        return str(glob_path.split('Photos')[0] + 'Photos/Logs/')


def _log_file(glob_path, img_folder, img_initial, img_final, kept_images):
    """
    Create a log file containing information about the image files that were renamed and the ones that were not.

    :param glob_path: A string representing a global folder path.
    :param img_folder: A string representing the name of the folder containing the image files.
    :param img_initial: A list of strings representing the initial file names.
    :param img_final: A list of strings representing the final file names.
    :param kept_images: A list of strings representing the file names that were not renamed.
    :return: None
    """
    today = f'{datetime.now():%Y-%m-%d %H.%M.%S%z}'
    log_base = _create_folder(log_file_folder(glob_path))
    log_name = f"{log_base}Log for {img_folder} {today}.txt"
    with open(log_name, "w") as log:
        log.write(f"Log for the folder {img_folder}\n\n")
        log.write(f"Date and time: {today}\n\n")
        log.write(f"Source global_folder: {glob_path}\n")
        if img_final:
            log.write(f'\nInitial images were renamed to:\n')
            for i, j in enumerate(img_initial):
                log.write(f"{i + 1}. {j}\t{img_final[i]}\n")
        if kept_images:
            log.write('\nImages being untouched:\n')
            for q, w in enumerate(kept_images):
                log.write(f"{q + 1}. {w}\n")


def main():
    """
    The main function that renames the image files based on the specified format.
    """
    for folder in folders:
        img_in_folder, img_renamed, img_untouched = [], [], []
        if folder not in forbidden_list:  # Avoid changing name in previous folders
            if folder in do_list_sample:
                session_determinant = str(input("Enter the determinant for the photo sessions if needed: ") or '')
                if session_determinant:
                    session_determinant = "_" + session_determinant
                files = os.listdir(f"{path}/{folder}")
                for file in files:
                    # Getting files only starting with '_' and in ARW format
                    if file.endswith('.ARW'):
                        if file.startswith('_'):
                            path_to_folder = path + folder
                            path_to_file = path + folder + '/' + file
                            f = open(path_to_file, 'rb')
                            tags = exifread.process_file(f, stop_tag='DateTime')
                            date = str(tags.get("Image DateTime"))
                            f.close()
                            if date.split(' ')[0].replace(':', '-') == folder:
                                img_output_path = folder + session_determinant + file
                                os.rename(os.path.join(path_to_folder, file),
                                          os.path.join(path_to_folder, img_output_path))
                                img_in_folder.append(file)
                                img_renamed.append(img_output_path)
                                print(f'In {folder} the file {file} was renamed to'
                                      f' {folder + session_determinant + file}')
                            else:
                                raise ValueError("A very specific bad thing happened."
                                                 "\nThe photo taken date is not the same as the folder's name")
                        else:
                            img_untouched.append(file)
                    if not file.endswith('.ARW'):
                        print(f'Consider moving or deleting these in folder {folder} files {file}')
                _log_file(path, folder, img_in_folder, img_renamed, img_untouched)
    print("\n", "--- %s seconds ---" % (time.time() - start_time))


if __name__ == '__main__':
    main()
