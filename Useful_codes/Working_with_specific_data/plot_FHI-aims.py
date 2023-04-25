import os
import re
from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk
import matplotlib.pyplot as plt
from icecream import ic


class ParserApp:

    def __init__(self):
        self.root = ctk.CTk()
        self.vbm_values = []
        self.cbm_values = []
        self.total_energy_values = []
        self.max_force_values = []
        self.file_path = None
        self.duration = None
        self.num_rows = 0
        self.atomic_structure = []
        self.save_fig = False
        self.output_directory = None
        self.folder_name = None
        self.scale_options = ["linear", "log", "symlog"]
        self.current_scale = self.scale_options[1]
        self.create_gui()

    def create_gui(self):

        self.root.title("Rustem and Hassan project")
        self.root.geometry("800x600")

        open_file_button = ctk.CTkButton(self.root, text="Open File", command=self.open_file)
        open_file_button.pack(pady=20)

        print_duration_button = ctk.CTkButton(self.root, text="Print duration",
                                              command=self.print_duration)
        print_duration_button.pack(pady=20)

        scale_options_label = ctk.CTkLabel(self.root, text="Scale Options:")
        scale_options_label.pack(pady=5)

        scale_menu = ctk.CTkOptionMenu(
            self.root,
            values=self.scale_options,
            command=self.update_scale
        )
        scale_menu.pack(pady=5)

        find_atomic_structure_button = ctk.CTkButton(self.root, text="Find Updated Atomic Structure",
                                                     command=self.find_updated_atomic_structure)
        find_atomic_structure_button.pack(pady=20)

        compare_with_reference_button = ctk.CTkButton(self.root, text="Compare with Reference",
                                                      command=lambda: self.compare_with_reference())
        compare_with_reference_button.pack(pady=20)

        print_atomic_structure_button = ctk.CTkButton(self.root, text="Atomic Structure for geometry.in",
                                                      command=self.print_atomic_structure_to_file)
        print_atomic_structure_button.pack(pady=20)

        save_plots_button = ctk.CTkButton(self.root, text="Save Plots", command=self.save_plots)
        save_plots_button.pack(pady=20)

        close_plots_button = ctk.CTkButton(self.root, text="Close Plots", command=self.close_plots)
        close_plots_button.pack(pady=20)

        self.root.mainloop()

    def update_scale(self, new_scale):
        print(f"New scale selected: {new_scale}")
        self.current_scale = new_scale
        self.plot_plots()

    def plot_plots(self):
        plt.close('all')
        fig, axs = plt.subplots(2, 2, figsize=(6.75 * 2, 9 * 2))
        self.plot_vbm_values(axs[0, 0])  # HOMO
        self.plot_cbm_values(axs[1, 0])  # LUMO
        self.plot_max_force_values(axs[0, 1])  # Max force
        self.plot_total_energy_values(axs[1, 1])  # Energy
        if not self.save_fig:
            plt.show(block=False)

    def compare_with_reference(self):
        file_path = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
        if file_path:
            with open(file_path, 'r') as file:
                lines = file.readlines()
                reference_lines = [line for line in lines if line.strip() and line[0] != "#"]

                if len(reference_lines) != len(self.total_energy_values) or len(reference_lines) != len(
                        self.max_force_values):
                    print("Lengths do not match.")
                    return

                print("Lengths match.")

                tolerance = 0.00001
                total_energy_match = True
                max_force_match = True

                for i, line in enumerate(reference_lines):
                    columns = line.split()
                    ref_energy = float(columns[1])
                    ref_max_force = float(columns[5])

                    energy_difference = abs(ref_energy - self.total_energy_values[i])
                    max_force_difference = abs(ref_max_force - self.max_force_values[i])

                    if energy_difference > tolerance:
                        total_energy_match = False
                        print(f"Energy values do not match at index {i}: {ref_energy} != {self.total_energy_values[i]}")

                    if max_force_difference > tolerance:
                        max_force_match = False
                        print(
                            f"Max force values do not match at"
                            f" index {i}: {ref_max_force} != {self.max_force_values[i]}")

                if total_energy_match:
                    print("All total energy values values match.")
                if max_force_match:
                    print("All maximum force values match.")

    def clear_all(self):
        self.close_plots()
        self.vbm_values = []
        self.cbm_values = []
        self.total_energy_values = []
        self.max_force_values = []
        self.file_path = None
        self.duration = None
        self.num_rows = 0
        self.atomic_structure = []
        self.save_fig = False
        self.output_directory = None
        self.folder_name = None
        self.current_scale = self.scale_options[1]

    @staticmethod
    def close_plots():
        plt.close('all')

    def print_duration(self, end, start):
        if self.duration:
            ic(self.duration)
            file_size_mb = os.path.getsize(self.file_path) / (1024 * 1024)
            self.num_rows = format(self.num_rows, ",")
            file_size_mb = format(int(file_size_mb), ",")
            ic(self.num_rows)
            ic(file_size_mb)
            ic('')
            duration_without_seconds = self.duration.rsplit(',', 1)[0]

            # Format the result string without seconds
            result = f'{duration_without_seconds}, num of rows: {self.num_rows}, size: {file_size_mb} MB'
            print(result)

    def print_updated_atomic_structure(self):
        print("\nUpdated atomic structure:")
        for line in self.atomic_structure:
            values = re.findall(r"[-+]?\d*\.\d+|\d+|[A-Za-z]+", line)
            formatted_line = "{:<12} {:<12} {:<12} {}".format(values[1], values[2], values[3], values[4])
            print(formatted_line)

    def find_updated_atomic_structure(self):
        if self.file_path:
            self.parse_updated_atomic_structure()
            self.print_updated_atomic_structure()
        else:
            self.file_path = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
            self.find_updated_atomic_structure()

    def parse_updated_atomic_structure(self):
        with open(self.file_path, 'r') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if "Updated atomic structure:" in line:
                    self.atomic_structure = []  # Reset the atomic_structure list
                    j = i + 1
                    while j < len(lines) and "x [A]" not in lines[j]:
                        j += 1
                    j += 1  # Move to the line after "x [A] y [A] z [A]"
                    while j < len(lines) and re.match(r"\s*atom", lines[j]):
                        self.atomic_structure.append(lines[j])
                        j += 1

    def print_atomic_structure_to_file(self):
        if not self.atomic_structure:
            print("No updated atomic structure found. Please find the updated atomic structure first.")
            return
        print('\nAtomic structure for geometry.in')
        for line in self.atomic_structure:
            values = re.findall(r"[-+]?\d*\.\d+|\d+|[A-Za-z]+", line)
            formatted_line = "atom {:<12} {:<12} {:<12} {}".format(values[1], values[2], values[3], values[4])
            print(formatted_line)

    def parse_values(self):
        self.vbm_values = []
        self.cbm_values = []
        self.total_energy_values = []
        self.max_force_values = []
        start_time = None
        end_time = None
        self.num_rows = 0
        with open(self.file_path, 'r') as file:
            for line in file:
                self.num_rows += 1
                if "Highest occupied state (VBM) at" in line:
                    value = float(re.findall(r"[-+]?\d*\.\d+(?:[Ee][-+]?\d+)?|\d+", line)[0])
                    self.vbm_values.append(value)
                elif "Lowest unoccupied state (CBM) at" in line:
                    value = float(re.findall(r"[-+]?\d*\.\d+(?:[Ee][-+]?\d+)?|\d+", line)[0])
                    self.cbm_values.append(value)
                elif "Total energy uncorrected" in line:
                    value = float(re.findall(r"[-+]?\d*\.\d+(?:[Ee][-+]?\d+)?|\d+", line)[0])
                    self.total_energy_values.append(value)
                elif "Maximum force component is" in line:
                    value = float(re.findall(r"[-+]?\d*\.\d+(?:[Ee][-+]?\d+)?|\d+", line)[0])
                    self.max_force_values.append(value)
                elif "Date     :" in line and "Time     :" in line:
                    date_time_str = re.search(r"Date\s*:\s*(\d+),\s*Time\s*:\s*(\d+\.\d+)", line)
                    date_str, time_str = date_time_str.groups()
                    date_time = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H%M%S.%f")

                    if start_time is None:
                        start_time = date_time
                    end_time = date_time

        if start_time and end_time:
            total_duration = end_time - start_time
            days = total_duration.days
            remainder = total_duration.seconds
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            hours += days * 24
            self.duration = f"{hours} hours, {minutes} minutes, and {seconds + total_duration.microseconds / 1e6} seconds."
            self.print_duration(end_time, start_time)

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
        if self.file_path:
            self.parse_values()
            self.plot_plots()
            plt.show()

    def save_plots(self):
        if not self.file_path:
            print("No file opened. Please open a file first.")
            return
        self.output_directory = os.path.dirname(self.file_path)
        self.folder_name = os.path.basename(self.output_directory)
        fig, axs = plt.subplots(2, 2, figsize=(9 * 3 / 2.54, 6.75 * 3 / 2.54), dpi=300)
        self.plot_vbm_values(axs[0, 0])  # HOMO
        self.plot_cbm_values(axs[1, 0])  # LUMO
        self.plot_max_force_values(axs[0, 1])  # Max force
        self.plot_total_energy_values(axs[1, 1])  # Energy

        plt.tight_layout()

        output_file = os.path.join(self.output_directory, f"{self.folder_name}_combined_plots.png")
        plt.savefig(output_file, dpi=300)
        self.close_plots()
        print(f"Plots saved to {self.output_directory}")

    def plot_vbm_values(self, ax):
        ax.plot(self.vbm_values, marker='o', linestyle='-')
        ax.set_xlabel('Step')
        ax.set_ylabel('VBM Value (eV)')
        ax.set_title('Highest Occupied State (VBM) Values')
        ax.text(0.05, 0.05, f'The number of occurrences is: {len(self.vbm_values)}', transform=ax.transAxes,
                verticalalignment='bottom')
        ax.grid(True)

    def plot_cbm_values(self, ax):
        ax.plot(self.cbm_values, marker='o', linestyle='-')
        ax.set_xlabel('Step')
        ax.set_ylabel('CBM Value (eV)')
        ax.set_title('Lowest Unoccupied State (CBM) Values')
        ax.text(0.05, 0.05, f'The number of occurrences is: {len(self.cbm_values)}', transform=ax.transAxes,
                verticalalignment='bottom')
        ax.grid(True)

    def plot_total_energy_values(self, ax):
        ax.plot(self.total_energy_values, marker='o', linestyle='-')
        ax.set_xlabel('Step')
        ax.set_ylabel('Total Energy (eV)')
        ax.set_title('Total Energy Values')
        ax.grid(True)

    def plot_max_force_values(self, ax):
        ax.plot(self.max_force_values, marker='o', linestyle='-')
        ax.set_xlabel('Step')
        ax.set_ylabel('Max Force (eV/AA)')
        ax.set_title('Maximum Force Values')
        ax.set_yscale(self.current_scale)
        ax.grid(True)


if __name__ == "__main__":
    ic.configureOutput(prefix='')
    app = ParserApp()
