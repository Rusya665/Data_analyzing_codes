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

        if self.settings['iv_json']:
            json_iv = get_newest_file_global(os.path.join(self.highest_path), " IV data.json")
            if json_iv is None:
                raise JVjsonIsMissing(f"\nThe given path:\n{self.highest_path}\ndoes not contain json with IV data")
            with open(json_iv, 'r') as f:
                self.settings['iv_json'] = json.load(f)
            self.settings['iv_to_color_map'] = iv_to_color_map
        return self.settings
