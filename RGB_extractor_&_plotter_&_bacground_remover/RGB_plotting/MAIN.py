from RGB_and_IV_plotter import RGBandIVplotter
import os


if __name__ == "__main__":
    one_drive_path = os.environ.get('OneDrive')
    path = "path/to/your/folder"
    RGBandIVplotter(highest_path=path)
