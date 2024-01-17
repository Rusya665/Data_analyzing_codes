import os
import tkinter as tk

import customtkinter as ctk
import matplotlib.pyplot as plt
import pandas as pd


class TransmittancePlotter:
    """
    A class to plot transmittance data using matplotlib.

    :param data: The transmittance data as a pandas DataFrame.
    :param file_name: The name of the file from which the data was loaded.
    """

    def __init__(self, data: pd.DataFrame, file_name: str):
        """
        Initialize the TransmittancePlotter with data and a file name.
        """
        self.file_name = file_name
        self.data = data
        self.fig, self.ax = plt.subplots()
        self.fig.canvas.manager.set_window_title(f"{self.file_name} Transmittance")
        self.lines = {}
        self.additional_lines = []
        self._plot_initial()
        self.original_x_lim = self.ax.get_xlim()
        self.original_y_lim = self.ax.get_ylim()
        plt.show(block=False)
        self.control_panel = ControlPanel(self, self.file_name)
        self.control_panel.run_control_panel()

    def _plot_initial(self) -> None:
        """
        Plot the initial set of transmittance data.
        """
        wavelengths = self.data.columns[5:]  # Assuming wavelength data starts from the 6th column
        for index, row in self.data.iterrows():
            line, = self.ax.plot(wavelengths, row[5:], label=row['Name'])
            self.lines[row['Name']] = line
        self.ax.set_xlabel('Wavelength (nm)')
        self.ax.set_ylabel('Transmittance (%)')
        self.ax.legend()
        self.legend = self.ax.legend()
        # self.fig.canvas.set_window_title("Figure Window Title")

    def reset_view(self) -> None:
        """
        Reset the plot view to the initial x and y-axis limits.
        """
        self.ax.set_xlim(self.original_x_lim)
        self.ax.set_ylim(self.original_y_lim)
        self.fig.canvas.draw_idle()

    def _update_legend(self) -> None:
        """
        Update the plot legend to only show visible data lines.
        """
        visible_lines = [line for line in self.lines.values() if line.get_visible()]
        labels = [label for label, line in self.lines.items() if line.get_visible()]
        self.legend.remove()  # Remove the old legend
        self.legend = self.ax.legend(visible_lines, labels)  # Create a new legend with the visible lines and labels

    def toggle_visibility(self, sample_name: str) -> None:
        """
        Toggle the visibility of a data line in the plot.

        :param sample_name: The name of the sample associated with the line to toggle.
        """
        line = self.lines[sample_name]
        line.set_visible(not line.get_visible())
        self._update_legend()
        self.fig.canvas.draw_idle()

    def show_all(self) -> None:
        """
        Set all data lines to visible in the plot.
        """
        for line in self.lines.values():
            line.set_visible(True)
        self._update_legend()
        self.fig.canvas.draw_idle()
        for chk in self.control_panel.checkboxes:
            chk.select()

    def hide_all(self) -> None:
        """
        Set all data lines to hidden in the plot.
        """
        for line in self.lines.values():
            line.set_visible(False)
        self._update_legend()
        self.fig.canvas.draw_idle()
        for chk in self.control_panel.checkboxes:
            chk.deselect()

    def zoom_to_x(self, x_min: float, x_max: float) -> None:
        """
        Zoom into a specified range on the x-axis.

        :param x_min: The minimum x-axis value to zoom to.
        :param x_max: The maximum x-axis value to zoom to.
        """
        self.ax.set_xlim(x_min, x_max)
        self.fig.canvas.draw_idle()

    def zoom_to_y(self, y_min: float, y_max: float) -> None:
        """
        Zoom into a specified range on the y-axis.

        :param y_min: The minimum y-axis value to zoom to.
        :param y_max: The maximum y-axis value to zoom to.
        """
        self.ax.set_ylim(y_min, y_max)
        self.fig.canvas.draw_idle()

    def draw_horizontal_line(self, y_value: float, **kwargs) -> None:
        """
        Draw a horizontal line at the specified y-value.

        :param y_value: The y-axis value at which to draw the horizontal line.
        """
        h_line = self.ax.axhline(y=y_value, **kwargs)
        self.additional_lines.append(h_line)
        self.fig.canvas.draw_idle()

    def draw_vertical_line(self, x_value: float, **kwargs) -> None:
        """
        Draw a vertical line at the specified x-value.

        :param x_value: The x-axis value at which to draw the vertical line.
        """
        v_line = self.ax.axvline(x=x_value, **kwargs)
        self.additional_lines.append(v_line)
        self.fig.canvas.draw_idle()

    def remove_additional_lines(self) -> None:
        """
        Remove all additional lines (horizontal or vertical) from the plot.
        """
        while self.additional_lines:
            line = self.additional_lines.pop()
            line.remove()
        self.fig.canvas.draw_idle()


