import os
import sys
import numpy as np
import subprocess


def columns_swap(df, col1='V', col2='I'):
    """
    Swapping two columns in a PandasDataframe and convert str values to floats.
    :param df: An initial dataframe
    :param col1: First column to swap
    :param col2: Second column to swap
    :return: A swapped dataframe
    """
    df[col2] = df[col2].astype(float)
    df[col1] = df[col1].astype(float)
    df[col2] = df[col2].multiply(-1)
    col_list = list(df.columns)
    x, y = col_list.index(col1), col_list.index(col2)
    col_list[y], col_list[x] = col_list[x], col_list[y]
    df = df[col_list]
    return df


def create_folder(path: str, suffix: str):  # Creating new folder for storing new data
    """
    Create a folder inside a given one.
    :param path: Given path
    :param suffix: Desired name of a new one
    :return: String with the folder's name (the folder has been created)
    """
    if suffix:
        if not suffix.endswith('/'):
            suffix = suffix + '/'
    if not os.path.exists(path + suffix):
        m = path + suffix
        os.makedirs(m)
        return m
    else:
        return str(path + suffix)


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


def logger(log_dict: dict):
    """
    The custom "logging" decorator which stores return values of the chosen method/function in a given dict.
    :param log_dict: dict where the method's/function's return is going to be stored
    :return: dict with key as method's/function's name and return values
    """
    def wrap(function):
        def wrapper_log(*args, **kwargs):
            return_value = function(*args, **kwargs)
            log_dict[f'{function.__name__}'] = {}
            log_dict[f'{function.__name__}'][f'{function.__code__.co_varnames[:function.__code__.co_argcount]}'] = \
                return_value
            return return_value
        return wrapper_log
    return wrap


def axis_crossing(df, col_name):
    """
    Detect sign changing along the columns in PandasDataframe. If more than one detected,
    drop the first row.
    :param df: df
    :param col_name: column's name
    :return: Int with corresponding row id
    """
    df = df[col_name].loc[np.sign(df[col_name]).diff().ne(0)]
    if df.index[0] == 0:  # .diff() always detects the first row as True. Drop that result
        df.drop(df.index[0], inplace=True)
    if len(df.index) == 0:  # If no sign-changes was found return None
        return None
    return df.index[0]
