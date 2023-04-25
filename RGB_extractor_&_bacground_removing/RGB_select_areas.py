import json
import os
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
import numpy as np
from PIL import ImageDraw, ImageTk
from icecream import ic

import Instruments

start_time = time.time()
ctk.set_appearance_mode("dark")
ic.configureOutput(prefix='')


class RGBExtractingCanvas(ctk.CTkFrame):
    width = 1200
    height = 1200

    def __init__(self, parent, folder, data, zoom, extension, current_folder, data_len, *args, **kwargs):
        super().__init__(master=parent, *args, **kwargs)

        # Some vars
        self.zi = zoom
        self.folder_suffix = folder
        self.extension = extension
        self.parent = parent
        self.auto_prefix = ''
        self.raw_data = data
        self.top_x, self.top_y, self.bot_x, self.bot_y = 0, 0, 0, 0
        self.area_dict = {'q': 1, 'w': 2, 'e': 3}
        self.outline = defaultdict(dict)
        self.rectangle_width = 15
        self.rect_id = None
        self.counter = 0
        self.area_number = None
        self.event_char = None
        self.parent_path = str(Path(self.raw_data[0]['Name']).parents[0]) + '/'
        self.data_dict = self.generate_data_dict()  # Autogenerate this dict at the very beginning
        self.rgb_folder = self.make_folder()
        self.outer_prefix = self.prefix()

        # Window
        self.parent.title(f'{current_folder} in total {data_len}. Select areas in picture 1 of {len(self.raw_data)}'
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
        """
        Make a folder if not exist
        :return: Parth to folder, str
        """
        if self.parent_path.endswith('Processed/'):
            self.parent_path = self.parent_path.split('Processed/')[0]
        return Instruments.create_folder(self.parent_path, "RGB_analyzing")

    def prefix(self):
        """
        Apply a specific prefix in output filename
        :return: prefix, str
        """
        png_list = []
        for png in os.listdir(self.rgb_folder):
            if png.endswith('.png'):
                png_list.append(png)
        if len(png_list) >= len(self.raw_data):
            prefix0 = png_list[-1].split('-')[0]
            return str(int(prefix0) + 1)
        if len(png_list) < len(self.raw_data):
            return str('1')

    def generate_data_dict(self):
        """
        Generates empty nested well-structured data dict.
        :return: Structured dict filled with None
        """
        data_dict = {}
        for i in range(len(self.raw_data)):
            data_dict[i] = {}
            for n in range(1, 4):
                data_dict[i][f'Area {n}'] = {}
                data_dict[i][f'Area {n}']['RGB'] = {'R': None, 'G': None, 'B': None}
                data_dict[i][f'Area {n}']['Coordinates'] = {'1top_x': None, '2top_y': None, '3bot_x': None,
                                                            '4bot_y': None}
        return data_dict

    def get_mouse_position(self, event):
        """
        Get the mouse position
        :param event: mouse left-click event
        :return: None
        """
        self.top_x, self.top_y = event.x, event.y

    def update_sel_rect(self, event):
        """
        Draw rectangle based on new coordinates
        :param event: Mouse left bottom is clicked and mouse is moving
        :return: None
        """
        self.bot_x, self.bot_y = event.x, event.y
        self.canvas.coords(self.rectangle, self.top_x, self.top_y, self.bot_x, self.bot_y)

    def get_rgb_pil(self, counter=None):
        """
        Extracting the RGB values from pure non-resized image over a given rectangular area. Pillow version.
        Should be faster that cv2.
        :param counter: If passed changes the 'self.counter'
        :return: R, G, and B average values
        """
        if not counter:
            counter = self.counter
        a_list2 = []
        im12 = self.raw_data[counter]['Image_original']
        pix_count = 0
        for x in range(self.top_x * self.zi, self.bot_x * self.zi + 1):
            for y in range(self.top_y * self.zi, self.bot_y * self.zi + 1):
                h = im12.getpixel((x, y))
                pix_count += 1
                a_list2.append(h)
        r, g, b = np.mean(a_list2, axis=0)
        return [r, g, b]

    @staticmethod
    def r_c(average_rgb):
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
        resulting_json = self.rgb_folder + today + self.auto_prefix + ' Results_' + self.folder_suffix + ".json"
        with open(resulting_json, 'w', encoding='utf-8') as f:
            json.dump(self.data_dict, f, ensure_ascii=False, indent=4)

    def main_method(self, event):
        """
        The main method. Depends on which key was pressed calls corresponding methods
        :param event: q, w or e -> save drawn rectangle and extract average rgb values
                      p -> emergency stop bottom, close windows and stop script
                      f -> move to the next picture is exist and save all data to dict. If no more images - save all
                      data to a file and properly finish the program
                      a -> apply obtained for the first picture coordinates for all remaining pictures (auto-applying)
        :return:
        """
        if event.char in ('q', 'w', 'e'):
            self.area_number = self.area_dict[event.char]
            self.event_char = event.char
            self.canvas.delete(f'Area_{self.area_number}')
            avr_rgb = self.get_rgb_pil()
            self.data_dict[self.counter][f'Area {self.area_number}'] |= \
                {'RGB': {'R': avr_rgb[0], 'G': avr_rgb[1], 'B': avr_rgb[2]}}
            self.data_dict[self.counter][f'Area {self.area_number}'] |= \
                {'Coordinates': {'1top_x': self.top_x, '2top_y': self.top_y, '3bot_x': self.bot_x,
                                 '4bot_y': self.bot_y}}
            self.outline[self.counter][f'Area {self.area_number}'] = self.r_c(avr_rgb)[0]
            self.canvas.create_rectangle(self.top_x, self.top_y, self.bot_x, self.bot_y, fill='',
                                         outline=self.r_c(avr_rgb)[0], width=9, tags=f'Area_{self.area_number}')

        if event.char == 'p':
            print("Oh no, why did someone push the emergency stop butt?")
            self.parent.destroy()

        if event.char == 'a':
            dialog = ctk.CTkInputDialog(text="Do you want me to apply the same ares"
                                             " for the rest images? 1-yes, 2-no: ", title="Auto applying")
            if dialog.get_input() == '1':
                for widget in self.winfo_children():
                    widget.quit()
                self.pack_forget()
                self.destroy()
                self.auto_applying()
                self.save_image_with_areas(auto=' auto')
                self.write_rgb_json()
                print('Auto-processed has been applied.')

        if event.char == 'f':  # and not self.auto:
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
                self.save_image_with_areas()
                self.write_rgb_json()
                print('Everything is done successfully, good job, buddy!')

    def auto_applying(self):
        """
        Apply the first image obtained coordinates to the remaining one
        :return: None
        """
        for picture in range(1, len(self.raw_data)):
            for i in range(1, 4):
                self.top_x = self.data_dict[0][f'Area {i}']['Coordinates']['1top_x']
                self.top_y = self.data_dict[0][f'Area {i}']['Coordinates']['2top_y']
                self.bot_x = self.data_dict[0][f'Area {i}']['Coordinates']['3bot_x']
                self.bot_y = self.data_dict[0][f'Area {i}']['Coordinates']['4bot_y']
                avr_rgb = self.get_rgb_pil(picture)
                self.outline[picture][f'Area {i}'] = self.r_c(avr_rgb)[0]
                self.data_dict[picture][f'Area {i}'] |= \
                    {'Coordinates': {'1top_x': self.top_x, '2top_y': self.top_y, '3bot_x': self.bot_x,
                                     '4bot_y': self.bot_y}}
                self.data_dict[picture][f'Area {i}'] |= \
                    {'RGB': {'R': avr_rgb[0], 'G': avr_rgb[1], 'B': avr_rgb[2]}}

    def save_image_with_areas(self, auto=''):
        """
        Save image in lower/resized resolution. Draw corresponding rectangles if they do exist.
        :param auto: Define a file suffix if needed
        :return: None
        """
        for picture in range(len(self.data_dict)):
            img_pil = ImageTk.getimage(self.raw_data[picture]['Image'])
            draw = ImageDraw.Draw(img_pil)
            for i in range(1, 4):
                if self.data_dict[picture][f'Area {i}']['Coordinates']['1top_x']:
                    xy = tuple(self.data_dict[picture][f'Area {i}']['Coordinates'].values())
                    draw.rectangle(xy, outline=self.outline[picture][f'Area {i}'], width=5)
            img_pil.save(self.rgb_folder + self.outer_prefix + '-' +
                         str(picture + 1) + auto + '.png')
