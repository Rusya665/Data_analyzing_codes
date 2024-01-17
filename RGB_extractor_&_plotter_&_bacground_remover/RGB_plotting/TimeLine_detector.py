import os
import pandas as pd
from tkinter import messagebox
from fuzzywuzzy import fuzz


class TimeLineProcessor:
    def __init__(self, folder_path, hardcore_timeline=None):
        """
        Initialize a TimeLineProcessor instance.

        :param folder_path: The path of the folder to check.
        """
        self.folder_path = folder_path
        self.hardcore_timeline = hardcore_timeline

    def find_timeline_file(self):
        """
        Search for the file with 'Timeline' in its name within the folder
        """
        if self.hardcore_timeline is not None:
            return os.path.join(self.folder_path, self.hardcore_timeline)
        highest_score = 0
        timeline_file = None

        for filename in os.listdir(self.folder_path):
            score = fuzz.partial_ratio("Timeline", filename)
            if score > highest_score:
                highest_score = score
                timeline_file = filename

        if timeline_file:
            return os.path.join(self.folder_path, timeline_file)
        else:
            messagebox.showerror('Error', 'No Timeline file found')
            return None

    def check_the_path(self):
        """
        Check the file extension and read data accordingly.
        """
        file_path = self.find_timeline_file()
        if not file_path:
            return None

        file_extension = os.path.splitext(file_path)[1].lower()

        try:
            if file_extension == '.txt':
                df = pd.read_csv(file_path, delimiter='\t')  # Assuming tab-delimited txt file
            elif file_extension == '.json':
                df = pd.read_json(file_path)
            elif file_extension == '.csv':
                df = pd.read_csv(file_path)
            elif file_extension == '.xlsx':
                df = pd.read_excel(file_path, header=None, na_values=["NA"])
            else:
                messagebox.showerror('Error', 'Unknown file type')
                return None

            if df.shape[1] != 1:
                messagebox.showerror("Error", "The DataFrame must have only one column.")
                return None
            return df

        except Exception as e:
            messagebox.showerror('Error', str(e))
            return None
