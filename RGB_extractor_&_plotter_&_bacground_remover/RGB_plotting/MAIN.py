from RGB_and_IV_plotter import RGBandIVplotter
import os


if __name__ == "__main__":
    one_drive_path = os.environ.get('OneDrive')
    path = r'C:\Users\runiza_admin\OneDrive - O365 Turun yliopisto\Desktop\new_aging_blah_blah/'
    RGBandIVplotter(highest_path=path)
