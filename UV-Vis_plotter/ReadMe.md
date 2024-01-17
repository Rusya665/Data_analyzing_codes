
# Transmittance Plotter

This application provides a graphical user interface for visualizing and analyzing transmittance data using matplotlib.

## Features

- Open and display transmittance data from files.
- Interactive plot with zooming and panning capabilities.
- Show/hide individual data series.
- Draw horizontal and vertical lines on the plot.
- Reset view to the original scale.
- Control Panel for managing plot elements.

## Usage

Run the `InitialWindow` to start the application. Use the "Open File" button to load transmittance data from a .xlsx file. The `TransmittancePlotter` will then display the data in an interactive plot.

The `ControlPanel` provides a user interface to interact with the plot. You can show or hide individual lines, zoom to specific x or y ranges, and draw horizontal or vertical lines across the plot.

## Requirements

- Python 3.6+
- matplotlib
- pandas
- customtkinter

## Installation

Clone the repository and install the required packages using pip:

```bash
git clone https://your-repository-url.git
cd your-repository-directory
pip install -r requirements.txt
```

## Running the Application

To run the application, execute the following command:

```bash
python path/to/your_script.py
```

Replace `path/to/your_script.py` with the actual path to the script file.

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request.

