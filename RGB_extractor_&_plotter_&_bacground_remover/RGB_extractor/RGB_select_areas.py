import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
import numpy as np
from PIL import ImageDraw, ImageTk, ImageFont
from tqdm import tqdm

from Instruments import create_folder, get_newest_file, recursive_default_dict


class RGBExtractingCanvas(ctk.CTkFrame):
    width = 1200
    height = 1200

    def __init__(self, parent, folder, data, zoom, extension, current_folder, data_len, start_from=0,
                 *args, **kwargs):
        super().__init__(master=parent, *args, **kwargs)
        self.zoom_index = zoom
        self.auto_applying_flag = False
        self.folder_suffix = folder
        self.extension = extension
        self.parent = parent
        self.raw_data = data
        self.counter = start_from if start_from < len(self.raw_data) else 0
        self.top_x, self.top_y, self.bot_x, self.bot_y = 0, 0, 0, 0
        self.outline = defaultdict(dict)
        self.rectangle_width = 15
        self.text_size = 20
        self.text_offset_x = 15
        self.text_offset_y = 15
        self.pil_font = ImageFont.truetype("arial.ttf", self.text_size)
        self.tk_font = ("Arial", self.text_size)
        self.parent_path = str(Path(self.raw_data[0]['Name']).parents[0]) + '/'
        self.data_dict = recursive_default_dict()
        self.rgb_folder = self.make_folder()
        self.outer_prefix = self.prefix()

        # Window
        self.parent.title(
            f'{current_folder} in total {data_len}. Select areas in picture {self.counter + 1} of {len(self.raw_data)}'
            f' of the {self.raw_data[self.counter]["Name"]}')
        self.parent.geometry(f"{self.width}x{self.height}")
        self.parent.resizable(True, True)
        self.parent.configure(background='grey')

        self.img_resized = self.raw_data[self.counter]['Image']
        self.pack(fill=ctk.BOTH, expand=True)
        # Canvas
        self.canvas = ctk.CTkCanvas(master=self, width=self.img_resized.width(), height=self.img_resized.height(),
                                    borderwidth=0, highlightthickness=0)
        self.canvas.pack(expand=True)
        self.canvas.img = self.img_resized
        self.canvas.create_image(0, 0, image=self.img_resized, anchor='nw', tag='image')
        self.rectangle = self.canvas.create_rectangle(self.top_x, self.top_y, self.bot_x, self.bot_y,
                                                      fill='', outline='white', width=5, tags='rectangle')
        self.canvas.bind('<Button-1>', lambda event: self.get_mouse_position(event))
        self.canvas.bind('<B1-Motion>', lambda event: self.update_sel_rect(event))
        self.canvas.bind_all("<KeyPress>", self.main_method)
        self.canvas.update()
        self.mainloop()

    def make_folder(self):
        if self.parent_path.endswith('Processed/'):
            self.parent_path = self.parent_path.split('Processed/')[0]
        return create_folder(self.parent_path, "RGB_analyzing")

    def prefix(self):
        png_list = []
        for png in os.listdir(self.rgb_folder):
            if png.endswith('.png'):
                png_list.append(png)
        if len(png_list) >= len(self.raw_data):
            prefix0 = png_list[-1].split('-')[0]
            return str(int(prefix0) + 1)
        if len(png_list) < len(self.raw_data):
            return str('1')

    def get_mouse_position(self, event):
        """
        Get the mouse position
        :param event: mouse left-click event
        :return: None
        """
        self.top_x, self.top_y = event.x, event.y

    def update_sel_rect(self, event):
        """
        Draw rectangle based on new coordinates.
        :param event: Mouse left bottom is clicked and mouse is moving
        :return: None
        """
        self.bot_x, self.bot_y = event.x, event.y
        self.canvas.coords(self.rectangle, self.top_x, self.top_y, self.bot_x, self.bot_y)

    def get_rgb_pil(self, counter=None):
        """
        Extracting the RGB values from pure non-resized image over a given rectangular area. Pillow version.
        This has to be faster than cv2.
        :param counter: If passed changes the 'self.counter'
        :return: R, G, and B average values
        """
        if counter is None:
            counter = self.counter
        pixels_list = []
        img = self.raw_data[counter]['Image_original']
        for x in range(self.top_x * self.zoom_index, self.bot_x * self.zoom_index + 1):
            for y in range(self.top_y * self.zoom_index, self.bot_y * self.zoom_index + 1):
                h = img.getpixel((x, y))
                pixels_list.append(h)
        r, g, b = np.mean(pixels_list, axis=0)
        return [r, g, b]

    @staticmethod
    def get_outline_box_color(average_rgb):
        """
        Return the average color of a given RGB value
        :param average_rgb: initial RGB value
        :return: 'white' or 'black' and corresponding chanel values
        """
        if np.average(average_rgb) <= 123:
            return 'white', (255, 255, 255)
        else:
            return 'black', (0, 0, 0)

    def write_rgb_json(self):
        """
        Generate output json file with timepoints, RGB values and corresponding coordinates
        :return: None
        """
        today = f'{datetime.now():%Y-%m-%d %H.%M.%S%z}'
        resulting_json = self.rgb_folder + today + ' Results_' + self.folder_suffix + ".json"
        with open(resulting_json, 'w', encoding='utf-8') as f:
            json.dump(self.data_dict, f, ensure_ascii=False, indent=4)

    def main_method(self, event):
        """
        The main method. Depends on which key was pressed, calls corresponding methods.

        Key and Description:

        - Numbers from 0 to 9: Save drawn rectangle and extract average RGB values.
        - 'p': Emergency stop button, close windows and stop script.
        - 'f': Move to the next picture if exist and save all data to dict.
          If no more images, save all data to a file and properly finish the program.
        - 'b': move backward.
        - 'a': Apply obtained for the current picture coordinates for all remaining pictures (auto-applying).

        :param event: The event key pressed.
        :return: None
        """
        if event.char in map(str, range(0, 10)):
            area_number = int(event.char)
            self.canvas.delete(f'Area_{area_number}')
            self.canvas.delete(f'Area_{area_number}_text')
            avr_rgb = self.get_rgb_pil()
            self.data_dict[self.counter][f'Area {area_number}'] |= \
                {'RGB': {'R': avr_rgb[0], 'G': avr_rgb[1], 'B': avr_rgb[2]}}
            self.data_dict[self.counter][f'Area {area_number}'] |= \
                {'Coordinates': {'1top_x': self.top_x, '2top_y': self.top_y, '3bot_x': self.bot_x,
                                 '4bot_y': self.bot_y}}
            outline_color = self.get_outline_box_color(avr_rgb)[0]
            self.outline[self.counter][f'Area {area_number}'] = outline_color
            self.canvas.create_rectangle(self.top_x, self.top_y, self.bot_x, self.bot_y, fill='',
                                         outline=outline_color, width=9, tags=f'Area_{area_number}')

            # Check if the rectangle is too small
            rect_width = abs(self.bot_x - self.top_x)
            rect_height = abs(self.bot_y - self.top_y)

            # Initialize text position
            text_x = self.bot_x - self.text_offset_x
            text_y = self.top_y + self.text_offset_y

            if rect_width < 30 or rect_height < 30:
                # If the rectangle is too small, so move the text aside
                text_x = self.bot_x + 20
                text_y = self.top_y + 20

            self.canvas.create_text(text_x, text_y, font=self.tk_font,
                                    text=str(area_number), fill=outline_color, tags=f'Area_{area_number}_text')

        if event.char == 'p':
            print("Oh no, why did someone push the emergency stop butt?")
            self.parent.destroy()

        if event.char == 'a':
            dialog = ctk.CTkInputDialog(text="Do you want me to apply the same ares"
                                             " for the rest images? y-yes, n-no: ", title="Auto applying")
            if dialog.get_input().lower() == 'y':
                for widget in self.winfo_children():
                    widget.quit()
                self.pack_forget()
                self.destroy()
                self.auto_applying_flag = False
                self.auto_applying(self.counter)
                self.write_rgb_json()
            print('Auto-processed has been applied.')

        if event.char == 'f':
            self.canvas.delete('all')
            self.canvas.update()
            self.counter += 1
            self.top_x, self.top_y, self.bot_x, self.bot_y = 0, 0, 0, 0
            if self.counter < len(self.raw_data):
                self.parent.title(f"Select areas in picture {self.counter + 1} of {len(self.raw_data)} of:"
                                  f" the {self.raw_data[self.counter]['Name']}")
                self.img_resized = self.raw_data[self.counter]['Image']
                self.canvas.img = self.img_resized
                self.canvas.create_image(0, 0, image=self.img_resized, anchor='nw', tag='image')
                self.rectangle = self.canvas.create_rectangle(self.top_x, self.top_y, self.bot_x, self.bot_y,
                                                              fill='', outline='white', width=5, tags='rectangle')
                self.canvas.update()
            else:
                for widget in self.winfo_children():
                    widget.quit()
                self.pack_forget()
                self.destroy()
                self.write_rgb_json()
                print('Everything is done successfully, good job, buddy!')

        if event.char == 'b':
            if self.counter > 0:
                self.canvas.delete('all')
                self.canvas.update()
                self.counter -= 1
                self.top_x, self.top_y, self.bot_x, self.bot_y = 0, 0, 0, 0
                self.parent.title(f"Select areas in picture {self.counter + 1} of {len(self.raw_data)} of:"
                                  f" the {self.raw_data[self.counter]['Name']}")
                self.img_resized = self.raw_data[self.counter]['Image']
                self.canvas.img = self.img_resized
                self.canvas.create_image(0, 0, image=self.img_resized, anchor='nw', tag='image')
                self.rectangle = self.canvas.create_rectangle(self.top_x, self.top_y, self.bot_x, self.bot_y,
                                                              fill='', outline='white', width=5, tags='rectangle')
                self.canvas.update()
            else:
                messagebox.showinfo(title='Info', message='This is the first image.')

    def auto_applying(self, counter):
        """
        Apply the first image obtained coordinates to the remaining one
        :return: None
        """
        existing_areas = self.data_dict[counter].keys()
        for picture in range(len(self.raw_data)):
            for area in existing_areas:
                self.top_x = self.data_dict[counter][area]['Coordinates']['1top_x']
                self.top_y = self.data_dict[counter][area]['Coordinates']['2top_y']
                self.bot_x = self.data_dict[counter][area]['Coordinates']['3bot_x']
                self.bot_y = self.data_dict[counter][area]['Coordinates']['4bot_y']
                avr_rgb = self.get_rgb_pil(counter=picture)
                self.outline[picture][area] = self.get_outline_box_color(avr_rgb)[0]
                self.data_dict[picture][area] = {
                    'Coordinates': {'1top_x': self.top_x, '2top_y': self.top_y,
                                    '3bot_x': self.bot_x, '4bot_y': self.bot_y},
                    'RGB': {'R': avr_rgb[0], 'G': avr_rgb[1], 'B': avr_rgb[2]}}

    def save_image_with_areas_after(self):
        """
        Save image in lower/resized resolution AFTER the main RGB.
        Draw corresponding rectangles if they do exist.
        :return: None
        """
        latest_json_file = get_newest_file(self.rgb_folder)
        if latest_json_file is None:
            raise FileNotFoundError
        with open(latest_json_file, 'r') as json_file:
            json_data = json.load(json_file)
            total_images = len(json_data)

            for img_index in tqdm(range(total_images), desc="Working on images", position=1, leave=False,
                                  colour='#00ff00'):
                if str(img_index) not in json_data:  # Check if the image index exists in json_data
                    continue

                img_pil = ImageTk.getimage(self.raw_data[img_index]['Image'])
                draw_tool = ImageDraw.Draw(img_pil)

                for area_key, area_values in json_data[f'{img_index}'].items():
                    area_number_str = area_key.split(' ')[-1]
                    if area_values['Coordinates']['1top_x']:
                        coordinates = tuple(area_values['Coordinates'].values())
                        top_x, top_y, bot_x, bot_y = coordinates
                        rect_width = abs(bot_x - top_x)
                        rect_height = abs(bot_y - top_y)

                        # Initialize text position
                        text_x = bot_x - self.text_offset_x
                        text_y = top_y + self.text_offset_y

                        if rect_width < 30 or rect_height < 30:
                            # If the rectangle is too small, so move the text aside
                            text_x = bot_x + 5
                            text_y = top_y + 5

                        draw_tool.rectangle(coordinates, outline=self.outline[img_index][area_key], width=5)
                        draw_tool.text((text_x, text_y), str(area_number_str),
                                       font=self.pil_font, fill=self.outline[img_index][area_key])

                image_filename = os.path.join(self.rgb_folder, f"{self.outer_prefix}-{img_index + 1}.png")
                img_pil.save(image_filename)

    def get_data_dict(self):
        return self.data_dict
