# Image renaming

This folder contains two Python scripts for changing the names of raw image files in a specific format. The main rule for the file names is that each raw image file name is supposed to be in the format 'yyyy-mm-dd(-n)_name.arw', where:

1. yyyy-mm-dd has to correspond to the folder name, i.e., the folder name (date) must be the same as the picture DateTime from the EXIF. If not, a warning message will appear.
2. (-n) is the specific format which appears only if the folder already contains some properly named files, in other words, preventing name overlapping and allowing multiple photo-sessions per day for the same samples.

## Table of Contents
- [File Name Changing Script](#file-name-changing-script)
  - [Table of Contents](#table-of-contents)
  - [Usage](#usage)
    - [Requirements](#requirements)
    - [Changing File Names](#changing-file-names)
    - [Undoing File Name Changes](#undoing-file-name-changes)
  - [Contributing](#contributing)
  - [License](#license)

## Usage

### Requirements

Before running the scripts, make sure to install the required Python packages:

- exifread
- pandas

### Changing File Names

To use the `Lightroom_naming_changing.py` script for changing file names, follow these steps:

1. Open the script in your Python environment (e.g., PyCharm, Jupyter Notebook).
2. Edit the `path_given` variable to the path to your folder with folders with raw images.
3. Run the script.
4. The script will go through each folder and rename the raw image files according to the specified format.

### Undoing File Name Changes

To use the `Undo_file_renaming.py` script for undoing file name changes, follow these steps:

1. Open the script in your Python environment (e.g., PyCharm, Jupyter Notebook).
2. Edit the `Undo_for_folder` variable to the folder name for which you want to undo the file name changes.
3. Run the script.
4. The script will go through the log file for the specified folder and undo the file name changes.

## Contributing

Contributions to this project are welcome. If you find a bug or have a feature request, please open an issue on the GitHub repository.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
