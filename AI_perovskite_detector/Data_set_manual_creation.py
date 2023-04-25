import pathlib
import time
import tkinter as tk
from datetime import datetime

import customtkinter as ctk
import numpy
import xlsxwriter as xw
from PIL import Image, ImageTk, ImageGrab
from imutils import perspective


class CornerDetector:
    """
    A class that provides a graphical interface for detecting the four corners of an image.
    The detected corner coordinates are saved to an Excel file.
    Attributes:
    image_folder (pathlib.Path): The folder containing the images to be processed.
    image_list (list): A list of image paths in the folder.
    file_names (list): A list of filenames of the images in the folder.
    Global_counter (int): A counter for the images processed.
    corner_counter (int): A counter for the corners selected.
    points (list): A list of selected corner coordinates.
    top_x, top_y (int): The coordinates of the latest clicked point.
    size (int): The size of the circle drawn around the selected point.
    rect_id, arc_id (int): Canvas item IDs for the rectangle and arc.
    zi (int): Zoom factor for displaying the image.
    zoom_rate (float): The inverse of the zoom factor.
    root (ctk.CTk): The main window of the application.
    img_initial (PIL.ImageTk.PhotoImage): The first image to be displayed.
    canvas (ctk.CTkCanvas): The canvas for displaying the image and user interactions.
    workbook, worksheet (xlsxwriter.Workbook, xlsxwriter.Worksheet): The workbook and worksheet for saving corner data.
    """
    def __init__(self, image_folder):
        """
         Initializes the CornerDetector object with the given image folder and sets up the GUI.

        :param image_folder: The folder containing the images to be processed.
        """
        self.image_folder = image_folder
        self.image_list, self.file_names = self.load_images()
        self.Global_counter = 0
        self.corner_counter = 0
        self.points = []
        self.top_x, self.top_y = 0, 0
        self.size = 2
        self.rect_id = None
        self.arc_id = None
        self.zi = 1
        self.zoom_rate = 1 / self.zi

        self.root = ctk.CTk()
        self.root.title(f"Select 4 corners in picture 1 of {len(self.image_list)} of the"
                        f" {self.image_list[self.Global_counter]}")
        self.root.geometry(self.center_window(1200, 700))
        self.root.configure(background='grey')
        self.img_initial = self.image_tk(0)

        self.canvas = ctk.CTkCanvas(self.root, width=self.img_initial.width(), height=self.img_initial.height(),
                                    borderwidth=0, highlightthickness=0)
        self.canvas.pack(expand=True)
        self.canvas.img = self.img_initial
        self.canvas.create_image(0, 0, image=self.img_initial, anchor=tk.NW, tag='image')

        self.canvas.bind('<Button-1>', self.mouse_event)
        self.canvas.bind_all("<KeyPress>", self.save_coordinates_move_on)
        self.canvas.update()

        self.workbook, self.worksheet = self.create_workbook()

        self.root.mainloop()

    def load_images(self):
        """
        Loads images from the image folder and returns a list of image paths and filenames.

        :return: A tuple containing the list of image paths and filenames.
        """
        extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        image_list = [str(f) for f in self.image_folder.glob("*") if f.suffix.lower() in extensions]
        file_names = [f.name for f in self.image_folder.glob("*") if f.suffix.lower() in extensions]
        return image_list, file_names

    def create_workbook(self):
        """
        Creates an Excel workbook and worksheet to store the corner data.

        :return: A tuple containing the workbook and worksheet objects.
        """
        workbook = xw.Workbook(self.create_folder() / f'{datetime.now():%Y-%m-%d %H.%M.%S%z}'
                                                      f' Results_{self.image_folder.name}.xlsx')
        worksheet = workbook.add_worksheet('Corners')
        return workbook, worksheet

    def create_folder(self):
        """
        Creates a folder for saving corner detection results if it does not exist.

        :return: The created folder's pathlib.Path object.
        """
        corner_detection_folder = self.image_folder / "Corner_Detection"
        if not corner_detection_folder.exists():
            corner_detection_folder.mkdir()
        return corner_detection_folder

    def image_tk(self, number):
        """
        Opens and resizes an image from the image list and returns a PhotoImage object for display on the canvas.

        :param number: The index of the image in the image list.
        :return: The resized PIL.ImageTk.PhotoImage object.
        """
        try:
            img_main = Image.open(self.image_list[number])
            height = img_main.height * self.zoom_rate
            width = img_main.width * self.zoom_rate
            img_resize = img_main.resize((int(width), int(height)), Image.Resampling.NEAREST)
            img_result = ImageTk.PhotoImage(img_resize)
            return img_result
        except IndexError:
            self.workbook.close()
            self.root.destroy()

    def mouse_event(self, event):
        """
        Handles mouse click events on the canvas and records the clicked coordinates as corner points.

        :param event: The mouse click event object.
        :return: None
        """
        if self.corner_counter < 5:
            self.top_x, self.top_y = event.x, event.y
            self.canvas.create_oval(self.top_x - self.size, self.top_y + self.size, self.top_x + self.size,
                                    self.top_y - self.size, fill='', outline='red', width=5, tags='circle')
            self.points.append((self.top_x * self.zi, self.top_y * self.zi))
            self.corner_counter += 1
        if self.corner_counter == 5:
            self.canvas.delete('circle')
            self.canvas.update()
            self.points.clear()
            self.corner_counter = 0

    def results(self):
        """
        Writes the detected corner coordinates to the worksheet.

        :return: None
        """
        self.worksheet.write(self.Global_counter, 0, str(self.file_names[self.Global_counter]))
        points_array = numpy.array(self.points)
        points_sorted = perspective.order_points(points_array)
        flat_list = [x for xs in points_sorted for x in xs]
        self.worksheet.write_row(self.Global_counter, 1, flat_list)

    def save_coordinates_move_on(self, event):
        """
        Handles keyboard events to save coordinates, move to the next image, or exit the program.

        :param event: The keyboard event object.
        :return: None
        """
        if event.char == 'c':
            self.canvas.delete('circle')
            self.canvas.update()
            self.points.clear()
            self.corner_counter = 0

        if event.char == 'f':
            if self.corner_counter == 4:
                self.results()
                x = self.root.winfo_rootx() + self.canvas.winfo_x()
                y = self.root.winfo_rooty() + self.canvas.winfo_y()
                x1 = x + self.canvas.winfo_width()
                y1 = y + self.canvas.winfo_height()
                current_name = self.file_names[self.Global_counter].split('.')[0]
                ImageGrab.grab().crop((x, y, x1, y1)).save(self.create_folder() / f'{current_name}.png')
                self.canvas.delete('circle')
                self.canvas.delete('image')
                self.Global_counter += 1
                self.corner_counter = 0
                self.points.clear()
                if self.Global_counter < len(self.image_list):
                    self.root.title(
                        f"Select areas in picture {self.Global_counter + 1} of {len(self.image_list)}"
                        f" of the {self.image_list[self.Global_counter]}")
                    img = self.image_tk(self.Global_counter)
                    self.canvas.img = img
                    self.canvas.create_image(0, 0, image=img, anchor=tk.NW, tag='image')
                    self.canvas.update()
                else:
                    print('Everything is done successfully, good job, buddy!')
                    self.workbook.close()
                    self.root.destroy()

        if event.char == 'p':
            print("Oh no, why did someone push the emergency stop button?")
            self.workbook.close()
            self.root.destroy()

    def center_window(self, width=300, height=200):
        """
        Centers the main window on the screen with the specified width and height.

        :param width: The width of the main window.
        :param height: The height of the main window.
        :return: A formatted string containing the window dimensions and position.
        """
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        return f'{width}x{height}+{int(x)}+{int(y)}'


if __name__ == '__main__':
    start_time = time.time()
    path_folder = pathlib.Path("path/to/your/folder")
    corner_detector = CornerDetector(path_folder)
    print("\n", "--- %s seconds ---" % (time.time() - start_time))
