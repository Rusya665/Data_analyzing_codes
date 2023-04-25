import time
import tkinter as tk
from collections import defaultdict
from pathlib import Path
from tkinter import filedialog, ttk, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk

from Instruments import *
from RGB_select_areas import RGBExtractingCanvas

start_time = time.time()
ctk.set_appearance_mode("dark")


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
        # window
        self.title("Average RGB value extractor.py")
        self.geometry(f"{self.screen_width}x{self.screen_height}")
        self.resizable(True, True)

        SpecifyPath(self, self.zoom_rate, self.get_data)

    def get_data(self, data=None, extension=None, new_zoom=None):
        """
        Pass a data_dict from one Tkinter clss to another one
        :param extension: Images extension
        :param data: Dict with data
        :param new_zoom: If desired zoom might be changed
        :return: None
        """
        self.data = data
        zoom = new_zoom if new_zoom else self.zi
        for i, (key, value) in enumerate(self.data.items()):
            RGBExtractingCanvas(self, folder=key, data=value, zoom=zoom, extension=extension, current_folder=i,
                                data_len=len(self.data))
        self.destroy()


class SpecifyPath(ctk.CTkFrame):
    def __init__(self, parent, zoom_rate, get_data, *args, **kwargs):
        super().__init__(master=parent, *args, **kwargs)

        # Some variables
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

        # widgets
        self.pack(fill=ctk.BOTH, expand=True)
        self.label_1 = ctk.CTkLabel(self, text='Specify a directory with images to work with')
        self.label_1.pack()
        self.button_1 = ctk.CTkButton(self, text='Choose a directory', command=lambda: self.ask_directory())
        self.button_1.pack()
        self.first_frame = ctk.CTkFrame(self, width=200, height=200, fg_color='transparent')
        self.first_frame.pack()
        self.combox = ctk.CTkComboBox(self.first_frame, values=['JPG', 'PNG'], width=70,
                                      command=lambda event: self.set_extension(event))
        self.expand = ctk.CTkButton(self.first_frame, text='Expand all', width=20,
                                    command=lambda: self.expand_collapse())
        self.collapse = ctk.CTkButton(self.first_frame, text='Collapse all', width=20,
                                      command=lambda: self.expand_collapse(False))
        self.pick_zoom = ctk.CTkComboBox(self.first_frame, values=['1', '2', '3', '4', '5'], width=70,
                                         command=self.set_zoom)
        self.pick_zoom.set(str(int(1 / self.zoom_rate)))
        self.extension_label = ctk.CTkLabel(self.first_frame, text='Extension')
        self.zoom_picking_label = ctk.CTkLabel(self.first_frame, text='Zoom')
        self.extension_label.grid(row=0, column=2, columnspan=2, sticky='w')
        self.zoom_picking_label.grid(row=0, column=3, sticky='NSEW', )
        self.combox.grid(row=1, column=2, sticky='w', pady=0, padx=0)
        self.expand.grid(row=1, column=0, sticky='w', pady=0, padx=0)
        self.collapse.grid(row=1, column=1, sticky='w', pady=0, padx=7)
        self.pick_zoom.grid(row=1, column=3, sticky='w', pady=0, padx=7)
        self.table_frame = ctk.CTkFrame(master=self, height=800)
        self.table_frame.pack(pady=10)
        self.table_scrollbar = ctk.CTkScrollbar(master=self.table_frame)
        self.table_scrollbar.pack(side='right', fill='y')
        self.table = ttk.Treeview(self.table_frame, columns=('Dimensions', 'Size'),
                                  selectmode='extended', height=self.table_size,
                                  yscrollcommand=self.table_scrollbar.set)
        self.table.heading('#0', text='Name', anchor='w')
        self.table.heading(0, text='Dimensions', anchor='w')
        self.table.heading(1, text='Size', anchor='w')
        self.table.column('#0', width=350)
        self.table.column(0, width=150)
        self.table.column(1, width=100)
        self.table.pack(side='left', fill='y')
        self.table_scrollbar.configure(command=self.table.yview)
        self.table.bind('<<TreeviewSelect>>', lambda event: self.items_select())
        self.frame = ctk.CTkFrame(master=self, width=200, height=200)
        self.frame.pack(pady=10)
        self.label_in_frame = ctk.CTkLabel(master=self.frame, text='Proceed with selected or all the files:')
        self.button_selected = ctk.CTkButton(self.frame, text='Selected', width=50,
                                             command=lambda: self.final_output("Selected"))
        self.button_all = ctk.CTkButton(self.frame, text='All', width=50, command=lambda: self.final_output("All"))
        self.label_in_frame.pack(fill='x', padx=5)
        self.button_selected.pack(side='left', padx=15)
        self.button_all.pack(side='right', padx=15)
        self.lowest_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.lowest_frame_left = ctk.CTkFrame(self.lowest_frame, fg_color='transparent')
        self.lowest_frame_right = ctk.CTkFrame(self.lowest_frame, fg_color='transparent')
        self.lowest_frame.pack(fill='x')
        self.lowest_frame_left.pack(side='left', padx=15)
        self.lowest_frame_right.pack(side='right', padx=15)
        self.appearance_mode_label = ctk.CTkLabel(self.lowest_frame_left, text='Appearance mode')
        self.appearance_mode_label.pack()
        self.appearance_mode = ctk.CTkOptionMenu(self.lowest_frame_left, values=["Dark", "Light", "System"], width=100,
                                                 command=self.change_appearance_mode_event)
        self.appearance_mode.pack()
        self.exit_button = ctk.CTkButton(self.lowest_frame_right, text='Exit', width=70, command=lambda: self.exit())
        self.exit_button.pack(side='bottom')
        self.progress_bar = ctk.CTkProgressBar(master=self, width=300)
        self.progress_bar.pack()
        self.progress_bar.set(0)

    def set_zoom(self, event):
        """
        Set zoom value
        :param event: Pick a given int
        :return: None
        """
        self.zoom_rate = 1 / int(event)

    def exit(self):
        """
        Close Tkinter and script
        :return: None
        """
        self.quit()

    @staticmethod
    def change_appearance_mode_event(new_appearance_mode: str):
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
            for item in self.table.selection():
                self.treeview_expand_collapse(item, True, select=True)
                self.table.set(item)
            self.items_select()
            self.out()
        if state == 'All':
            self.table.selection_add(self.table.get_children())
            for item in self.table.get_children():
                self.treeview_expand_collapse(item, True, select=True)
            self.items_select()
            self.out()

    def expand_collapse(self, expand=True):
        """
        Only expand/collapse item in treeview
        :param expand: expand if True, collapse if False
        :return: None
        """
        for item in self.table.get_children():
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
        self.table.item(item, open=expand_collapse)
        if expand_collapse and select:
            self.table.selection_add(item)
        # Select all nested (children) items
        if self.table.get_children(item):
            for item_inner in self.table.get_children(item):
                self.treeview_expand_collapse(item_inner, expand_collapse, select)

    def items_select(self):
        """
        Returns selected value/clues from the table
        :return: None
        """
        for i in self.table.selection():
            if self.table.item(i)['tags'] == ['file']:
                self.files_selected.append(self.table.item(i)['values'][-1])

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
        for i in self.table.get_children():
            self.table.delete(i)
        abspath = os.path.abspath(self.file_directory).replace('\\', '/')
        root_node = self.table.insert('', 'end', text=os.path.basename(abspath), open=True)
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
        for file in os.listdir(path):
            abspath = os.path.join(path, file).replace('\\', '/')
            b = path.replace(self.file_directory, '').count('/')
            if os.path.isfile(abspath):
                if file.endswith(self.extension):  # Insert a file only if extension(s) suits
                    with Image.open(abspath) as img:
                        width, height = img.size
                    size = str(round(os.path.getsize(abspath) / 1048576, 2)) + ' MB'
                    data = [f'{width}x{height}', size, abspath]
                    self.table.insert(parent=parent, index=tk.END, text=file, values=data, tags='file')
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
                    oid = self.table.insert(parent, 'end', text=file, open=False, tags='folder',
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
            for ind, file in enumerate(self.files_selected):
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
            self.get_data(data=self.data, extension=self.extension, new_zoom=int(1 / self.zoom_rate))


if __name__ == "__main__":
    screen = get_screen_settings()
    z = 1
    if screen == (1920, 1080):
        z = 4
    elif screen == (3840, 2160):
        z = 2
    app_1 = RGBMainRoot(zoom=z)
    app_1.mainloop()

print("\n", "--- %s seconds ---" % (time.time() - start_time))
