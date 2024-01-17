import json
import os
import re

import pandas as pd
from natsort import natsorted

from Instruments import get_newest_file, get_newest_file_global
from TimeLine_detector import TimeLineProcessor


class RGBAndIVDataGatherer:
    def __init__(self, highest_path, settings):
        self.highest_path = highest_path
        self.settings = settings
        self.data = {}
        if self.settings['iv_to_color_map'] is not None:
            self.iv_key_iterator = self.generate_iv_key_iterator()
        self.data_gathering()
        self.sort_data()

    def data_generate(self) -> dict:
        """
        Return generated dict
        :return: Dictionary with data
        """
        return self.data

    def sort_data(self):
        """
        Sorts the data dictionary based on different conditions present in self.highest_path.
        The keys of the dictionary are rearranged based on the sorting rules defined for each condition.
        :return: None
        """
        try:
            # Add your sorter here
            ...
        except Exception as e:
            print(f"An error occurred while sorting the data: {e}")

    @staticmethod
    def extract_numeric_value(s):
        match = re.search(r'Results_(\d) (\w+) (\d+)_', s)
        if match:
            category = match.group(1) + " " + match.group(2)
            numeric_value = int(match.group(3))
            return category, numeric_value
        else:
            return "", 0

    def data_gathering(self):
        """
        Generate a dictionary containing RGB data. Use data from the newest "Total_RGB.json" file
        within the highest_path directory if available, otherwise gather data from individual directories.

        :return: None
        """
        newest_total_rgb_file = get_newest_file_global(self.highest_path, "Total_RGB.json")

        if newest_total_rgb_file:
            with open(newest_total_rgb_file, 'r') as f:
                total_rgb_data = json.load(f)

            for dir_name, dir_data in total_rgb_data.items():
                self.data[dir_name] = {"RGB_data": {}}
                if self.settings['iv_to_color_map'] is not None:
                    self.add_iv_data(dir_name)
                specific_timeline = self.settings['Specific Timeline'].get(dir_name)
                self.data[dir_name]['Timeline'] = TimeLineProcessor(self.highest_path,
                                                                    specific_timeline).check_the_path()

                self.data[dir_name]['RGB_data'] = dir_data

        else:
            for dir_path, dir_names, _ in os.walk(self.highest_path):
                for dir_name in dir_names:
                    rgb_path = os.path.join(dir_path, dir_name, "RGB_analyzing")
                    if os.path.exists(rgb_path):
                        self.data[dir_name] = {"RGB_data": {}}
                        if self.settings['iv_to_color_map'] is not None:
                            self.add_iv_data(dir_name)
                        specific_timeline = self.settings['Specific Timeline'].get(dir_name)
                        self.data[dir_name]['Timeline'] = TimeLineProcessor(self.highest_path,
                                                                            specific_timeline).check_the_path()
                        # newest_file = get_newest_file(rgb_path)
                        # if newest_file:
                        #     self.rgb_reading(newest_file, rgb_path, dir_name)
                        # Find the newest file for each extension and prefer JSON over XLSX
                        newest_file = get_newest_file(rgb_path, '.json') or get_newest_file(rgb_path, '.xlsx')
                        if newest_file:
                            extension = os.path.splitext(newest_file)[1]
                            self.rgb_reading(newest_file, rgb_path, dir_name)

    def rgb_reading(self, current_file, path_to, dir_name):
        final_path = os.path.join(path_to, current_file)
        extension = os.path.splitext(current_file)[1]

        if extension == '.xlsx':
            df_rgb = pd.read_excel(final_path, header=None, na_values=["NA"], index_col=None)
            df_rgb = df_rgb.drop(df_rgb.columns[0], axis=1)  # Drop the first "order" column
            for row_num, row in df_rgb.iterrows():
                self.data[dir_name]["RGB_data"][str(row_num)] = {}
                area_count = 1
                for i in range(1, 12, 4):
                    self.data[dir_name]["RGB_data"][str(row_num)][f"Area {area_count}"] = {
                        "RGB": {
                            "R": row[i],
                            "G": row[i + 1],
                            "B": row[i + 2]
                        }
                    }
                    area_count += 1

        elif extension == '.json':
            with open(final_path, 'r') as f:
                json_data = json.load(f)
            for pic_number, areas in json_data.items():
                self.data[dir_name]["RGB_data"][str(pic_number)] = {}
                for area, values in areas.items():
                    self.data[dir_name]["RGB_data"][str(pic_number)][area] = {"RGB": {}}
                    self.data[dir_name]["RGB_data"][str(pic_number)][area]["RGB"] = values["RGB"]

    def add_iv_data(self, dir_name):
        iv_map = self.settings['iv_to_color_map']
        is_dict = isinstance(iv_map, dict)
        iv_data_dict = {}

        mapped_name = None
        if is_dict:
            mapped_name = iv_map.get(dir_name)

        else:
            try:
                mapped_name = next(self.iv_key_iterator)
            except StopIteration:
                print(f"No more unused IV data keys for {dir_name}")
                mapped_name = None
        if mapped_name is None:
            return
        # Loop through the folder names (dates) in iv_json
        for folder_name, devices_data in self.settings['iv_json'].items():
            # Get the IV data for the device based on the mapped_name
            device_data = devices_data.get(mapped_name)

            if device_data is not None:
                # The key here is an integer starting from 0, incrementing for each folder_name
                next_key = len(iv_data_dict)
                iv_data_dict[next_key] = device_data

        # Add iv_data_dict to self.data under the key ['iv_data']
        self.data[dir_name]['iv_data'] = iv_data_dict

    def generate_iv_key_iterator(self):
        """
        Generate an iterator for the IV data keys in self.settings['iv_json'].
        :return: Iterator for the IV data keys.
        """
        first_folder = next(iter(self.settings['iv_json']))
        return iter(self.settings['iv_json'][first_folder])
