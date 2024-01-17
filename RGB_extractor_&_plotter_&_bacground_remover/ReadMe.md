# RGB channels extraction and images background erasing

This folder contains codes to work with images and IV data of solar cells.

| File name              | Description                                                                                                                                                             |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Delete_bg_make_movie` | Processes all images in a given folder and deletes background using `rembg` package. Also, tries to make a video. Use for degradation analysis of photovoltaic devices. |
| `RGB_plotting`         | Plots the RGB values obtained by `RGB_select_areas.py` in Microsoft Excel.                                                                                              |
| `RGB_extractor `       | Allows the user to draw up to 10 rectangular areas for subsequent extraction of RGB values and saves the drawing.                                                       |
                                                                                         |


## Table of Contents
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Usage

1. Use `Deleting&filming.py` to erase background if desired.

2. Use `Area_selecting.py` to select which pictures will be used for further analysis. If `Deleting&filming.py` apply .png extension and work with specific folders created by it.

3. `RGB_select_areas.py` will be opened after step 2 for all folders being selected.

4. Use `RGB_plotting`. Note this plotter contains tons of settings so better to play around.


## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT License](https://choosealicense.com/licenses/mit/)
