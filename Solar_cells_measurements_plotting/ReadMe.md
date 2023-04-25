# IV Data Processing and Analysis

This folder contains codes to read, process, and analyze IV data from potentiostats. The data processing pipeline can handle multiple file formats and encodings, and it provides useful information about the input data, such as axis crossing points.

## Table of Contents
- [Usage](#usage)
- [Modules](#modules)
- [Contributing](#contributing)
- [License](#license)

## Usage

1. Make sure you have the necessary Python packages installed, such as pandas and NumPy.
2. Place your raw data files in a directory.
3. Run the main script using the following command, specifying the path to your data directory: 
python main.py --path /path/to/your/data-directory
4. The program will read and process the data, providing useful information and storing the results in a structured format.

## Modules

- `main.py`: The main entry point of the program, providing a user-friendly interface to interact with the data processing pipeline.
- `instruments.py`: Contains utility functions and classes for working with instrument data, such as data filtering, interpolation, and axis crossing detection.
- `read_iv.py`: Contains the `ReadData` class, which reads and parses raw data from different potentiostats, and gathers metadata for logging purposes.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT License](https://choosealicense.com/licenses/mit/)
