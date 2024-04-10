"""
Check if the number of files in subfolders is the as given N
"""

import os


def count_files_in_directory(directory, extension):
    """
    Counts the number of files with a given extension in a directory.

    Parameters:
    directory (str): The path of the directory to check.
    extension (str): The file extension to count.

    Returns:
    int: The number of files with the given extension in the directory.
    """
    return sum(
        [file.endswith(extension) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))])


def check_folders_for_file_count(root_dir, target_count, extension):
    """
    Checks each "Processed" subdirectory within the root directory for the correct number of files with a given extension.

    If a "Processed" subdirectory doesn't contain the correct number of files, prints the path of the directory,
    the number of files it contains, and the expected number of files.

    Parameters:
    root_dir (str): The path of the root directory to check.
    target_count (int): The expected number of files in each "Processed" subdirectory.
    extension (str): The file extension to count.

    Returns:
    bool: True if all "Processed" subdirectories contain the correct number of files, False otherwise.
    """
    all_correct = True
    for subdir in os.listdir(root_dir):
        subdir_path = os.path.join(root_dir, subdir)
        if os.path.isdir(subdir_path):
            processed_dir = os.path.join(subdir_path, "Processed")
            if os.path.isdir(processed_dir):
                file_count = count_files_in_directory(processed_dir, extension)
                if file_count != target_count:
                    print(f"The folder '{processed_dir}' contains {file_count} files, not {target_count}.")
                    all_correct = False
    return all_correct


path = r"C:/Users/runiza.TY2206042/OneDrive - O365 Turun yliopisto/Desktop/2023 Carbon dark storage"
N = 8
extension = '.png'  # replace with your target extension
check_folders_for_file_count(path, N, extension)

if check_folders_for_file_count(path, N, extension):
    print("All 'Processed' folders contain the correct number of files with the given extension.")
