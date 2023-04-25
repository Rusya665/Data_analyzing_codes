import re
import os
import time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from icecream import ic
from matplotlib.ticker import MaxNLocator


class XLSXReader:
    """
    A class to read and process .xlsx data files, and plot the extracted data.
    """

    def __init__(self, xlsx_file, time_line, num_points=None, selected_charts=None, path_out=None, show_plot=False,
                 extension='png'):
        """
        Initialize the XLSXReader with file paths and optional number of data points.

        :param xlsx_file: str, path to the .xlsx file containing the data.
        :param time_line: str, path to the .xlsx file containing the timeline data.
        :param num_points: int, optional, number of data points to be plotted. If not provided, it will be set to the
         length of the timeline data.
        :param selected_charts: str, selected plots to be plotted
        """
        self.extension = extension
        self.path_out = path_out
        self.show_plot = show_plot
        self.xlsx_file = xlsx_file
        self.time_line = time_line
        self.df = pd.read_excel(self.xlsx_file)
        self.df_time = pd.read_excel(self.time_line, header=None)
        self.num_points = num_points if num_points is not None else len(self.df_time)
        if self.num_points >= len(self.df_time):
            self.num_points = len(self.df_time)
        self.color_map = 'jet'
        self.column_name_mapping = {
            "Efficiency (%)": "Eff. (%)",
            "Short-circuit current density (mA/cm^2)": "Jsc (mA/cm²)",
            "Open circuit voltage (V)": "Voc (V)",
            "Fill factor": "FF",
            "Maximum power (W)": "Pmax (W)",
            "Voltage at MPP (V)": "VMPP (V)",
            "Current density at MPP (mA/cm^2)": "JMPP (mA/cm²)",
            "Series resistance, Rs (ohm)": "Rs (Ω)",
            "Shunt resistance, Rsh (ohm)": "Rsh (Ω)",
        }
        self.selected_charts = selected_charts if selected_charts is not None else self.column_name_mapping.keys()
        self.plot_data(plot_type='all')
        self.plot_data(plot_type='average')

    def group_data(self, column_index=2):
        """
        Group the data based on column index.

        :param column_index: int, index of the column in the DataFrame for grouping.
        :return: dict, a dictionary containing the grouped data.
        """
        grouped_data = {}
        for _, row in self.df.iterrows():
            sample, direction = row['Sample'], row['Scan direction']
            x_val = sample.split('_')[1]
            if x_val not in grouped_data:
                grouped_data[x_val] = {'Forward': [], 'Reverse': []}

            grouped_data[x_val][direction].append(row.iloc[column_index])

        # Custom sorting function
        def custom_sort_key(x_value):
            """
            Custom sorting function.

            :param x_value: str, a string value to be sorted.
            :return: list, a list of integers and strings after splitting and converting to integers when possible.
            """
            parts = re.split(r'(\d+)', x_value)
            return [int(part) if part.isdigit() else part for part in parts]

        sorted_grouped_data = dict(sorted(grouped_data.items(), key=lambda x: custom_sort_key(x[0])))

        return sorted_grouped_data

    def extract_data_for_plotting(self, column_index):
        """
        Extract data for plotting based on the column index.

        :param column_index: int, index of the column in the DataFrame.
        :return: tuple, containing the column name and a dictionary of extracted data for plotting.
        """
        column_name = self.df.columns[column_index]
        grouped_data = self.group_data(column_index)
        extracted_data = {}

        for sample, directions in grouped_data.items():
            for direction, values in directions.items():
                extracted_data[f'{sample}_{direction}'] = values

        return column_name, extracted_data

    def plot_data(self, plot_type='all'):
        """
        Plot the extracted data.

        :param plot_type: str, optional, type of plot to create. Supported values are 'all' and 'average'. Default is 'all'.
        """
        # Apply OriginPro-like styling
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial']
        plt.rcParams['font.size'] = 16
        plt.rcParams['axes.linewidth'] = 1.1
        plt.rcParams['axes.labelpad'] = 10.0
        plot_color_cycle = plt.cycler('color', ['000000', '0000FE', 'FE0000', '008001', 'FD8000', '8c564b',
                                                'e377c2', '7f7f7f', 'bcbd22', '17becf'])
        plt.rcParams['axes.prop_cycle'] = plot_color_cycle
        plt.rcParams['axes.xmargin'] = 0
        plt.rcParams['axes.ymargin'] = 0
        plt.rcParams.update({"figure.figsize": (6.4, 4.8),
                             "figure.subplot.left": 0.177, "figure.subplot.right": 0.946,
                             "figure.subplot.bottom": 0.156, "figure.subplot.top": 0.965,
                             "axes.autolimit_mode": "round_numbers",
                             "xtick.major.size": 7,
                             "xtick.minor.size": 3.5,
                             "xtick.major.width": 1.1,
                             "xtick.minor.width": 1.1,
                             "xtick.major.pad": 5,
                             "xtick.minor.visible": True,
                             "ytick.major.size": 7,
                             "ytick.minor.size": 3.5,
                             "ytick.major.width": 1.1,
                             "ytick.minor.width": 1.1,
                             "ytick.major.pad": 5,
                             "ytick.minor.visible": True,
                             "lines.markersize": 10,
                             "lines.markerfacecolor": "none",
                             "lines.markeredgewidth": 0.8})
        num_selected_charts = len(self.selected_charts)
        grid_size = int(np.ceil(np.sqrt(num_selected_charts)))
        # ic(0.9 * grid_size/0.393701 + 5)
        # fig, axes = plt.subplots(grid_size, grid_size, figsize=(0.9 * grid_size/0.393701 + 5, 0.9 * grid_size/0.393701), dpi=300)
        fig, axes = plt.subplots(grid_size, grid_size, figsize=(12, 7), dpi=300)
        if grid_size == 1:
            axes = [[axes]]
        pad_val = 3 if grid_size >= 3 else 2
        fig.tight_layout(pad=1)
        ax = None
        plot_index = 0
        colors = plt.cm.get_cmap('jet', len(self.group_data()))
        num_columns = len(self.df.columns)
        for i in range(2, num_columns):
            column_name, extracted_data = self.extract_data_for_plotting(i)
            if column_name not in self.selected_charts:
                continue
            ax = axes[plot_index // grid_size][plot_index % grid_size]
            avg_forward = [0] * self.num_points
            avg_reverse = [0] * self.num_points
            count_forward = 0
            count_reverse = 0
            y_values = 0
            label = ''
            line_style = '-'
            marker = 'o'
            x_values = list(self.df_time[0][:self.num_points])

            for idx, (key, values) in enumerate(extracted_data.items()):
                direction = 'Forward' if key.endswith('Forward') else 'Reverse'

                if plot_type == 'all':
                    y_values = values[:self.num_points]
                    line_style = '-' if direction == 'Forward' else '--'
                    marker = 'o' if direction == 'Forward' else 's'
                    label = key.split('_')[0]
                elif plot_type == 'average':
                    if direction == 'Forward':
                        count_forward += 1
                        avg_forward = [sum(x) for x in zip(avg_forward, values[:self.num_points])]
                    else:
                        count_reverse += 1
                        avg_reverse = [sum(x) for x in zip(avg_reverse, values[:self.num_points])]
                    continue

                ax.plot(x_values, y_values, label=label,
                        color=colors(idx // 2),
                        linestyle=line_style, marker=marker, markersize=4, linewidth=1)

            if plot_type == 'average':
                avg_forward = [x / count_forward for x in avg_forward]
                avg_reverse = [x / count_reverse for x in avg_reverse]
                line_style_forward = '-'
                line_style_reverse = '--'
                marker_forward = 'o'
                marker_reverse = 's'
                ax.plot(x_values, avg_forward, label='Forward', color=colors(0),
                        linestyle=line_style_forward, marker=marker_forward, markersize=4, linewidth=1)
                ax.plot(x_values, avg_reverse, label='Reverse', color=colors(1),
                        linestyle=line_style_reverse, marker=marker_reverse, markersize=4, linewidth=1)

            ax.xaxis.set_major_locator(MaxNLocator(integer=True))  # Set the x-axis tick locator
            ax.set_title(column_name, fontsize=12)
            ax.set_xlabel("Time, h", fontsize=10, labelpad=2)
            ax.set_ylabel(self.column_name_mapping.get(column_name, column_name), fontsize=10)
            ax.tick_params(axis='both', which='major', labelsize=8)
            plot_index += 1
        # Add a legend only once, outside the plot area
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        fig.legend(by_label.values(), by_label.keys(), loc='center right', fontsize=8)
        selected_charts_count = len(self.selected_charts) if self.selected_charts else "all"
        test_name = os.path.basename(os.path.dirname(os.path.dirname(self.xlsx_file)))
        filename = f"{test_name} {plot_type} {self.num_points} points {selected_charts_count} plots.{self.extension}"
        output_dir = os.path.dirname(self.xlsx_file)
        if self.path_out:
            output_dir = self.path_out
        output_path = os.path.join(output_dir, filename)
        plt.savefig(output_path, format=self.extension, dpi=300)
        if self.show_plot:
            fig.set_figheight(5 * grid_size)
            fig.set_figwidth(5 * grid_size)
            plt.show()


if __name__ == '__main__':
    ic.configureOutput('')
    start_time = time.time()
    path = 'path/to/your/folder'
    time_line_path = 'path/to/your/folder'
    out_path = 'path/to/your/folder'
    points = 99
    out_format = 'png'
    select_charts = ["Efficiency (%)", "Short-circuit current density (mA/cm^2)", "Open circuit voltage (V)",
                     "Fill factor"]
    XLSXReader(path, time_line_path, path_out=out_path, num_points=points, show_plot=False,
               selected_charts=select_charts, extension=out_format)
    print("\n", "--- %s seconds ---" % (time.time() - start_time))
