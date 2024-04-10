import os

import json
from Instruments import get_newest_file_global
from Custom_errors import JVjsonIsMissing


class UpdateSettings:
    def __init__(self, highest_path, settings):
        self.settings = settings
        self.highest_path = highest_path

    def update_settings_based_on_path(self):
        iv_to_color_map = None
        self.settings['ChartsCreator']['major_unit'] = self.settings['ChartsCreator']['max_time'] // 4
        self.settings['ChartsCreator']['minor_unit'] = self.settings['ChartsCreator']['major_unit'] / 2

        if 'IEDT' in self.highest_path:
            self.settings['color_temperature'] = 3350
            self.settings['LAB_delta_flag'] = 1
            self.settings['Table_tab'] = 'Yes'
            self.settings['samples_number'] = 2
            self.settings['ChartsCreator']['max_time'] = 100
            self.settings['ChartsCreator']['major_unit'] = self.settings['ChartsCreator']['max_time'] // 4
            self.settings['ChartsCreator']['minor_unit'] = self.settings['ChartsCreator']['major_unit'] / 2
            self.settings['ChartsCreator']['LAB_delta']['y_min'] = -4
            self.settings['ChartsCreator']['LAB_delta']['y_max'] = 10

        if 'CNC' in self.highest_path:
            self.settings['ChartsCreator']['max_time'] = 1000
            # self.settings['ChartsCreator']['major_unit'] = self.settings['ChartsCreator']['max_time'] // 4
            # self.settings['ChartsCreator']['minor_unit'] = self.settings['ChartsCreator']['major_unit'] / 2
            self.settings['ChartsCreator']['rgb_plot']['y_min'] = 130
            self.settings['ChartsCreator']['rgb_plot']['y_max'] = 240
            self.settings['samples_number'] = 6

        if 'CNC-CNF' in self.highest_path:
            self.settings['samples_number'] = 4
            self.settings['ChartsCreator']['rgb_plot']['y_min'] = 140
            self.settings['ChartsCreator']['rgb_plot']['y_max'] = 240
            self.settings['LAB_delta_flag'] = 1
            self.settings['color_temperature'] = 3400
            self.settings['Specific Timeline'] = {
                '1': 'Timeline.xlsx',
                '2': 'Timeline.xlsx',
                '3': 'Timeline.xlsx',
                '4': 'Timeline.xlsx',
                '5': 'Timeline.xlsx',
                '6': 'Timeline.xlsx',
                '7': 'Timeline.xlsx',
                '8': 'Timeline.xlsx',
                '9': 'Timeline1.xlsx',
                '10': 'Timeline1.xlsx',
                '11': 'Timeline1.xlsx',
                '12': 'Timeline1.xlsx',
            }

        if 'Perovskite' in self.highest_path:
            self.settings['ChartsCreator']['max_time'] = 340
            self.settings['ChartsCreator']['major_unit'] = self.settings['ChartsCreator']['max_time'] // 4
            self.settings['ChartsCreator']['minor_unit'] = self.settings['ChartsCreator']['major_unit'] / 2
            self.settings['samples_number'] = 12
            self.settings['LAB_delta_flag'] = 1
            self.settings['color_temperature'] = 3400

        if 'dark storage' in self.highest_path:
            self.settings['ChartsCreator']['LAB_delta']['y_max'] = 10
            self.settings['ChartsCreator']['max_time'] = 2500
            self.settings['ChartsCreator']['major_unit'] = self.settings['ChartsCreator']['max_time'] // 4
            self.settings['ChartsCreator']['minor_unit'] = self.settings['ChartsCreator']['major_unit'] / 2
            self.settings['prediction_flag'] = 0
            self.settings['iv_json'] = True
            self.settings['Table_tab'] = 'Yes'
            self.settings['samples_number'] = 6
            self.settings['color_temperature'] = 3400
            self.settings['LAB_delta_flag'] = 1
            self.settings['ChartsCreator']['rgb_plot']['y_min'] = 30
            self.settings['ChartsCreator']['rgb_plot']['y_max'] = 60
            self.settings['ChartsCreator']['LAB_delta']['y_min'] = -3
            self.settings['ChartsCreator']['LAB_delta']['y_max'] = 6
            iv_to_color_map = {
                'R1_0': 'scanCVivsE-R1',
                'R2_0': 'scanCVivsE-R2',
                'R3_0': 'scanCVivsE-R3',
                'R4_0': 'scanCVivsE-R4',
                'R5_0': 'scanCVivsE-R5',
                'R7_0': 'scanCVivsE-R7',
                'R8_0': 'scanCVivsE-R8',
                'R11_0': 'scanCVivsE-R11',
                               }

        if self.settings['iv_json']:
            json_iv = get_newest_file_global(os.path.join(self.highest_path), " IV data.json")
            if json_iv is None:
                raise JVjsonIsMissing(f"\nThe given path:\n{self.highest_path}\ndoes not contain json with IV data")
            with open(json_iv, 'r') as f:
                self.settings['iv_json'] = json.load(f)
            self.settings['iv_to_color_map'] = iv_to_color_map
        return self.settings