class ControlPanel(ctk.CTk):
    """
    A Control Panel class that provides an interface for manipulating the TransmittancePlotter plot.

    :param plotter: An instance of the TransmittancePlotter class to control.
    :param file_name: The name of the file being analyzed.
    """

    def __init__(self, plotter: 'TransmittancePlotter', file_name: str):
        super().__init__()
        self.file_name = file_name
        self.plotter = plotter
        self.title(f"{self.file_name} Transmittance Data Control Panel")
        self.geometry("950x750")

        self.checkboxes = []

        self.scrollable_frame = ctk.CTkScrollableFrame(self, width=380, height=580, corner_radius=10)
        self.scrollable_frame.grid(row=0, column=0, pady=10, padx=10, sticky="nsew")

        for sample_name in self.plotter.lines.keys():
            chk = ctk.CTkCheckBox(self.scrollable_frame, text=sample_name,
                                  command=lambda name=sample_name: self.plotter.toggle_visibility(name))
            chk.select()
            chk.pack(anchor=tk.W, pady=2)
            self.checkboxes.append(chk)

        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=0, column=1, pady=10, padx=10, sticky="nsew")

        self.show_hide_frame = ctk.CTkFrame(self)
        self.show_hide_frame.grid(row=1, column=0, pady=10, padx=10, sticky="ew")

        self.show_all_button = ctk.CTkButton(self.show_hide_frame, text="Show All", command=self.plotter.show_all)
        self.show_all_button.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5))

        self.hide_all_button = ctk.CTkButton(self.show_hide_frame, text="Hide All", command=self.plotter.hide_all)
        self.hide_all_button.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 10))

        # Entry for zooming to x
        self.x_zoom_frame = ctk.CTkFrame(self.control_frame)
        self.x_zoom_frame.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

        self.x_zoom_label = ctk.CTkLabel(self.x_zoom_frame, text="Zoom to X:")
        self.x_zoom_label.pack(side=tk.LEFT)

        self.x_zoom_entry_min = ctk.CTkEntry(self.x_zoom_frame, placeholder_text="X min")
        self.x_zoom_entry_min.pack(side=tk.LEFT)

        self.x_zoom_entry_max = ctk.CTkEntry(self.x_zoom_frame, placeholder_text="X max")
        self.x_zoom_entry_max.pack(side=tk.LEFT)

        self.x_zoom_button = ctk.CTkButton(self.x_zoom_frame, text="Zoom", command=self.zoom_x)
        self.x_zoom_button.pack(side=tk.LEFT)

        # Add widgets for y-zooming in the control frame
        self.y_zoom_frame = ctk.CTkFrame(self.control_frame)
        self.y_zoom_frame.grid(row=1, column=0, pady=10, padx=10, sticky="ew")

        self.y_zoom_label = ctk.CTkLabel(self.y_zoom_frame, text="Zoom to Y:")
        self.y_zoom_label.pack(side=tk.LEFT)

        self.y_zoom_entry_min = ctk.CTkEntry(self.y_zoom_frame, placeholder_text="Y min")
        self.y_zoom_entry_min.pack(side=tk.LEFT)

        self.y_zoom_entry_max = ctk.CTkEntry(self.y_zoom_frame, placeholder_text="Y max")
        self.y_zoom_entry_max.pack(side=tk.LEFT)

        self.y_zoom_button = ctk.CTkButton(self.y_zoom_frame, text="Zoom", command=self.zoom_y)
        self.y_zoom_button.pack(side=tk.LEFT)

        # Add a Reset View button
        self.reset_view_button = ctk.CTkButton(self.control_frame, text="Reset View", command=self.plotter.reset_view)
        self.reset_view_button.grid(row=2, column=0, pady=10, padx=10)

        # Entry for drawing a horizontal line
        self.h_line_frame = ctk.CTkFrame(self.control_frame)
        self.h_line_frame.grid(row=3, column=0, pady=10, padx=10, sticky="ew")

        self.h_line_label = ctk.CTkLabel(self.h_line_frame, text="Draw H-Line at Y:")
        self.h_line_label.pack(side=tk.LEFT)

        self.h_line_entry = ctk.CTkEntry(self.h_line_frame, placeholder_text="Y value")
        self.h_line_entry.pack(side=tk.LEFT)

        self.h_line_button = ctk.CTkButton(self.h_line_frame, text="Draw", command=self.draw_h_line)
        self.h_line_button.pack(side=tk.LEFT)

        # Add widgets for drawing a vertical line in the control frame
        self.v_line_frame = ctk.CTkFrame(self.control_frame)
        self.v_line_frame.grid(row=4, column=0, pady=10, padx=10, sticky="ew")

        self.v_line_label = ctk.CTkLabel(self.v_line_frame, text="Draw V-Line at X:")
        self.v_line_label.pack(side=tk.LEFT)

        self.v_line_entry = ctk.CTkEntry(self.v_line_frame, placeholder_text="X value")
        self.v_line_entry.pack(side=tk.LEFT)

        self.v_line_button = ctk.CTkButton(self.v_line_frame, text="Draw", command=self.draw_v_line)
        self.v_line_button.pack(side=tk.LEFT)

        # Button to remove all lines
        self.remove_lines_button = ctk.CTkButton(self.control_frame, text="Remove all lines",
                                                 command=self.plotter.remove_additional_lines)
        self.remove_lines_button.grid(row=5, column=0, pady=10, padx=10)

    def zoom_x(self) -> None:
        """
        Zooms in on the x-axis of the plot based on the user input in the x-axis zoom fields.
        """
        try:
            x_min = float(self.x_zoom_entry_min.get())
            x_max = float(self.x_zoom_entry_max.get())
            self.plotter.zoom_to_x(x_min, x_max)
        except ValueError:
            pass

    def zoom_y(self) -> None:
        """
        Zooms in on the y-axis of the plot based on the user input in the y-axis zoom fields.
        """
        try:
            y_min = float(self.y_zoom_entry_min.get())
            y_max = float(self.y_zoom_entry_max.get())
            self.plotter.zoom_to_y(y_min, y_max)
        except ValueError:
            pass

    def draw_h_line(self) -> None:
        """
        Draws a horizontal line on the plot at the y-axis value specified by the user.
        """
        try:
            y_value = float(self.h_line_entry.get())
            self.plotter.draw_horizontal_line(y_value)
        except ValueError:
            pass

    def draw_v_line(self) -> None:
        """
        Draws a vertical line on the plot at the x-axis value specified by the user.
        """
        try:
            x_value = float(self.v_line_entry.get())
            self.plotter.draw_vertical_line(x_value)
        except ValueError:
            pass

    def run_control_panel(self) -> None:
        """
        Runs the control panel event loop. This should be called to start the control panel application.
        """
        self.mainloop()


