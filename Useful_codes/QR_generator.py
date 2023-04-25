# Make the SVG being saved with sengo. But thwn you no longer can use drawer and color mask.
import os
import random
import time
from tkinter import filedialog, messagebox, colorchooser

import customtkinter as ctk
import qrcode
import qrcode.image.svg
from PIL import Image, ImageTk, ImageDraw
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import (
    SolidFillColorMask,
    RadialGradiantColorMask,
    SquareGradiantColorMask,
    HorizontalGradiantColorMask,
    VerticalGradiantColorMask,
)
from qrcode.image.styles.moduledrawers import (
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
    VerticalBarsDrawer,
    HorizontalBarsDrawer,
)


class QRCodeGeneratorApp(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("QR Code Generator")
        self.geometry("800x600")
        self.minsize(800, 410)

        # Add the left, middle, and right frames
        self.middle_frame = MiddleFrame(self)
        self.left_frame = LeftFrame(self, self.middle_frame)
        self.right_frame = RightFrame(self, self.middle_frame)
        self.left_frame.grid(row=0, column=0, sticky='nsew')
        self.middle_frame.grid(row=0, column=1, sticky='nsew')
        self.right_frame.grid(row=0, column=2, sticky='nsew')

        # Set the column weights for proper resizing
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)


class MiddleFrame(ctk.CTkFrame):
    def __init__(self, parent, fill_color=(0, 0, 0)):
        super().__init__(parent, width=500, height=600, border_width=2)
        self.version = None
        self.fast_qr = True
        self.qr = None
        self.parent = parent
        self.color_mask_key = "SolidFillColorMask"
        self.logo_path = None
        self.fill_color = fill_color
        self.back_color = (255, 255, 255)
        self.extra_color = (0, 125, 255)
        self.time_label = ctk.CTkLabel(self, text="")
        self.canvas = ctk.CTkCanvas(self, width=450, height=450)
        self.entry = ctk.CTkTextbox(self, height=15, width=350, wrap='none')
        self.module_drawer_options = {
            "SquareModuleDrawer": SquareModuleDrawer(),
            "GappedSquareModuleDrawer": GappedSquareModuleDrawer(),
            "CircleModuleDrawer": CircleModuleDrawer(),
            "RoundedModuleDrawer": RoundedModuleDrawer(),
            "VerticalBarsDrawer": VerticalBarsDrawer(),
            "HorizontalBarsDrawer": HorizontalBarsDrawer(),
        }
        self.module_drawer = self.module_drawer_options["SquareModuleDrawer"]
        self.build_gui()

    def change_version(self, num: int):
        self.version = num
        self.on_generate_click()

    def apply_color_mask(self):
        color_masks = {
            "SolidFillColorMask": SolidFillColorMask(back_color=self.back_color,
                                                     front_color=self.fill_color),
            "RadialGradiantColorMask": RadialGradiantColorMask(back_color=self.back_color,
                                                               center_color=self.fill_color,
                                                               edge_color=self.extra_color),
            "SquareGradiantColorMask": SquareGradiantColorMask(back_color=self.back_color,
                                                               center_color=self.fill_color,
                                                               edge_color=self.extra_color),
            "HorizontalGradiantColorMask": HorizontalGradiantColorMask(back_color=self.back_color,
                                                                       left_color=self.fill_color,
                                                                       right_color=self.extra_color),
            "VerticalGradiantColorMask": VerticalGradiantColorMask(back_color=self.back_color,
                                                                   bottom_color=self.fill_color,
                                                                   top_color=self.extra_color),
        }
        return color_masks[self.color_mask_key]

    def change_qr_generation_speed(self, state):
        self.fast_qr = state
        self.on_generate_click()

    def change_color_mask_key(self, color_mask_key):
        self.color_mask_key = color_mask_key
        self.on_generate_click()

    def change_module_drawer(self, selected_module_drawer):
        self.module_drawer = self.module_drawer_options[selected_module_drawer]
        self.on_generate_click()

    def change_fill_color(self, color):
        self.fill_color = color
        self.on_generate_click()

    def change_extra_color(self, color):
        self.extra_color = color
        self.on_generate_click()

    def generate_qr_code(self, data: str, svg=False):
        if svg:
            self.qr = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage)
            return
        qr = qrcode.QRCode(
            version=self.version,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        if not self.version:
            qr.make(fit=True)
        if self.fast_qr:
            qr_img = qr.make_image(
                fill_color=self.fill_color,
                back_color=self.back_color
            )
        else:
            qr_img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=self.module_drawer,
                color_mask=self.apply_color_mask(),
            )
        if self.logo_path is not None and self.logo_path.strip() != "":
            logo = Image.open(self.logo_path).convert("RGBA")
            modules_size = len(qr.modules)
            module_width = qr_img.width // modules_size

            # Calculate the scaling factor based on the canvas size
            scaling_factor = min(self.canvas.winfo_width(), self.canvas.winfo_height()) / qr_img.width

            max_logo_width = int(modules_size // 2 * module_width * 0.8 * scaling_factor)
            max_logo_height = int(modules_size // 2 * module_width * 0.8 * scaling_factor)

            logo.thumbnail((max_logo_width, max_logo_height), Image.LANCZOS)
            logo_width, logo_height = logo.size

            upper_left = int((modules_size // 2) * module_width - logo_width // (2 * scaling_factor))
            lower_right = int((modules_size // 2) * module_width + logo_width // (2 * scaling_factor))

            logo_pos_x = 0.5  # Set relative position in X-axis (0 to 1)
            logo_pos_y = 0.5  # Set relative position in Y-axis (0 to 1)

            box = (
                int(qr_img.width * logo_pos_x - logo_width // 2),
                int(qr_img.height * logo_pos_y - logo_height // 2),
            )
            # qr_img.paste(logo, box, logo)
            qr_img.paste(logo, box)

        return qr_img

    def on_generate_click(self):
        start_time = time.time()
        self.canvas.delete("all")
        data = self.entry.get("1.0",
                              "end-1c")  # Get text from the beginning to the end, excluding the last newline character
        if not data:
            return
        self.qr = self.generate_qr_code(data)
        # self.qr = self.qr.resize((200, 200), Image.NEAREST)
        photo_img = ImageTk.PhotoImage(self.qr)  # Convert the img to a PhotoImage
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x_center = canvas_width // 2
        y_center = canvas_height // 2
        # self.canvas.create_image(200, 200, image=photo_img, anchor='center', tags="qr_image")
        self.canvas.create_image(x_center, y_center, image=photo_img, anchor='center', tags="qr_image")
        self.canvas.image = photo_img  # Store the PhotoImage in the canvas to prevent garbage collection
        total_time = time.time() - start_time
        self.time_label.configure(text=f'Generation time {round(total_time, 2)} sec')

    def build_gui(self):

        entry_label = ctk.CTkLabel(self, text="Enter your text to generate QR:")
        entry_label.pack(pady=5)

        self.entry.pack(padx=10, pady=10)
        self.entry.bind('<KeyRelease>', lambda event: self.on_generate_click())

        logo_path_label = ctk.CTkLabel(self, text="Logo image path (optional):")
        logo_path_label.pack()

        logo_button = ctk.CTkButton(self, text="Browse...", command=self.browse_logo)
        logo_button.pack()

        self.canvas.pack(pady=10)

        self.time_label.pack(padx=5, pady=5)

        save_button = ctk.CTkButton(self, text="Save QR Code", command=self.save_qr_code)
        save_button.pack()

    def browse_logo(self):
        self.logo_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
        self.parent.right_frame.clear_logo_button.configure(state=ctk.NORMAL, hover=True)
        self.on_generate_click()

    def save_qr_code(self):
        if self.qr is not None:
            if not self.fast_qr:
                file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                         filetypes=[("PNG Image", "*.png"),
                                                                    ("JPEG Image", "*.jpg;*.jpeg"),
                                                                    ("CSV Image", "*.csv"),
                                                                    ("BMP Image", "*.bmp")])
                self.qr.save(file_path)
                messagebox.showinfo(title="Success!",
                                    message=f"QR code {os.path.basename(file_path)} successfully has been saved")
            if self.fast_qr:
                file_path = filedialog.asksaveasfilename(defaultextension=".svg",
                                                         filetypes=[("SVG Image", "*.svg"),
                                                                    ("PNG Image", "*.png"),
                                                                    ("JPEG Image", "*.jpg;*.jpeg"),
                                                                    ("CSV Image", "*.csv"),
                                                                    ("BMP Image", "*.bmp")])
                if os.path.splitext(file_path)[1] == '.svg':
                    data = self.entry.get("1.0", "end-1c")
                    self.generate_qr_code(data, svg=True)
                self.qr.save(file_path)
                messagebox.showinfo(title="Success!",
                                    message=f"QR code {os.path.basename(file_path)} successfully has been saved")
        else:
            messagebox.showwarning("Warning", "Generate a QR code before saving.")


class LeftFrame(ctk.CTkFrame):
    def __init__(self, parent, middle_frame):
        super().__init__(parent, width=200, height=600, border_width=2)
        self.parent = parent
        self.middle_frame = middle_frame
        self.svg_fast_label = ctk.CTkLabel(self,
                                           text="Enable to faster QR  generation. \n Disable for more options\n Note!"
                                                " Only fast regime allows\n to save in .svg")
        self.svg_fast_label.pack(pady=5)
        self.svg_fast = ctk.CTkSwitch(master=self, text="Fast QRcode generation",
                                      command=self.fast_qr)
        self.svg_fast.select(1)
        self.svg_fast.pack(pady=5)
        self.module_drawer_label = ctk.CTkLabel(self, text="Module Drawer:")
        self.module_drawer_label.pack(pady=3)
        self.module_drawer_menu = ctk.CTkOptionMenu(self, values=[k for k, v in
                                                                  self.middle_frame.module_drawer_options.items()],
                                                    width=218,
                                                    command=self.select_drawer, state='disabled', hover=False)
        self.module_drawer_menu.set("SquareModuleDrawer")
        self.module_drawer_menu.pack(pady=3)
        self.color_mask_label = ctk.CTkLabel(self, text="Color Mask:")
        self.color_mask_label.pack(pady=3)
        self.color_mask_menu = ctk.CTkOptionMenu(self,
                                                 values=['SolidFillColorMask', 'RadialGradiantColorMask',
                                                         'SquareGradiantColorMask', 'HorizontalGradiantColorMask',
                                                         'VerticalGradiantColorMask'],
                                                 command=self.select_mask, state='disabled', hover=False)
        self.color_mask_menu.set("SolidFillColorMask")
        self.color_mask_menu.pack(pady=3)
        ctk.CTkLabel(self, text="Manual size changing works\n super slow!").pack(pady=10)
        self.resizing_checkbox = ctk.CTkCheckBox(master=self, text="Change QRcode size manually",
                                                 command=self.qr_resizing)
        self.resizing_checkbox.pack(padx=5, pady=5)
        self.version_label = ctk.CTkLabel(self, text='QR size 4 of 40')
        self.version_slider = ctk.CTkSlider(self, from_=1, to=40, number_of_steps=40, hover=False,
                                            command=self.change_version, state="disabled")
        self.version_slider.set(4)
        self.version_label.pack(padx=5, pady=5)
        self.version_slider.pack(padx=5, pady=5)
        self.lowest_frame = ctk.CTkFrame(self, fg_color='transparent', border_width=0)
        self.lowest_frame.pack(side='bottom', pady=3)
        self.appearance_mode_label = ctk.CTkLabel(self.lowest_frame, text='Appearance mode')
        self.appearance_mode_label.pack()
        self.appearance_mode = ctk.CTkOptionMenu(self.lowest_frame, values=["Dark", "Light", "System"], width=100,
                                                 command=self.change_appearance_mode_event)
        self.appearance_mode.pack(pady=10)

    def fast_qr(self):
        state = ctk.DISABLED
        hover = ctk.FALSE
        fast = True
        if self.svg_fast.get() == 0:
            state = ctk.NORMAL
            hover = ctk.TRUE
            fast = False
        self.module_drawer_menu.configure(state=state, hover=hover)
        self.color_mask_menu.configure(state=state, hover=hover)
        self.middle_frame.change_qr_generation_speed(fast)

    def change_version(self, event):
        self.version_label.configure(text=f'QR size {int(event)} of 40')
        self.middle_frame.change_version(int(event))

    def qr_resizing(self):
        if self.resizing_checkbox.get() == 1:
            self.version_slider.configure(state='normal', hover=True)
        if self.resizing_checkbox.get() == 0:
            self.version_slider.configure(state='disabled', hover=False)

    @staticmethod
    def change_appearance_mode_event(new_appearance_mode: str):
        """
        Change the Tkinter appearance mode
        :param new_appearance_mode: Type of appearance mode
        :return: None
        """
        ctk.set_appearance_mode(new_appearance_mode)

    def select_mask(self, event: str):
        state = ctk.NORMAL
        if event == "SolidFillColorMask":
            state = ctk.DISABLED
        self.parent.right_frame.custom_secondary_color_button.configure(state=state)
        self.parent.right_frame.random_secondary_color_button.configure(state=state)
        self.middle_frame.change_color_mask_key(event)

    def select_drawer(self, event: str):
        self.middle_frame.change_module_drawer(event)


class RightFrame(ctk.CTkFrame):
    def __init__(self, parent, middle_frame):
        super().__init__(parent, width=200, height=600, border_width=2)
        self.parent = parent
        self.middle_frame = middle_frame
        self.preset_var = ctk.StringVar()
        self.fill_color_var = (0, 0, 0)
        self.secondary_color_var = (0, 0, 0)
        self.fill_color_frame = ctk.CTkFrame(self)
        self.fill_color_label = ctk.CTkLabel(self.fill_color_frame, text='Fill color options').pack()
        self.secondary_color_frame = ctk.CTkFrame(self)
        self.secondary_color_label = ctk.CTkLabel(self.secondary_color_frame, text='Secondary color options').pack()
        self.fill_color_frame.pack(pady=5)
        self.secondary_color_frame.pack(pady=5)
        self.custom_fill_color_button = ctk.CTkButton(self.fill_color_frame, text="Custom fill color",
                                                      command=self.custom_fill_color, state='normal')
        self.custom_fill_color_button.pack(padx=7, pady=10)

        self.random_fill_color_button = ctk.CTkButton(self.fill_color_frame, text="Random fill color",
                                                      command=self.random_fill_color, state='normal')
        self.random_fill_color_button.pack(padx=7, pady=10)

        self.custom_secondary_color_button = ctk.CTkButton(self.secondary_color_frame, text="Custom secondary color",
                                                           command=self.custom_secondary_color, state='disabled')
        self.custom_secondary_color_button.pack(padx=7, pady=10)

        self.random_secondary_color_button = ctk.CTkButton(self.secondary_color_frame, text="Random secondary color",
                                                           command=self.random_secondary_color, state='disabled')
        self.random_secondary_color_button.pack(padx=7, pady=10)

        ctk.CTkLabel(self, text='Preset fill color').pack(pady=5)
        colors = [("Black", "(0, 0, 0)"),
                  ("Violet", "(127, 0, 255)"),
                  ("Orange", "(255, 165, 0)"),
                  ]

        for text, value in colors:
            ctk.CTkRadioButton(
                self,
                text=text,
                value=value,
                variable=self.preset_var,
                command=self.preset_fill_color,
            ).pack(padx=7, pady=10)
        self.clear_logo_button = ctk.CTkButton(self, text='Clear logo', command=self.clear_logo, state=ctk.DISABLED, hover=False)
        self.clear_logo_button.pack(pady=20)

    def clear_logo(self):
        self.middle_frame.logo_path = None
        self.middle_frame.on_generate_click()

    def custom_fill_color(self):
        chosen_color = colorchooser.askcolor()[0]  # Open the color dialog and get the chosen color as RGB tuple
        if chosen_color:  # Make sure a color was chosen
            self.fill_color_var = chosen_color  # Set the chosen color as the new fill color
            self.change_fill_color()  # Apply the new fill color

    def custom_secondary_color(self):
        chosen_color = colorchooser.askcolor()[0]  # Open the color dialog and get the chosen color as RGB tuple
        if chosen_color:  # Make sure a color was chosen
            self.secondary_color_var = chosen_color  # Set the chosen color as the new fill color
            self.change_fill_color()  # Apply the new fill color

    def random_fill_color(self):
        self.fill_color_var = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.change_fill_color()

    def random_secondary_color(self):
        self.secondary_color_var = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.change_secondary_color()

    def preset_fill_color(self):
        color = self.preset_var.get()
        color_tuple = tuple(map(int, color.strip("()").split(", ")))
        self.middle_frame.change_fill_color(color_tuple)

    def change_fill_color(self):
        self.middle_frame.change_fill_color(self.fill_color_var)

    def change_secondary_color(self):
        self.middle_frame.change_extra_color(self.secondary_color_var)


class CustomButton(ctk.CTkButton):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)


if __name__ == "__main__":
    app = QRCodeGeneratorApp()
    app.mainloop()
