import json
import os
import time
import tkinter as tk
from collections import defaultdict
from datetime import datetime
from idlelib.tooltip import Hovertip
from pathlib import Path
from tkinter import filedialog, ttk, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk
from natsort import natsorted
from tqdm import tqdm

from Instruments import get_screen_settings
from RGB_select_areas import RGBExtractingCanvas


class RGBMainRoot(ctk.CTk):
    screen_width, screen_height = 700, 680

    def __init__(self, zoom=2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.s = ttk.Style()
        self.s.configure('Treeview', rowheight=30)
        # Some variables
        self.data = {}
        self.frames = {}
        self.zi = zoom  # Zoom. For FullHD screens 4 is fine (when working with 6000x4000 pictures). For 4k: 2
        self.zoom_rate = 1 / self.zi
        self.save_after = False
        # window
        self.title("Average RGB value extractor.py")
        self.geometry(f"{self.screen_width}x{self.screen_height}")
        self.minsize(600, 600)
        self.resizable(True, True)

        SpecifyPath(self, self.zoom_rate, self.get_data)

    def get_data(self, highest_path, data=None, extension=None, new_zoom=None, first_img=0):
        """
        Pass a data_dict from one Tkinter clss to another one
        :param highest_path: The highest folder path of the project
        :param extension: Images extension
        :param data: Dict with data
        :param new_zoom: If desired zoom might be changed
        :param first_img: If desired first image to shown might be changed
        :return: None
        """
        all_instances = []
        temp_rgb_executor = None
        self.data = data
        zoom = new_zoom if new_zoom else self.zi
        total_data_dict = {}
        for i, (key, value) in enumerate(self.data.items()):
            temp_rgb_executor = RGBExtractingCanvas(self, folder=key, data=value, zoom=zoom, extension=extension,
                                                    current_folder=i + 1, data_len=len(self.data), start_from=first_img)
            all_instances.append(temp_rgb_executor)
            total_data_dict[key] = temp_rgb_executor.get_data_dict()
        temp_rgb_executor.destroy()
        for instance in tqdm(all_instances, desc=f'Saving images with rectangles', ncols=100, unit='directory',
                             colour='#ffc25c', position=0, leave=True):
            instance.save_image_with_areas_after()
        # Write the total data to a JSON file
        today = f'{datetime.now():%Y-%m-%d %H.%M.%S%z}'
        resulting_json = os.path.join(highest_path, today + ' Total_RGB.json')
        with open(resulting_json, 'w', encoding='utf-8') as f:
            json.dump(total_data_dict, f, ensure_ascii=False, indent=5)
        self.destroy()


class SpecifyPath(ctk.CTkFrame):
    def __init__(self, parent, zoom_rate, get_data, *args, **kwargs):
        super().__init__(master=parent, *args, **kwargs)

        # Some variables
        self.parent = parent
        self.zoom_rate = zoom_rate
        self.table_size = 15
        if self.zoom_rate == 1 / 4:
            self.table_size = 13
        self.extension = '.jpg'
        self.file_directory = '/'
        self.files_selected = []
        self.get_data = get_data
        self.data = defaultdict(dict)
        self.nodes = {}
        self.new_data = {}
        self.first_img = 0

        # widgets
        self.pack(fill=ctk.BOTH, expand=True)
        self.label_1 = ctk.CTkLabel(self, text='Specify a directory with images to work with')
        self.label_1.pack()
        self.button_1 = ctk.CTkButton(self, text='Choose a directory', command=lambda: self.ask_directory())
        self.button_1.pack()

        self.first_frame = FirstFrame(parent=self, width=200, height=200, fg_color='transparent')
        self.first_frame.pack()

        self.table_frame = TableFrame(parent=self, height=800)
        self.table_frame.pack(pady=10)

        self.frame = ProceedFrame(parent=self, width=200, height=200)
        self.frame.pack(pady=10)

        self.lowest_frame = LowestFrame(self, fg_color='transparent')
        self.lowest_frame.pack(fill='x')

        self.progress_bar = ctk.CTkProgressBar(master=self, width=300)
        self.progress_bar.pack()
        self.progress_bar.set(0)

    def set_zoom(self, event) -> None:
        """
        Set zoom value
        :param event: Pick a given int
        :return: None
        """
        self.zoom_rate = 1 / int(event)

    def set_first_img(self, event) -> None:
        """
        Set first image to be shown
        :param event: Pick given int
        :return: None
        """
        self.first_img = int(event) - 1

    def exit(self) -> None:
        """
        Close Tkinter and script
        :return: None
        """
        self.quit()

    @staticmethod
    def change_appearance_mode_event(new_appearance_mode: str) -> None:
        """
        Change the Tkinter appearance mode
        :param new_appearance_mode: Type of appearance mode
        :return: None
        """
        ctk.set_appearance_mode(new_appearance_mode)

    def resize_image(self, img):
        """
        Resizing an image based on the specified zoom rate
        :param img: Numeric order of an image
        :return: Resized image to show with Tkinter
        """
        image = Image.open(img)
        height = image.height * self.zoom_rate
        width = image.width * self.zoom_rate
        img_resize = image.resize((int(width), int(height)), resample=Image.Resampling.NEAREST,
                                  reducing_gap=None)  # Use filter NEAREST to increase performance
        img_result = ImageTk.PhotoImage(img_resize)
        return img_result

    def final_output(self, state):
        """
        Choose the state to work on
        :param state: Selected files or all the files
        :return: None
        """
        self.data.clear()
        self.files_selected = []
        if state == "Selected":
            for item in self.table_frame.table.selection():
                self.treeview_expand_collapse(item, True, select=True)
                self.table_frame.table.set(item)
            self.items_select()
            self.out()
        if state == 'All':
            self.table_frame.table.selection_add(self.table_frame.table.get_children())
            for item in self.table_frame.table.get_children():
                self.treeview_expand_collapse(item, True, select=True)
            self.items_select()
            self.out()

    def expand_collapse(self, expand=True):
        """
        Only expand/collapse item in treeview
        :param expand: expand if True, collapse if False
        :return: None
        """
        for item in self.table_frame.table.get_children():
            self.treeview_expand_collapse(item, expand, select=False)

    def treeview_expand_collapse(self, item, expand_collapse, select=False):
        """
        Expand/collapse treeview. Select all nested elements in a table and expand parental ones
        :param select: select expanded values
        :param expand_collapse: True for expanding, False - collapsing
        :param item: Item to select
        :return: None
        """
        # Expand items
        self.table_frame.table.item(item, open=expand_collapse)
        if expand_collapse and select:
            self.table_frame.table.selection_add(item)
        # Select all nested (children) items
        if self.table_frame.table.get_children(item):
            for item_inner in self.table_frame.table.get_children(item):
                self.treeview_expand_collapse(item_inner, expand_collapse, select)

    def items_select(self):
        """
        Returns selected value/clues from the table
        :return: None
        """
        for i in self.table_frame.table.selection():
            if self.table_frame.table.item(i)['tags'] == ['file']:
                self.files_selected.append(self.table_frame.table.item(i)['values'][-1])

    def ask_directory(self):
        """
        Built-in Tkinter function to return a str with a path
        :return: String with a path
        """
        self.file_directory = filedialog.askdirectory(mustexist=True)
        self.list_files()
        self.label_1.configure(text=self.file_directory)

    def set_extension(self, event):
        """
        Set extension for filtering all unnecessary files and
        updating global extension and rebuilding the table of files
        :param event: Chose extension through the ComboBox
        """
        self.extension = '.' + event.lower()
        if self.file_directory == '/':
            return
        self.list_files()

    def list_files(self):
        """
        Update and fill the file table with filtered files
        """
        # Clean the treeview before filling
        for i in self.table_frame.table.get_children():
            self.table_frame.table.delete(i)
        abspath = os.path.abspath(self.file_directory).replace('\\', '/')
        root_node = self.table_frame.table.insert('', 'end', text=os.path.basename(abspath), open=True)
        self.process_directory(root_node, abspath)

    def process_directory(self, parent, path, depth=1):
        """
        Insert to a table and into the file_list filtered by extension type of files, including nested folders.
        Will show folders only if it contains required file.
        :param parent: parent folder
        :param path: path to work with
        :param depth: depth of the folders path
        :return: None
        """

        for file in natsorted(os.listdir(path)):
            abspath = os.path.join(path, file).replace('\\', '/')
            b = path.replace(self.file_directory, '').count('/')
            if os.path.isfile(abspath):
                if file.endswith(self.extension):  # Insert a file only if extension(s) suits
                    with Image.open(abspath) as img:
                        width, height = img.size
                    size = str(round(os.path.getsize(abspath) / 1048576, 2)) + ' MB'
                    data = [f'{width}x{height}', size, abspath]
                    self.table_frame.table.insert(parent=parent, index=tk.END, text=file, values=data, tags='file')
            if os.path.isdir(abspath):
                extension_flag = False
                for dir_path, dir_names, files in os.walk(abspath):
                    for filename in files:
                        f_name = os.path.join(dir_path, filename)
                        if f_name.endswith(self.extension):
                            extension_flag = True
                if extension_flag:  # Insert a folder only if extension(s) suits
                    if abspath.endswith('RGB_analyzing'):
                        return
                    elif b == depth and not abspath.endswith('Processed'):  # Nested folders with the deep of 1 only
                        # allowed for the Processed folders
                        return messagebox.showerror('Waring!', f"Too many sub folders in"
                                                               f" a folder {abspath}")
                    oid = self.table_frame.table.insert(parent, 'end', text=file, open=False, tags='folder',
                                                        values=['', '', abspath])
                    self.process_directory(oid, abspath)

    def out(self):
        """
        Resize images accordingly and generate output dict
        :return: None
        """
        if not self.files_selected:
            messagebox.showerror('Waring!', "Choose a folder(s) or an image(s) to continue!")
        else:
            folder_name = []
            counter = 0
            # for ind, file in enumerate(self.files_selected):
            for ind, file in tqdm(enumerate(self.files_selected), desc=f'Preparing images to work with', ncols=100,
                                  unit='picture', colour='#ffc25c', total=len(self.files_selected), leave=False):
                self.progress_bar.set(round((1 - (len(self.files_selected) - ind - 1) /
                                             len(self.files_selected)), 2))
                self.update_idletasks()
                dir_name = os.path.basename(Path(file).parents[0])
                if 'Processed/' in file:
                    dir_name = Path(file.split('Processed/')[0]).name
                folder_name.append(dir_name)
                if ind != 0 and not folder_name[ind - 1] == folder_name[ind]:
                    counter = 0
                self.data[dir_name][counter] = {'Name': file,
                                                'Image': self.resize_image(file),
                                                'Image_original': Image.open(file).convert('RGB')}
                counter += 1
            for widget in self.winfo_children():
                widget.quit()
            self.pack_forget()
            self.get_data(data=self.data, extension=self.extension, new_zoom=int(1 / self.zoom_rate),
                          first_img=self.first_img, highest_path=self.file_directory)


class FirstFrame(ctk.CTkFrame):
    def __init__(self, parent, width=200, height=200, fg_color='transparent', *args, **kwargs):
        super().__init__(master=parent, width=width, height=height, fg_color=fg_color, *args, **kwargs)
        self.parent = parent
        self.extension_combox = ctk.CTkComboBox(self, values=['JPG', 'PNG'], width=70,
                                                command=lambda event: self.parent.set_extension(event))
        self.expand = ctk.CTkButton(self, text='Expand all', width=20,
                                    command=lambda: self.parent.expand_collapse())
        self.collapse = ctk.CTkButton(self, text='Collapse all', width=20,
                                      command=lambda: self.parent.expand_collapse(False))
        self.pick_zoom = ctk.CTkComboBox(self, values=['1', '2', '3', '4', '5'], width=70,
                                         command=self.parent.set_zoom)
        self.pick_zoom.set(str(int(1 / self.parent.zoom_rate)))
        self.pick_first_image = ctk.CTkComboBox(self, values=[str(i) for i in range(1, 16)], width=70,
                                                command=self.parent.set_first_img)
        self.pick_first_image.set('1')
        self.extension_label = ctk.CTkLabel(self, text='Extension')
        self.zoom_picking_label = ctk.CTkLabel(self, text='Zoom')
        self.pick_first_image_label = ctk.CTkLabel(self, text='First img')
        self.extension_label.grid(row=0, column=2, columnspan=2, sticky='w')
        self.zoom_picking_label.grid(row=0, column=3, sticky='NSEW')
        self.pick_first_image_label.grid(row=0, column=4, sticky='NSEW', )
        self.extension_combox.grid(row=1, column=2, sticky='w', pady=0, padx=0)
        self.expand.grid(row=1, column=0, sticky='w', pady=0, padx=0)
        self.collapse.grid(row=1, column=1, sticky='w', pady=0, padx=7)
        self.pick_zoom.grid(row=1, column=3, sticky='w', pady=0, padx=7)
        self.pick_first_image.grid(row=1, column=4, sticky='w', pady=0, padx=7)
        self.hovers()

    def hovers(self):
        hover_delay = 400
        hover_text_expand_all = 'Expand all folders'
        hover_text_collapse_all = 'Collapse all folders'
        hover_text_extension = 'Choose extension to work with'
        hover_text_zoom = 'Choose zoom to override auto calculated'
        hover_text_first_img = 'Choose the first image to be shown using\nRGBExtractingCanvas'
        Hovertip(self.expand, hover_text_expand_all, hover_delay=hover_delay)
        Hovertip(self.collapse, hover_text_collapse_all, hover_delay=hover_delay)
        Hovertip(self.extension_label, hover_text_extension, hover_delay=hover_delay)
        Hovertip(self.extension_combox, hover_text_extension, hover_delay=hover_delay)
        Hovertip(self.zoom_picking_label, hover_text_zoom, hover_delay=hover_delay)
        Hovertip(self.pick_zoom, hover_text_zoom, hover_delay=hover_delay)
        Hovertip(self.pick_first_image_label, hover_text_first_img, hover_delay=hover_delay)
        Hovertip(self.pick_first_image, hover_text_first_img, hover_delay=hover_delay)


class TableFrame(ctk.CTkFrame):
    def __init__(self, parent, height=200, *args, **kwargs):
        super().__init__(master=parent, height=height, *args, **kwargs)
        self.parent = parent
        self.table_scrollbar = ctk.CTkScrollbar(self)
        self.table_scrollbar.pack(side='right', fill='y')
        self.table = ttk.Treeview(self, columns=('Dimensions', 'Size'),
                                  selectmode='extended', height=self.parent.table_size,
                                  yscrollcommand=self.table_scrollbar.set)
        self.table.heading('#0', text='Name', anchor='w')
        self.table.heading(0, text='Dimensions', anchor='w')
        self.table.heading(1, text='Size', anchor='w')
        self.table.column('#0', width=350)
        self.table.column(0, width=150)
        self.table.column(1, width=100)
        self.table.pack(side='left', fill='y')
        self.table_scrollbar.configure(command=self.table.yview)
        self.table.bind('<<TreeviewSelect>>', lambda event: self.parent.items_select())


class ProceedFrame(ctk.CTkFrame):
    def __init__(self, parent, width=200, height=200, *args, **kwargs):
        super().__init__(master=parent, width=width, height=height, *args, **kwargs)
        self.parent = parent
        self.label_in_frame = ctk.CTkLabel(master=self, text='Proceed with selected or all the files:')
        self.button_selected = ctk.CTkButton(self, text='Selected', width=50,
                                             command=lambda: self.parent.final_output("Selected"))
        self.button_all = ctk.CTkButton(self, text='All', width=50, command=lambda: self.parent.final_output("All"))
        self.label_in_frame.pack(fill='x', padx=5)
        self.button_selected.pack(side='left', padx=15)
        self.button_all.pack(side='right', padx=15)


class LowestFrame(ctk.CTkFrame):
    def __init__(self, parent, fg_color='transparent', *args, **kwargs):
        super().__init__(master=parent, fg_color=fg_color, *args, **kwargs)
        self.parent = parent
        self.lowest_frame_left = ctk.CTkFrame(self, fg_color='transparent')
        self.lowest_frame_right = ctk.CTkFrame(self, fg_color='transparent')
        self.lowest_frame_left.pack(side='left', padx=15)
        self.lowest_frame_right.pack(side='right', padx=15)
        self.appearance_mode_label = ctk.CTkLabel(self.lowest_frame_left, text='Appearance mode')
        self.appearance_mode_label.pack()
        self.appearance_mode = ctk.CTkOptionMenu(self.lowest_frame_left, values=["Dark", "Light", "System"], width=100,
                                                 command=self.parent.change_appearance_mode_event)
        self.appearance_mode.pack()
        self.exit_button = ctk.CTkButton(self.lowest_frame_right, text='Exit', width=70,
                                         command=lambda: self.parent.exit())
        self.exit_button.pack(side='bottom')


if __name__ == "__main__":
    start_time = time.time()
    ctk.set_appearance_mode("dark")
    screen = get_screen_settings()
    z = 1
    if screen == (1920, 1080):
        z = 4
    elif screen == (3840, 2160):
        z = 2
    app_1 = RGBMainRoot(zoom=z)
    app_1.mainloop()
    print("\n", "--- %s seconds ---" % (time.time() - start_time))
