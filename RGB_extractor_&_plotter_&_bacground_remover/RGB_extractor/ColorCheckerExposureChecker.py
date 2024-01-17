import colorsys
import json
import os
from datetime import datetime

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
from tqdm import tqdm


class ColorCheckerExposureAdjuster:
    def __init__(self, folder_path: str, default_iso: int = None):
        self.folder_path = folder_path
        self.default_iso = default_iso
        self.color_values = {}
        self.colorChecker_data = {
            'ISO 200': {
                'R': {'R': 150, 'G': 40, 'B': 50, 'Target': 130},
                'G': {'R': 30, 'G': 130, 'B': 60, 'Target': 130},
                'B': {'R': 0, 'G': 35, 'B': 130, 'Target': 130},
                'exposure_change_step': 0.01,  # Check this value
                'color_change_per_exposure': 0.6,  # Check this value
            },
            'ISO 400': {
                'R': {'R': 210, 'G': 90, 'B': 100, 'Target': 200},
                'G': {'R': 140, 'G': 200, 'B': 120, 'Target': 200},
                'B': {'R': 0, 'G': 50, 'B': 200, 'Target': 200},
                'exposure_change_step': 0.01,
                'color_change_per_exposure': 0.6,
            }
        }

        self.min_area_threshold = 15000
        self.threshold = 30

    @staticmethod
    def rgb_to_hsv(r, g, b):
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        return h * 360, s * 100, v * 100

    def find_color_boxes(self, image: np.ndarray, channel: str, iso: str) -> list:
        r, g, b = self.colorChecker_data[iso][channel]['R'], self.colorChecker_data[iso][channel]['G'], \
            self.colorChecker_data[iso][channel]['B']
        lower_bound = np.array([b - self.threshold, g - self.threshold, r - self.threshold])
        upper_bound = np.array([b + self.threshold, g + self.threshold, r + self.threshold])
        mask = cv2.inRange(image, lower_bound, upper_bound)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return []

        filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > self.min_area_threshold]

        return [(cv2.boundingRect(cnt), cv2.contourArea(cnt)) for cnt in filtered_contours]

    def process_images(self):
        save_folder_path = os.path.join(self.folder_path, 'Adjusted')
        os.makedirs(save_folder_path, exist_ok=True)
        color_map = {'R': (0, 0, 255, 2), 'G': (0, 255, 0, 1), 'B': (255, 0, 0, 0)}
        # image_files = [f for f in os.listdir(self.folder_path) if f.endswith(".jpg")]
        image_files = sorted([f for f in os.listdir(self.folder_path) if f.endswith(".jpg")],
                             key=lambda x: int(''.join(filter(str.isdigit, x.split('.')[0]))))
        user_channel_choice = input("Which channel would you like to print? (R/G/B): ").upper()
        result_data = {}  # Data to be saved in JSON
        for image_counter, filename in enumerate(tqdm(image_files, desc='Processing images', unit='img'), 1):
            # Initialize a list for each image to store rectangles
            result_data[image_counter] = {"filename": filename, "rectangles": [], "ISO": ""}
            file_path = os.path.join(self.folder_path, filename)

            if self.default_iso:
                iso = f'ISO {self.default_iso}'
            else:
                with Image.open(file_path) as img:
                    exif_data = img._getexif()
                    iso = None
                    for tag, value in exif_data.items():
                        tag_name = TAGS.get(tag, tag)
                        if tag_name == 'ISOSpeedRatings':
                            iso = f'ISO {value}'
                            break
            result_data[image_counter]['ISO'] = iso
            self.color_values[filename] = {}
            img = cv2.imread(file_path)
            # Dynamic scaling factors based on image dimensions
            height, width, _ = img.shape
            scale_factor = min(height, width) / 2000

            # Apply scaling factors to rectangle thickness and font size
            rectangle_thickness = max(2, int(8 * scale_factor))
            font_size = max(0.5, 1.8 * scale_factor)
            font_thickness = max(1, int(6 * scale_factor))

            for channel, (b, g, r, num) in color_map.items():
                color = (b, g, r)
                for rect_counter, ((x, y, w, h), _) in enumerate(self.find_color_boxes(img, channel, iso), 1):
                    initial_avg_color = np.mean(img[y:y + h, x:x + w, num])
                    self.color_values[filename][channel] = initial_avg_color
                    cv2.rectangle(img, (x, y), (x + w, y + h), color, rectangle_thickness)
                    target_value = self.colorChecker_data[iso][channel]['Target']
                    required_exposure_change = self.colorChecker_data[iso]['exposure_change_step'] * (
                            target_value - initial_avg_color) / self.colorChecker_data[iso]['color_change_per_exposure']
                    text = (f"{channel}: Avg: {initial_avg_color:.2f}, Target: {target_value},"
                            f" Coef: {required_exposure_change:.4f}")
                    cv2.putText(img, text, (x, y - 150 * num), cv2.FONT_HERSHEY_SIMPLEX,
                                font_size, color, font_thickness)
                    rect_data = {
                        "rectangle_counter": rect_counter,
                        "coordinates": (x, y, w, h),
                        "rectangle_color_type": channel,
                        "avg_color": initial_avg_color,
                        "target_value": target_value,
                        "suggested_coefficient": required_exposure_change
                    }
                    result_data[image_counter]['rectangles'].append(rect_data)
            save_path = os.path.join(save_folder_path, f"{image_counter}_Adjusted_{filename}")
            cv2.imwrite(save_path, img)

        current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        folder_name = os.path.basename(self.folder_path)
        json_filename = f"{current_time}_{folder_name}.json"
        # Add the following code snippet at the end of the `process_images()` method:
        print(f"Image Counter | Filename       | Average Coefficient | {user_channel_choice} Coefficient")
        print("--------------------------------------------------------------------")
        for image_counter, data in result_data.items():
            coef_sum = 0
            coef_count = 0
            chosen_coef = 'N/A'

            for rect in data['rectangles']:
                coef = rect['suggested_coefficient']
                channel = rect['rectangle_color_type']

                if coef is not None:
                    coef_sum += coef
                    coef_count += 1

                    if channel == user_channel_choice:
                        chosen_coef = round(coef, 2)

            if coef_count > 0:
                avg_coef = round(coef_sum / coef_count, 2)
            else:
                avg_coef = 'N/A'

            print(f"{image_counter:13} | {data['filename']:15} | {avg_coef:8} | {chosen_coef:8}")

        with open(os.path.join(self.folder_path, json_filename), 'w') as json_file:
            json.dump(result_data, json_file, indent=4)

    def plot_values(self):
        channel_colors = {'R': 'red', 'G': 'green', 'B': 'blue'}

        for channel, color in channel_colors.items():
            x, y = [], []
            for idx, (filename, values) in enumerate(self.color_values.items(), 1):
                x.append(idx)
                y.append(values.get(channel, None))
            plt.plot(x, y, label=channel, color=color, marker='o')

        plt.xlim(left=1, right=len(x))  # Set x-axis limits
        plt.xlabel('Image Count')
        plt.ylabel('Average Color Value')
        plt.legend()

        today = datetime.now().strftime('%Y-%m-%d')
        folder_name = os.path.basename(self.folder_path)
        save_path = os.path.join(self.folder_path, f"{today}_{folder_name}.png")

        plt.savefig(save_path, dpi=300)
        plt.show()


path = "path/to/your/folder"
A = ColorCheckerExposureAdjuster(path)
A.process_images()
A.plot_values()
