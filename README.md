# Repository: Python Scripts and Tools Collection

This repository contains various Python scripts and tools for working with raw image files, generating PowerPoint slides, plotting data from XLSX files, performing specific data analysis, training and evaluating a convolutional neural network (CNN) for detecting the corners of perovskite crystals in images, and more.

# Table of Contents
- [Repo's structure](#repos-structure)
  - [Perovskite Crystal Corner Detection](#perovskite-crystal-corner-detection)
  - [RGB Channels Extraction/Plotting and Images Background Erasing](#rgb-channels-extractionplotting-and-images-background-erasing)
  - [Multiple Useful Codes](#multiple-useful-codes)
    - [Working_with_specific_data](#working_with_specific_data)
      - [Image Renaming](#image-renaming)
      - [PowerPoint Slide Generator and XLSX Data Plotter](#powerpoint-slide-generator-and-xlsx-data-plotter)
  - [UV-Vis_plotter](#tools-for-specific-data-analysis)
- [Contributing](#contributing)
- [License](#license)

## Repo's structure
```
|-- AI_perovskite_detector
|   +-- Data_set_manual_creation.py
|   +-- ReadME.md
|   +-- Train_model.py
|-- RGB_extractor_&_plotter_&_bacground_remover
|   |-- Delete_bg_make_movie
|   |   +-- Deleting&filming.py
|   |-- RGB_extractor
|   |   +-- Area_selecting.py
|   |   +-- ColorCheckerExposureChecker.py
|   |   +-- Exposure_plotting_and_fitting.py
|   |   +-- RGB_select_areas.py
|   |-- RGB_plotting
|   |   +-- Charts_creator.py
|   |   +-- Color_spaces_convertion.py
|   |   +-- Custom_errors.py
|   |   +-- IV_data_plots_creator.py
|   |   +-- IV_prediction.py
|   |   +-- MAIN.py
|   |   +-- RGB_and_IV_gatherer.py
|   |   +-- RGB_and_IV_plotter.py
|   |   +-- RGB_settings.py
|   |   +-- RGB_settings_update.py
|   |   +-- TimeLine_detector.py
|   +-- ReadMe.md
|-- UV-Vis_plotter
|   +-- UV-Vis_plotter.py
|-- Useful_codes
|   |-- Working_with_specific_data
|   |   |-- IV_data_manipulation_SC
|   |   |   +-- PlottingIVdata.py
|   |   |   +-- PowerPoint_pictures_adding.py
|   |   |   +-- ReadMe.md
|   |   |-- Lightroom
|   |   |   +-- Lightroom_naming_changing.py
|   |   |   +-- Lightroom_naming_changing_undo.py
|   |   |   +-- Lightroom_smart_collections_creator.py
|   |   |   +-- ReadME.md
|   |   +-- ReadMe.md
|   |   +-- dta_simple_plot+converge.py
|   |   +-- plot_FHI-aims.py
|   +-- DAT_reading.py
|   +-- QR_generator.py
|   +-- ReadMe.md
|   +-- Text_compare_to_a_list.py
+-- Instruments.py
+-- LICENSE
+-- README.md
```


## Perovskite Crystal Corner Detection

This folder contains codes to train and evaluate a convolutional neural network (CNN) for detecting the corners of perovskite crystals in images. Perovskite materials are used in solar cells, and their unique crystal structure allows them to efficiently absorb sunlight and convert it into electricity. Analyzing the crystal structure is important for understanding the performance of the solar cells.

For usage, see the [Perovskite Crystal Corner Detection README.md](AI_perovskite_detector/ReadME.md).


## RGB Channels Extraction/Plotting and Images Background Erasing

This folder contains codes to work with images and IV data of solar cells. The folder includes scripts for deleting image backgrounds, extracting RGB values, and plotting charts.

For usage, see the [RGB Channels Extraction/Plotting and Images Background Erasing README.md](RGB_extractor_&_plotter_&_bacground_remover/ReadMe.md).

## Multiple Useful Codes

This folder contains a variety of useful codes for data analysis and other tasks. Scripts include a QR code generator, a text comparison tool, a .dat file converter, and a folder containing codes for working with specific data.

For usage, see the [Multiple Useful Codes README.md](Useful_codes/ReadMe.md).

### Working_with_specific_data
This folder contains various Python scripts designed for specific data analysis tasks. These tools are tailored to process and analyze certain types of data or perform specific operations, such as file conversion, data extraction, and manipulation.
For usage, see the [ Tools for Specific Data Analysis README.md](Useful_codes/Working_with_specific_data/ReadMe.md).

####  Image Renaming

This folder contains two Python scripts for changing the names of raw image files in a specific format. The main rule for the file names is that each raw image file name is supposed to contain a certain string pattern. The script can be used to rename the files according to the user's needs.

For usage, see the [Image Renaming README.md](Useful_codes/Working_with_specific_data/Lightroom/ReadME.md).

#### PowerPoint Slide Generator and XLSX Data Plotter

This folder contains Python scripts for generating PowerPoint slides and plotting data from XLSX files. The slide generator allows users to create presentation slides based on a specific template and populated with data from various sources, such as images and text. The XLSX data plotter reads data from XLSX files and plots the data using a variety of chart types.

For usage, see the [PowerPoint Slide Generator and XLSX Data Plotter README.md](Useful_codes/Working_with_specific_data/IV_data_manipulation_SC/ReadMe.md).

## UV-Vis plotter
This folder contains a script for the fast UV-Vis data plotting.

For usage, see the [UV-Vis plotter README.md](UV-Vis_plotter/ReadMe.md).

## Contributing
If you have any suggestions, improvements, or issues, please feel free to create an issue or submit a pull request. We appreciate your contributions and feedback.

## License
This repository is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).
