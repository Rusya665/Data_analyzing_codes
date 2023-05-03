# Experimental script
import os
from Lightroom_naming_changing import path, log_file_folder
import pandas as pd
from pathlib import Path

Undo_for_folder = '2022-02-15'
log_file = None  # Specify manually or try the auto-detection (keep None here)


def _log_detection():
    """
    Auto-detects the latest log file and returns its path. If the log_file is manually specified, returns that path.
    :return: log file path
    """
    if log_file:
        return log_file
    else:
        log_list = []
        auto_detected_path = log_file_folder(path)
        logs = os.listdir(auto_detected_path)
        for some_log in logs:
            if Undo_for_folder and 'Log for' in some_log:
                log_flag = ''
                if '/Logs/' not in auto_detected_path:
                    log_flag = 'Logs/'
                log_list.append(auto_detected_path + log_flag + some_log)
        if len(log_list) > 1:
            latest_file = max(log_list, key=os.path.getctime)
        else:
            latest_file = log_list[0]
        return latest_file


def _row_in_log(file):
    """
    Reads the log file and returns the row number of the first row containing the renamed images data
    :param file: path to the log file
    :return: row number (int)
    """
    if Path(file).is_file():
        with open(file, 'r') as f:
            for row, line in enumerate(f):
                if line.startswith('Initial images were renamed to'):
                    return row + 1
    else:
        raise ValueError(f'This log file does not exist: {file} ')


def main():
    """
    Main function to undo Lightroom-naming changes
    """
    log = _log_detection()
    skip_rows = int(_row_in_log(log))
    df = pd.read_csv(log, sep=r'\t', header=None, engine='python', skiprows=skip_rows)
    try:
        max_row = df.loc[df[0].str.startswith("Images being untouched:"), 0].index[0]
    except IndexError:
        max_row = len(df)
    for img in range(max_row):
        old_name = df.iloc[img, 0].split(' ')[-1]
        new_name = df.iloc[img, 1]
        os.rename(os.path.join(path + Undo_for_folder + '/' + new_name),
                  os.path.join(path + Undo_for_folder + '/' + old_name))
        print(f'In folder {Undo_for_folder} the file {new_name} was renamed to {old_name}')


if __name__ == '__main__':
    main()
