# RGB channels extraction and images background erasing

This folder contains codes to work with images and IV data of solar cells.
Deleting&filming.py <- proceeds all images in given folder and deletes background using rembg package. Also, tries to make a video. Use for degradation analysis of photovoltaic devices.
Main chart plotting (total, IV).py <- Plot the obtained by RGB_select_areas.py RGB values in Microsoft Excel.
RGB_select_areas.py <- Allow user to draw 3 rectangular area for subsequent extraction RGB values and saves the drawing.
Select_images_extract_RGB.py <- GUI based folders with images selector for further RGB_select_areas.py usage.

## Table of Contents
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Usage

1. Use Deleting&filming.py to erase background if desired.

2. Use Select_images_extract_RGB.py to select which pictures will be used for further analysis. If Deleting&filming.py apply .png extension and work with specific folders created by it.

3. RGB_select_areas.py will be opened after step 2 for all folders being selected.

4. Apply Main chart plotting (total, IV).py. Note this plotter contains tons of settings so better to play around.


## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT License](https://choosealicense.com/licenses/mit/)