class InitialWindow(ctk.CTk):
    """
    A CustomTkinter window class that prompts the user to open a file.
    """

    def __init__(self):
        """
        Initializes the InitialWindow with a title and a fixed size.
        """
        super().__init__()
        self.title("Open File")
        self.geometry("300x100")
        self.files_to_show = {}  # This will be a dictionary to keep track of the counts
        self.open_button = ctk.CTkButton(self, text="Open File", command=self.open_file)
        self.open_button.pack(pady=20)

    def open_file(self) -> None:
        """
        Opens a file dialog for the user to select a file, and initializes a plotter for the file.
        If the file is already opened, increments a counter for the file name.
        """
        filepath = ctk.filedialog.askopenfilename()  # Use a file dialog to get the file path
        if filepath:
            file_name = os.path.basename(filepath)
            # Check if the file is already opened and increment the counter
            if file_name in self.files_to_show:
                self.files_to_show[file_name] += 1
                file_name = f"{file_name} {self.files_to_show[file_name]}"
            else:
                self.files_to_show[file_name] = 1  # Initialize the counter

            self.state('iconic')
            data = pd.read_excel(filepath)
            TransmittancePlotter(data=data, file_name=file_name)


if __name__ == "__main__":
    initial_window = InitialWindow()
    initial_window.mainloop()
