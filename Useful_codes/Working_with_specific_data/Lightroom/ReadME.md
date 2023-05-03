# Working with images

This folder contains Python scripts for changing the names of raw image files in a specific format. The main rule for the file names is that each raw image file name is supposed to be in the format 'yyyy-mm-dd(-n)_name.arw', where:

1. yyyy-mm-dd has to correspond to the folder name, i.e., the folder name (date) must be the same as the picture DateTime from the EXIF. If not, a warning message will appear.
2. (-n) is the specific format which appears only if the folder already contains some properly named files, in other words, preventing name overlapping and allowing multiple photo-sessions per day for the same samples.

Also, the `Lightroom_smart_collections_creator.py` can help with auto-creation of the smart collections for the Adobe LightroomClassic. 
## Table of Contents
- [Working with images](#working-with-images)
  - [Table of Contents](#table-of-contents)
  - [Usage](#usage)
    - [Requirements](#requirements)
    - [Changing File Names](#changing-file-names)
    - [Undoing File Name Changes](#undoing-file-name-changes)
    - [Smart collections creator](#smart-collection-creator)
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

### Smart collection creator

TO use the `Lightroom_smart_collections_creator.py` script for creating smart collections, follow these steps:


  1. Set the `output_path` variable to the desired folder path where the Smart Collection files will be saved.
  2. Set the `collection_value` variable to the desired collection value to be used in the Smart Collection criteria.
  3. Set the `filename_values` list to the desired filename values to be used in the Smart Collection criteria.
  4. Set the `side_flag` variable to `True` if you want to create two Smart Collections for each filename value 
  (with ".0" and ".1" appended). Set it to False if you want to create only one Smart Collection for each filename
  value without appending anything.


## Contributing

Contributions to this project are welcome. If you find a bug or have a feature request, please open an issue on the GitHub repository.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
