from __future__ import annotations

import math
import os
import time
from collections import defaultdict
from datetime import date
from typing import Optional, Dict

import colour
import numpy as np
import pandas as pd
import xlsxwriter
from natsort import natsorted
from tqdm import tqdm
from xlsxwriter.workbook import ChartScatter
from xlsxwriter.worksheet import Worksheet

from Charts_creator import ColorChartsCreator
from Color_spaces_convertion import (rgb_to_cmyk, rgb_to_hsl, rgb_to_hsv, rgb_to_lab)
from Custom_errors import ColorTemperatureIsMissing
from IV_data_plots_creator import IVPlotsCreator
from IV_prediction import YellowChannelPredictor
from Instruments import (random_color, open_file, row_to_excel_col, remove_pattern, map_name)
from RGB_and_IV_gatherer import RGBAndIVDataGatherer
from RGB_settings import *
from RGB_settings_update import UpdateSettings
from Standard_deviation_of_color_difference import StandardDeviationForEuclidianDistance


class RGBandIVplotter:
    def __init__(self, highest_path):
        start_time = time.time()
        # Main folder settings
        self.today = date.today()
        self.xlsx_name = ''
        self.highest_path = os.path.normpath(highest_path)
        self.settings = UpdateSettings(self.highest_path, SETTINGS).update_settings_based_on_path()
        print(f'Working on "{os.path.basename(self.highest_path)}"')
        self.timeline_len = 0
        self.plotter, self.iv_plotter = None, None
        self.predictor = None
        self.rgb_chart_copies, self.iv_chart_details, self.iv_prediction_chart_copies = {}, {}, {}
        self.lab_charts_copy = {}
        self.prediction_start, self.prediction_end = None, None
        self.iv_flag = True if self.settings['iv_json'] else False
        # Assuming the default cells height 20 pixels and width 64
        self.chart_horizontal_spacing = math.ceil((480 * self.settings['chart_x_scale']) / 64) + 1
        self.chart_vertical_spacing = math.ceil((288 * self.settings['chart_y_scale']) / 20) + 1
        self.chart_huge_horizontal_spacing = math.ceil(
            (480 * self.settings['all_in_one_chart_x_scale']) / 64) + 1
        self.chart_huge_vertical_spacing = math.ceil(
            (288 * self.settings['all_in_one_chart_y_scale']) / 20) + 1
        self.illuminant = colour.temperature.CCT_to_xy_CIE_D(self.settings['color_temperature'])
        self.row_first_plot = 0
        self.workbook = self.create_workbook()
        self.center = self.workbook.add_format({'align': 'center'})
        self.across_selection = self.workbook.add_format()
        self.across_selection.set_center_across()
        self.worksheet_main = self.workbook.add_worksheet('Main')
        self.worksheet_main.set_tab_color('#FFA500')
        if self.settings['Table_tab'] is not None:
            self.table_sheet = self.workbook.add_worksheet('Table')
            self.table_sheet.set_tab_color('#4169E1')
        self.iv_headers_short = [
            "\u03B7, %",  # η, %
            "Jsc, mA/cm²",  # Jsc, mA/cm²
            "Voc, V",  # Voc V
            "FF",  # FF
            "Pmax, W",  # Pmax, W
            "Vmpp, V",  # Vmpp, V
            "Jmpp, mA/cm²",  # Jmpp, mA/cm²
            "Rs, \u03A9",  # Rs, Ω
            "Rsh, \u03A9"  # Rsh, Ω
        ]
        self.delta_e_headers = ['CIE 1976', 'CIE 1994', 'CIE 1994 Textile', 'CIE 2000', 'CIE 2000 Textile',
                                'CMC acceptability', 'CMC imperceptibility', 'DIN99', 'DIN99 Textile']
        self.iv_map_dict = {short: full for short, full in zip(self.iv_headers_short, self.settings['iv_full_headers'])}
        self.data = RGBAndIVDataGatherer(highest_path=self.highest_path, settings=self.settings).data_generate()
        self.all_samples_list = list(self.data.keys())
        self.samples_number_per_row = self.settings['samples_number']
        if self.samples_number_per_row >= len(self.all_samples_list):
            self.samples_number_per_row = len(self.all_samples_list)
        self.batches, self.remainder = divmod(len(self.all_samples_list), self.samples_number_per_row)
        if self.remainder:
            print(
                f"Check the samples number and the batch ratio\n"
                f" Samples = {len(self.all_samples_list)} and batch = {self.samples_number_per_row}")

        self.set_worksheets()
        print("\nWorksheets have been set.")
        print("--- %s seconds ---" % (time.time() - start_time))
        print("\nCompressing the Excel file, hold on...")
        start_time2 = time.time()
        # if self.settings['Table_tab'] is not None:
        #     self.table_sheet.autofit()
        self.workbook.close()
        time.sleep(0.2)
        open_file(self.xlsx_name)
        print("--- %s seconds ---" % (time.time() - start_time2))
        print(f"\nThe total time is {time.time() - start_time}")

    def create_workbook(self) -> xlsxwriter.Workbook:
        """
        Create a new xlsx doc and/or folder for it.
        """
        new_folder = "RGB_plotting"
        folder_path = os.path.join(self.highest_path, new_folder)

        # Create the new folder if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Create the Excel workbook in the new folder
        base_dir = os.path.basename(self.highest_path)
        today = date.today()
        self.xlsx_name = os.path.join(folder_path, f"{today} {base_dir} Total RGB and all others.xlsx")

        return xlsxwriter.Workbook(self.xlsx_name, {'strings_to_numbers': True,
                                                    'use_future_functions': True,
                                                    'nan_inf_to_errors': True})

    def set_worksheets(self):
        # Generate a random color for each folder
        sample_color = {folder_name: random_color() for folder_name in self.data.keys()}

        for sample, data in tqdm(self.data.items(), bar_format="{l_bar}%s{bar}%s{r_bar}" % ("\033[31m", "\033[0m")):
            ws_name = sample if len(sample) < 31 else sample[:31]
            ws = self.workbook.add_worksheet(ws_name)
            ws.set_tab_color(sample_color[sample])
            self.plotter = ColorChartsCreator(workbook=self.workbook, data=data, settings=self.settings)
            self.timeline_len = len(data['Timeline'])
            self.row_first_plot = self.timeline_len * 2 + 6
            self.write_rgb_data(ws, sample, data)
            self.write_color_calculations(ws, sample)
            self.add_color_plots(ws, sample)
            if self.iv_flag and data.get('iv_data'):
                self.iv_plotter = IVPlotsCreator(workbook=self.workbook, data=data, settings=self.settings,
                                                 mapping_dict=self.iv_map_dict)
                self.write_iv_data(ws, data)
                self.add_iv_plots(ws, sample)
                if self.settings['prediction_flag']:
                    self.prediction_start = self.settings['min_possible_points_for_prediction']
                    self.prediction_end = self.timeline_len - 1
                    if isinstance(self.settings['num_of_points'], int):
                        self.prediction_start = self.settings['num_of_points']
                        self.prediction_end = self.prediction_start + 1
                    self.predictor = YellowChannelPredictor(workbook=self.workbook, settings=self.settings,
                                                            df_time=data['Timeline'], df_yellow=data['Yellow_df'],
                                                            j_sc_dict=data['iv_data'])
                    self.write_prediction_add_plots(ws, sample)
        self.add_charts_in_main_sheet_and_fill_table_sheet()

    def write_rgb_data(self, ws: Worksheet, device_name: str, data: dict) -> None:
        """
        Write headers into the Excel worksheet for a given device.

        :param ws: The xlsxwriter worksheet object where headers are to be written.
        :param device_name: The name of the device for which the sheet is being created.
        :param data: A dictionary with the raw data
        :return: None
        """
        ws.write(0, 0, device_name, self.center)

        # Write the Timeline twice
        ws.write(1, 0, 'Time, h', self.center)
        ws.write(self.timeline_len + 4, 0, 'Time, h', self.center)
        ws.write_column(2, 0, data['Timeline'].iloc[:, 0].tolist())
        ws.write_column(self.timeline_len + 5, 0, data['Timeline'].iloc[:, 0].tolist())

        written_areas = set()
        active_areas = set()  # Tracks areas for which data has been provided

        # Flag to track if a warning for "No area data present" has been printed for a time_point
        no_data_warning_flags = {}

        for time_point in range(self.timeline_len):
            time_point_str = str(time_point)
            row_offset = time_point + 2
            area_data = data['RGB_data'].get(time_point_str, {})

            if not area_data:
                print(
                    f"Warning: No area data present for device {device_name},"
                    f" Hour: {data['Timeline'].iloc[time_point, 0]}")
                no_data_warning_flags[time_point] = True
            else:
                no_data_warning_flags[time_point] = False  # Reset the flag

            for area_key, area_value in area_data.items():
                area_number = int("10" if area_key.split(' ')[-1] == "0" else area_key.split(' ')[-1])
                col_offset = (area_number - 1) * 4 + 2

                if area_number not in written_areas:
                    self.write_center_across_selection(ws, (0, col_offset), f'Area {area_number}', 3)
                    ws.write(1, col_offset, 'R', self.center)
                    ws.write(1, col_offset + 1, 'G', self.center)
                    ws.write(1, col_offset + 2, 'B', self.center)

                    written_areas.add(area_number)

                active_areas.add(area_number)

                for color_offset, color in enumerate(['R', 'G', 'B']):
                    ws.write(row_offset, col_offset + color_offset, area_value['RGB'][color])

        # Check for missing data in areas
        for area_key in active_areas:
            area_number = 0 if area_key == 10 else area_key
            for time_point in range(self.timeline_len):
                if f"Area {area_number}" not in data['RGB_data'].get(str(time_point), {}) \
                        and not no_data_warning_flags.get(time_point, False):
                    print(
                        f"Warning: Missing data for device {device_name}, "
                        f"area {area_key}, Hour: {data['Timeline'].iloc[time_point, 0]}"
                    )

    def write_center_across_selection(self, ws: Worksheet, position: tuple[int, int], text: str,
                                      number_of_cells=3) -> None:
        """
        Write text into a cell and center it across a specified number of adjacent cells in the Excel worksheet.

        This method writes the given text into the cell specified by the 'position' parameter. It then leaves the
        adjacent cells empty but sets their format to 'center across selection', effectively centering the text
        across 'number_of_cells' cells.

        :param ws: The xlsxwriter worksheet object where the text is to be written and centered.
        :param position: A tuple specifying the row and column indices of the starting cell.
        :param text: The text to be written and centered.
        :param number_of_cells: The number of cells across which the text will be centered.
        :return: None
        """
        row, col = position
        ws.write(row, col, text, self.across_selection)
        for i in range(1, number_of_cells):
            ws.write_blank(row, col + i, '', self.across_selection)

    def write_color_calculations(self, ws: Worksheet, device_name: str) -> None:
        """
        Write color calculation formulas into the Excel worksheet.

        :param ws: The xlsxwriter worksheet object where formulas are to be written.
        :param device_name: The name of the device for which the sheet is being created.
        :return: None
        """
        # Calculate average RGB and write CMYK, HSL, and HSV values
        (avg_rgb_per_time_point, standard_deviation_rgb_per_time_point, avg_lab_per_time_point,
         standard_deviation_lab_per_time_point, standard_deviation_new_rgb, standard_deviation_new_lab) \
            = self.get_average_rgb_values_per_time_point(device_name)
        initial_row = self.timeline_len + 6
        final_row = self.timeline_len * 2 + 5
        # Get starting columns from settings
        col_avg_rgb = self.settings['Starting columns']['Average RGB']
        col_stdev = self.settings['Starting columns']['STDEV']
        col_initial_vs_final = self.settings['Starting columns']['Initial vs final']
        col_rgb_euclid = self.settings['Starting columns']['RGB_Euclidian']
        col_cmyk = self.settings['Starting columns']['CMYK']
        col_hsl = self.settings['Starting columns']['HSL']
        col_hsv = self.settings['Starting columns']['HSV']
        col_lab = self.settings['Starting columns']['LAB']
        col_lab_std_dev = self.settings['Starting columns']['LAB_std_dev']
        col_lab_delta = self.settings['Starting columns']['LAB delta']
        col_yellow = self.settings['Starting columns']['Yellow']
        col_iv_data = self.settings['Starting columns']['IV data']

        self.write_center_across_selection(ws, (self.timeline_len + 3, col_avg_rgb), 'Average')
        self.write_center_across_selection(ws, (self.timeline_len + 3, col_stdev),
                                           "Standard deviation with Bessel's correction")

        self.write_center_across_selection(ws, (self.timeline_len + 3, col_initial_vs_final),
                                           'Initial vs Final', 4)
        ws.write(self.timeline_len + 5, col_initial_vs_final, 'Initial', self.center)
        ws.write(self.timeline_len + 6, col_initial_vs_final, 'Final', self.center)
        self.write_center_across_selection(ws, (self.timeline_len + 7, col_initial_vs_final),
                                           'Color difference initial vs final', 2)
        ws.write(self.timeline_len + 7, col_initial_vs_final + 1, 'RGB', self.center)
        ws.write(self.timeline_len + 7, col_initial_vs_final + 2, 'CIELAB', self.center)
        ws.write(self.timeline_len + 8, col_initial_vs_final, 'Value', self.center)
        ws.write(self.timeline_len + 9, col_initial_vs_final, 'Direct Standard Deviation Propagation', self.center)
        ws.write(self.timeline_len + 10, col_initial_vs_final, 'Partial Derivative Method', self.center)
        ws.write(self.timeline_len + 11, col_initial_vs_final, 'Monte Carlo Simulation', self.center)
        ws.write(self.timeline_len + 12, col_initial_vs_final, 'Distance STDEV.S', self.center)

        # check this "if" below
        if self.settings['LAB_standard_deviation_compute']:
            ws.write(self.timeline_len + 13, col_initial_vs_final, 'Standard deviation difference', self.center)
            col = row_to_excel_col(col_lab_std_dev + 1)
            ws.write_formula(self.timeline_len + 13, col_initial_vs_final + 2,
                             f'=SQRT({col}{initial_row}^2+{col}{final_row}^2)')
        ws.write(self.timeline_len + 7, col_initial_vs_final + 3, 'L*', self.center)
        ws.write(self.timeline_len + 9, col_initial_vs_final + 3, 'Color Temperature', self.center)
        ws.write(self.timeline_len + 11, col_initial_vs_final + 3, 'Jsc difference', self.center)

        # 'Average RGB' headers
        ws.write(self.timeline_len + 4, col_avg_rgb, 'R', self.center)
        ws.write(self.timeline_len + 4, col_avg_rgb + 1, 'G', self.center)
        ws.write(self.timeline_len + 4, col_avg_rgb + 2, 'B', self.center)

        # 'Standard Deviation' headers
        ws.write(self.timeline_len + 4, col_stdev, 'R', self.center)
        ws.write(self.timeline_len + 4, col_stdev + 1, 'G', self.center)
        ws.write(self.timeline_len + 4, col_stdev + 2, 'B', self.center)

        # 'Initial vs Final' headers with device name as suffix
        ws.write(self.timeline_len + 4, col_initial_vs_final + 1, f'R {device_name}', self.center)
        ws.write(self.timeline_len + 4, col_initial_vs_final + 2, f'G {device_name}', self.center)
        ws.write(self.timeline_len + 4, col_initial_vs_final + 3, f'B {device_name}', self.center)

        # Writing Average and Standard Deviation formulas for RGB
        for color_offset, color in enumerate(['R', 'G', 'B']):
            for data_point in range(self.timeline_len):
                formula_cells = []
                for area_number in range(1, 11):  # 10 areas
                    col_num = (area_number - 1) * 4 + col_avg_rgb + color_offset
                    col_letter = row_to_excel_col(col_num + 1)  # +1 because row_to_excel_col expects 1-based indexing
                    formula_cells.append(f"{col_letter}{data_point + 3}")

                avg_formula = f'=AVERAGE({",".join(formula_cells)})'
                stdev_formula = f'=STDEV.S({",".join(formula_cells)})'
                ws.write_formula(self.timeline_len + 5 + data_point, col_avg_rgb + color_offset, avg_formula)
                ws.write_formula(self.timeline_len + 5 + data_point, col_stdev + color_offset, stdev_formula)

        # Writing initial and final average RGB values
        # Initial average RGB
        ws.write(self.timeline_len + 5, col_initial_vs_final + 1, f'=C{initial_row}', self.center)
        ws.write(self.timeline_len + 5, col_initial_vs_final + 2, f'=D{initial_row}', self.center)
        ws.write(self.timeline_len + 5, col_initial_vs_final + 3, f'=E{initial_row}', self.center)

        # Final average RGB
        ws.write(self.timeline_len + 6, col_initial_vs_final + 1, f'=C{final_row}', self.center)
        ws.write(self.timeline_len + 6, col_initial_vs_final + 2, f'=D{final_row}', self.center)
        ws.write(self.timeline_len + 6, col_initial_vs_final + 3, f'=E{final_row}', self.center)

        # Writing the RGB color difference formula
        formula = (f'=SQRT((C${final_row} - C${initial_row})^2 + (D${final_row} - D${initial_row})^2 +'
                   f' (E${final_row} - E${initial_row})^2)')
        ws.write_formula(self.timeline_len + 8, col_initial_vs_final + 1, formula)

        # Writing the LAB color difference formula
        formula_lab = (
            f'=SQRT(({row_to_excel_col(col_lab + 1)}${final_row} - {row_to_excel_col(col_lab + 1)}${initial_row})^2 +'
            f' ({row_to_excel_col(col_lab + 2)}${final_row} - {row_to_excel_col(col_lab + 2)}${initial_row})^2 +'
            f' ({row_to_excel_col(col_lab + 3)}${final_row} - {row_to_excel_col(col_lab + 3)}${initial_row})^2)')
        ws.write_formula(self.timeline_len + 8, col_initial_vs_final + 2, formula_lab)

        # Calculate and write deviations for RGB
        deviations_rgb = StandardDeviationForEuclidianDistance(avg_rgb_per_time_point,
                                                               standard_deviation_rgb_per_time_point)
        # Write Weight differences
        ws.write(self.timeline_len + 9, col_initial_vs_final + 1,
                 deviations_rgb.direct_standard_deviation_propagation())
        # Write Error propagation
        ws.write(self.timeline_len + 10, col_initial_vs_final + 1, deviations_rgb.partial_derivative_method())
        # Write Monte Carlo
        ws.write(self.timeline_len + 11, col_initial_vs_final + 1, deviations_rgb.monte_carlo_simulation())

        ws.write(self.timeline_len + 12, col_initial_vs_final + 1, standard_deviation_new_rgb, self.center)
        # Calculate and write deviations for LAB
        deviations_lab = StandardDeviationForEuclidianDistance(avg_lab_per_time_point,
                                                               standard_deviation_lab_per_time_point)
        # Write Weight differences
        ws.write(self.timeline_len + 9, col_initial_vs_final + 2,
                 deviations_lab.direct_standard_deviation_propagation())
        # Write Error propagation
        ws.write(self.timeline_len + 10, col_initial_vs_final + 2, deviations_lab.partial_derivative_method())
        # Write Monte Carlo
        ws.write(self.timeline_len + 11, col_initial_vs_final + 2, deviations_lab.monte_carlo_simulation())
        ws.write(self.timeline_len + 12, col_initial_vs_final + 2, standard_deviation_new_lab, self.center)
        # Writing L* differences (0 - black, 100 - white). Final - initial. Positive - lightening, negative - darkening
        formula_lstar = f"={row_to_excel_col(col_lab + 1)}{final_row}-{row_to_excel_col(col_lab + 1)}{initial_row}"
        ws.write_formula(self.timeline_len + 8, col_initial_vs_final + 3, formula_lstar)

        # Calculate illuminant and write down the color temperature
        if self.settings['color_temperature'] is None:
            raise ColorTemperatureIsMissing(f"\nColor temperature is missing")

        ws.write(self.timeline_len + 10, col_initial_vs_final + 3, self.settings['color_temperature'])

        if self.iv_flag and self.data[device_name].get('iv_data'):
            ws.write(self.timeline_len + 12, col_initial_vs_final + 3,
                     f"=(({row_to_excel_col(col_iv_data + 2)}{final_row}"
                     f"-{row_to_excel_col(col_iv_data + 2)}{initial_row})/"
                     f"{row_to_excel_col(col_iv_data + 2)}{initial_row})*100")
        # # Write CIE76 Color difference (similar to Euclidian color difference)
        # formula_cie76 = (f'=SQRT(({row_to_excel_col(col_lab + 1)}${final_row} -'
        #                  f' {row_to_excel_col(col_lab + 1)}${initial_row})^2 +'
        #                  f' ({row_to_excel_col(col_lab + 2)}${final_row} -'
        #                  f' {row_to_excel_col(col_lab + 2)}${initial_row})^2 +'
        #                  f' ({row_to_excel_col(col_lab + 3)}${final_row} -'
        #                  f' {row_to_excel_col(col_lab + 3)}${initial_row})^2)')
        # ws.write_formula(self.timeline_len + 8, col_initial_vs_final + 3, formula_cie76)

        # Write headers for RGB_Euclidian
        self.write_center_across_selection(ws, (self.timeline_len + 3, col_rgb_euclid), 'RGB Euclidian')
        ws.write(self.timeline_len + 4, col_rgb_euclid, 'Color difference (n and n-1)', self.center)
        ws.write(self.timeline_len + 4, col_rgb_euclid + 1, 'Euclidian Norm (SRSS)', self.center)
        # Write headers for CMYK
        self.write_center_across_selection(ws, (self.timeline_len + 3, col_cmyk), 'CMYK', 4)
        ws.write(self.timeline_len + 4, col_cmyk, 'C', self.center)
        ws.write(self.timeline_len + 4, col_cmyk + 1, 'M', self.center)
        ws.write(self.timeline_len + 4, col_cmyk + 2, 'Y', self.center)
        ws.write(self.timeline_len + 4, col_cmyk + 3, 'K', self.center)

        # Write headers for HSL
        self.write_center_across_selection(ws, (self.timeline_len + 3, col_hsl), 'HSL')
        ws.write(self.timeline_len + 4, col_hsl, 'H', self.center)
        ws.write(self.timeline_len + 4, col_hsl + 1, 'S', self.center)
        ws.write(self.timeline_len + 4, col_hsl + 2, 'L', self.center)

        # Write headers for HSV
        self.write_center_across_selection(ws, (self.timeline_len + 3, col_hsv), 'HSV')
        ws.write(self.timeline_len + 4, col_hsv, 'H', self.center)
        ws.write(self.timeline_len + 4, col_hsv + 1, 'S', self.center)
        ws.write(self.timeline_len + 4, col_hsv + 2, 'V', self.center)

        # Write headers for CIELAB ΔE*
        self.write_center_across_selection(ws, (self.timeline_len + 3, col_lab), 'CIELAB ΔE*')
        ws.write(self.timeline_len + 4, col_lab, 'L*', self.center)
        ws.write(self.timeline_len + 4, col_lab + 1, 'a*', self.center)
        ws.write(self.timeline_len + 4, col_lab + 2, 'b*', self.center)

        # Write headers for CIELAB ΔE* standard deviation
        self.write_center_across_selection(ws, (self.timeline_len + 3, col_lab_std_dev),
                                           'CIELAB ΔE* standard deviation')
        ws.write(self.timeline_len + 4, col_lab_std_dev, 'L*', self.center)
        ws.write(self.timeline_len + 4, col_lab_std_dev + 1, 'a*', self.center)
        ws.write(self.timeline_len + 4, col_lab_std_dev + 2, 'b*', self.center)

        # Write headers for CIELAB ΔE* delta
        self.write_center_across_selection(ws, (self.timeline_len + 3, col_lab_delta), 'CIELAB ΔE* delta')
        ws.write(self.timeline_len + 4, col_lab_delta, 'L*', self.center)
        ws.write(self.timeline_len + 4, col_lab_delta + 1, 'a*', self.center)
        ws.write(self.timeline_len + 4, col_lab_delta + 2, 'b*', self.center)

        for idx, (colors, deviations_rgb, avg_lab, lab_std_dev) in enumerate(
                zip(avg_rgb_per_time_point, standard_deviation_rgb_per_time_point, avg_lab_per_time_point,
                    standard_deviation_lab_per_time_point)):
            avg_r, avg_g, avg_b, avg_y = colors
            row_to_write = self.timeline_len + 5 + idx

            # Convert average RGB to CMYK, HSL, and HSV
            avg_cmyk = rgb_to_cmyk(avg_r, avg_g, avg_b)
            avg_hsl = rgb_to_hsl(avg_r, avg_g, avg_b)
            avg_hsv = rgb_to_hsv(avg_r, avg_g, avg_b)

            ws.write_row(row_to_write, col_lab_std_dev, lab_std_dev, self.center)

            # Write these values into the worksheet
            ws.write_row(row_to_write, col_cmyk, avg_cmyk, self.center)
            ws.write_row(row_to_write, col_hsl, avg_hsl, self.center)
            ws.write_row(row_to_write, col_hsv, avg_hsv, self.center)
            ws.write_row(row_to_write, col_lab, avg_lab, self.center)

            # Write RGB_Euclidian calculations
            if idx != 0:
                ws.write_formula(row_to_write, col_rgb_euclid,
                                 f"=SQRT("
                                 f"({row_to_excel_col(col_avg_rgb + 1)}{row_to_write}"
                                 f" - {row_to_excel_col(col_avg_rgb + 1)}{row_to_write + 1})^2 +"
                                 f"({row_to_excel_col(col_avg_rgb + 2)}{row_to_write}"
                                 f" - {row_to_excel_col(col_avg_rgb + 2)}{row_to_write + 1})^2 +"
                                 f"({row_to_excel_col(col_avg_rgb + 3)}{row_to_write}"
                                 f" - {row_to_excel_col(col_avg_rgb + 3)}{row_to_write + 1})^2"
                                 f")")
            ws.write_formula(row_to_write, col_rgb_euclid + 1,
                             f"=SQRT({row_to_excel_col(col_avg_rgb + 1)}{row_to_write + 1}^2 +"
                             f"{row_to_excel_col(col_avg_rgb + 2)}{row_to_write + 1}^2 +"
                             f"{row_to_excel_col(col_avg_rgb + 3)}{row_to_write + 1}^2)")
            for lab in range(3):
                cell_lab = row_to_excel_col(col_lab + lab + 1)
                previous_row = row_to_write + 1 if idx == 0 else row_to_write
                ws.write_formula(row_to_write, col_lab_delta + lab,
                                 f'={cell_lab}{row_to_write + 1}-{cell_lab}{previous_row}')

            # Write Y values
            if self.settings['prediction_flag']:
                ws.write(row_to_write, col_yellow, avg_y)
                if idx == 0:
                    continue
                y_letter = row_to_excel_col(col_yellow + 1)
                ws.write_formula(row_to_write, col_yellow + 1,
                                 f'=ABS(({y_letter}{row_to_write}-'
                                 f'{y_letter}{row_to_write + 1})/{y_letter}{row_to_write})*100')
                ws.write_formula(row_to_write, col_yellow + 2,
                                 f'={y_letter}{row_to_write}-{y_letter}{row_to_write + 1}')
            # Write average RGB values calculated by python for debugging
            # ws.write_row(row_to_write, 50, [avg_r, avg_g, avg_b])

        lab_df = pd.DataFrame(avg_lab_per_time_point, columns=['L*', 'a*', 'b*'])
        self.data[device_name]['CIELAB_df'] = lab_df
        self.cielab_color_difference(ws=ws, device_name=device_name)

        if self.settings['prediction_flag']:
            ws.write(self.timeline_len + 3, col_yellow, 'Yellow color')
            ws.write(self.timeline_len + 4, col_yellow, 'Y')
            ws.write(self.timeline_len + 3, col_yellow + 1, 'Color change (how different each next compare to the '
                                                            'previous one)')
            ws.write(self.timeline_len + 4, col_yellow + 1, 'Color difference (%)')
            ws.write(self.timeline_len + 4, col_yellow + 2, 'Color difference')

    def cielab_color_difference(self, ws: Worksheet, device_name: str) -> None:
        """
        Write Color Differences values of CIELAB,
        including various methods like CIE 1976, CMC, CIE 1994, DIN99, and CIE 2000.

        :param ws: The xlsxwriter worksheet object where formulas are to be written.
        :param device_name: The name of the device for which the sheet is being created.
        :return: None
        """
        col_color_dif = self.settings['Starting columns']['Color Difference']
        cielab_df = self.data[device_name]['CIELAB_df']
        initial_lab = cielab_df.iloc[0]
        final_lab = cielab_df.iloc[-1]

        # CIE 1976
        # Return the difference delta E76 between two given CIE L*a*b* colourspace arrays using CIE 1976 recommendation.
        # Source: Bruce Lindbloom. Delta E (CIE 1976). http://brucelindbloom.com/Eqn_DeltaE_CIE76.html, 2003.
        e1976 = colour.difference.delta_E_CIE1976(Lab_1=initial_lab, Lab_2=final_lab)

        # CIE 1994
        # Return the difference delta E94 between two given CIE L*a*b* colourspace arrays using CIE 1994 recommendation.
        # Source: Bruce Lindbloom. Delta E (CIE 1994). http://brucelindbloom.com/Eqn_DeltaE_CIE94.html, 2011.
        e1994 = colour.difference.delta_E_CIE1994(Lab_1=initial_lab, Lab_2=final_lab, textiles=False)
        e1994_textile = colour.difference.delta_E_CIE1994(Lab_1=initial_lab, Lab_2=final_lab, textiles=True)

        # CIE 2000
        # Return the difference delta E00 between two given CIE L*a*b* colourspace arrays using CIE 2000 recommendation.
        # Source: Manuel Melgosa. CIE / ISO new standard: CIEDE2000. 2013; Gaurav Sharma, Wencheng Wu, and Edul N.
        # Dalal. The CIEDE2000 color-difference formula: Implementation notes, supplementary test data, and
        # mathematical observations. Color Research & Application, 30(1):21–30, February 2005. doi:10.1002/col.20070.
        e2000 = colour.difference.delta_E_CIE2000(Lab_1=initial_lab, Lab_2=final_lab, textiles=False)
        e2000_textile = colour.difference.delta_E_CIE2000(Lab_1=initial_lab, Lab_2=final_lab, textiles=True)

        # CMC
        # Return the difference delta ECMC between two given CIE L*a*b* colourspace arrays using Colour Measurement
        # Committee recommendation.
        # The quasimetric has two parameters: Lightness (l) and chroma (c), allowing the users to weight the
        # difference based on the ratio of l:c. Commonly used values are 2:1 for acceptability and 1:1 for
        # the threshold of imperceptibility.
        # Source: Bruce Lindbloom. Delta E (CMC). http://brucelindbloom.com/Eqn_DeltaE_CMC.html, 2009.
        cmc_acceptability = colour.difference.delta_E_CMC(Lab_1=initial_lab, Lab_2=final_lab, l=2, c=1)
        cmc_imperceptibility = colour.difference.delta_E_CMC(Lab_1=initial_lab, Lab_2=final_lab, l=1, c=1)

        # DIN99
        # Return the difference delta E76 between two given CIE L*a*b* colourspace arrays using DIN99 formula.
        # Source: ASTM International. ASTM D2244-07 - Standard Practice for Calculation of Color Tolerances and Color
        # Differences from Instrumentally Measured Color Coordinates. 2007. doi:10.1520/D2244-16.
        din99 = colour.difference.delta_E_DIN99(Lab_1=initial_lab, Lab_2=final_lab, textiles=False)
        din99_textile = colour.difference.delta_E_DIN99(Lab_1=initial_lab, Lab_2=final_lab, textiles=True)

        self.write_center_across_selection(ws, (self.timeline_len + 3, col_color_dif),
                                           'Color Difference, Delta E', 9)
        ws.write_row(self.timeline_len + 4, col_color_dif, self.delta_e_headers, self.center)
        color_differences = (e1976, e1994, e1994_textile, e2000, e2000_textile, cmc_acceptability, cmc_imperceptibility,
                             din99, din99_textile)

        for i, delta_e in enumerate(color_differences):
            ws.write(self.timeline_len + 5, col_color_dif + i, delta_e)

    def get_average_rgb_values_per_time_point(self, device_name: str) -> \
            tuple[
                list[tuple[float, ...]],
                list[tuple[float, ...]],
                list[tuple[float, ...]],
                list[tuple[float, ...]],
                float,
                float]:
        """
        Calculate the average R, G, B, and LAB values per time point from the data dictionary,
        as well as their standard deviations.

        :param device_name: The name of the device for which the sheet is being created.
        :return: A tuple containing lists of tuples with the average R, G, B, LAB values,
                 their standard deviations, and average LAB values for each time point.
        """
        sum_rgb = defaultdict(lambda: [0, 0, 0])
        sum_squares_rgb = defaultdict(lambda: [0, 0, 0])
        count_rgb = defaultdict(int)

        # Convert RGB to LAB and accumulate for each time point
        sum_lab = defaultdict(lambda: [0, 0, 0])
        sum_squares_lab = defaultdict(lambda: [0, 0, 0])
        set_initial_rgb, set_final_rgb = [], []
        set_initial_lab, set_final_lab = [], []
        # Sort the keys
        sorted_keys = natsorted(self.data[device_name]['RGB_data'].keys())
        # Create a new dictionary with sorted keys
        sorted_dict = {k: self.data[device_name]['RGB_data'][k] for k in sorted_keys}
        for time_point_str, area_data in sorted_dict.items():
            # if time_point_str == '0' or time_point_str == f'{self.timeline_len - 1}':
            #     ic(time_point_str, area_data)
            for area_value in area_data.values():
                rgb_value = area_value.get('RGB')
                if rgb_value and all(v is not None for v in rgb_value.values()):
                    r, g, b = rgb_value['R'], rgb_value['G'], rgb_value['B']
                    sum_rgb[time_point_str][0] += r
                    sum_rgb[time_point_str][1] += g
                    sum_rgb[time_point_str][2] += b
                    sum_squares_rgb[time_point_str][0] += r ** 2
                    sum_squares_rgb[time_point_str][1] += g ** 2
                    sum_squares_rgb[time_point_str][2] += b ** 2
                    count_rgb[time_point_str] += 1

                    # Convert RGB to LAB
                    l, a, b_ = rgb_to_lab(r, g, b, illuminant=self.illuminant)
                    sum_lab[time_point_str][0] += l
                    sum_lab[time_point_str][1] += a
                    sum_lab[time_point_str][2] += b_
                    sum_squares_lab[time_point_str][0] += l ** 2
                    sum_squares_lab[time_point_str][1] += a ** 2
                    sum_squares_lab[time_point_str][2] += b_ ** 2
                    # Add to initial and final sets based on condition
                    if time_point_str == '0':
                        set_initial_rgb.append([r, g, b])
                        set_initial_lab.append([l, a, b_])
                    elif time_point_str == f'{self.timeline_len - 1}':
                        set_final_rgb.append([r, g, b])
                        set_final_lab.append([l, a, b_])
        # Calculate the Euclidian distance and standard deviation using new approach
        distances_new_rgb = np.linalg.norm(np.array(set_final_rgb) - np.array(set_initial_rgb), axis=1)
        distances_new_lab = np.linalg.norm(np.array(set_final_lab) - np.array(set_initial_lab), axis=1)
        # avg_distance_new_rgb = np.mean(distances_new_rgb)
        # avg_distance_new_lab = np.mean(distances_new_lab)
        std_distance_new_rgb = np.std(distances_new_rgb, ddof=1)
        std_distance_new_lab = np.std(distances_new_lab, ddof=1)

        avg_rgb_per_time_point, avg_lab_per_time_point = [], []
        standard_deviation_rgb, standard_deviation_lab = [], []

        for time_point_str, _ in sum_rgb.items():
            count = count_rgb[time_point_str]

            # Average RGB and Yellow calculation
            avg_r, avg_g, avg_b = [sum_rgb[time_point_str][i] / count for i in range(3)]
            avg_rgb_per_time_point.append((avg_r, avg_g, avg_b, 255 - avg_b))

            # Average LAB calculation
            avg_l, avg_a, avg_b = [sum_lab[time_point_str][i] / count for i in range(3)]
            avg_lab_per_time_point.append((avg_l, avg_a, avg_b))

            if count > 1:
                stdev_rgb = [math.sqrt((sum_squares_rgb[time_point_str][i] -
                                        sum_rgb[time_point_str][i] ** 2 / count) / (count - 1)) for i in range(3)]

                stdev_lab = [math.sqrt((sum_squares_lab[time_point_str][i] -
                                        sum_lab[time_point_str][i] ** 2 / count) / (count - 1)) for i in range(3)]
            else:
                stdev_rgb = [0.0, 0.0, 0.0]
                stdev_lab = [0.0, 0.0, 0.0]
            standard_deviation_rgb.append(tuple(stdev_rgb))
            standard_deviation_lab.append(tuple(stdev_lab))

        self.data[device_name]['Average_RGB'] = avg_rgb_per_time_point
        self.data[device_name]['Average_LAB'] = avg_lab_per_time_point

        # Create DataFrames for Yellow and LAB values and store them
        yellow_df = pd.DataFrame([y for _, _, _, y in avg_rgb_per_time_point], columns=['Average_Yellow'])
        lab_df = pd.DataFrame(avg_lab_per_time_point, columns=['L*', 'a*', 'b*'])
        self.data[device_name]['Yellow_df'] = yellow_df
        self.data[device_name]['LAB_df'] = lab_df

        return (avg_rgb_per_time_point, standard_deviation_rgb, avg_lab_per_time_point, standard_deviation_lab,
                std_distance_new_rgb, std_distance_new_lab)

    def write_iv_data(self, ws: Worksheet, data: dict) -> None:
        """
        Write IV data into the Excel worksheet.

        :param ws: The xlsxwriter worksheet object where IV data is to be written.
        :param data: A dictionary with the raw data
        :return: None
        """
        col_iv = self.settings['Starting columns']['IV data']
        sweep_key = self.settings['sweep_key']
        self.write_center_across_selection(ws, (self.timeline_len + 3, col_iv), 'IV parameters', 8)

        ws.write_row(self.timeline_len + 4, col_iv, self.iv_headers_short, self.center)

        # Start writing data from the row next to headers
        start_row = self.timeline_len + 5
        for time_point, time_data in data['iv_data'].items():
            raw_data = []

            if sweep_key in time_data['Parameters']:
                for header in self.iv_headers_short:
                    # Mapping shortened headers to full parameter names
                    full_header = self.iv_map_dict.get(header)
                    param_value = time_data['Parameters'][sweep_key].get(full_header, "N/A")
                    raw_data.append(param_value)

                ws.write_row(start_row, col_iv, raw_data)
                start_row += 1  # Move to the next row for the next time point

    def add_color_plots(self, ws: Worksheet, device_name: str) -> None:
        """
        Add RGB for areas, RGB average, CMYK, HSL, and HSV plots into the Excel worksheet.

        :param ws: The xlsxwriter worksheet object where plots are to be added.
        :param device_name: The name of the device for which the sheet is being created.
        :return: None
        """
        self.rgb_chart_copies[device_name] = None
        # Generate and insert RGB scatters for each area and for the average data
        for i in range(1, 11):
            scatter = self.plotter.rgb_scatter(device_name=device_name, column_start=i, data_start=2,
                                               data_end=self.timeline_len + 1)
            ws.insert_chart(self.row_first_plot + self.chart_vertical_spacing, (i - 1) * self.chart_horizontal_spacing,
                            scatter)
        scatter_average = self.plotter.rgb_scatter(device_name=device_name, column_start=1,
                                                   data_start=self.timeline_len + 5,
                                                   data_end=self.timeline_len * 2 + 4, title='Average')
        scatter_average_copy = self.plotter.rgb_scatter(device_name=device_name, column_start=1,
                                                        data_start=self.timeline_len + 5,
                                                        data_end=self.timeline_len * 2 + 4, title='Average')
        self.rgb_chart_copies[device_name] = scatter_average_copy
        ws.insert_chart(self.row_first_plot, 0, scatter_average)

        # CIELAB ΔE*
        lab_chart = self.plotter.lab_scatter_chart(device_name=device_name, data_start=self.timeline_len + 5,
                                                   data_end=self.timeline_len * 2 + 4)
        ws.insert_chart(self.row_first_plot + self.chart_vertical_spacing * 2, 0, lab_chart)

        # CIELAB ΔE* delta
        lab_change_chart = self.plotter.lab_delta_scatter_chart(device_name=device_name,
                                                                data_start=self.timeline_len + 5,
                                                                data_end=self.timeline_len * 2 + 4)
        lab_change_chart_copy = self.plotter.lab_delta_scatter_chart(device_name=device_name,
                                                                     data_start=self.timeline_len + 5,
                                                                     data_end=self.timeline_len * 2 + 4)
        self.lab_charts_copy[device_name] = lab_change_chart_copy
        ws.insert_chart(self.row_first_plot + self.chart_vertical_spacing * 2, self.chart_horizontal_spacing * 5,
                        lab_change_chart)

        # Generate and insert CMYK scatter for average CMYK
        cmyk_scatter = self.plotter.cmyk_scatter(device_name=device_name, data_start=self.timeline_len + 5,
                                                 data_end=self.timeline_len * 2 + 4)
        ws.insert_chart(self.row_first_plot + self.chart_vertical_spacing * 2, self.chart_horizontal_spacing,
                        cmyk_scatter)

        # Generate and insert HSL and HSV scatters
        for i, mode in enumerate(['HSL', 'HSV'], 2):
            hsl_hsv_scatter = self.plotter.hsl_hsv_scatter(device_name=device_name, data_start=self.timeline_len + 5,
                                                           data_end=self.timeline_len * 2 + 4, color_mode=mode)
            ws.insert_chart(self.row_first_plot + self.chart_vertical_spacing * 2, self.chart_horizontal_spacing * i,
                            hsl_hsv_scatter)

        # Initial vs Final
        initial_vs_final = self.plotter.initial_vs_final_column_chart(device_name=device_name,
                                                                      start_row=self.timeline_len + 5)
        ws.insert_chart(self.row_first_plot + self.chart_vertical_spacing * 2, self.chart_horizontal_spacing * 4,
                        initial_vs_final)

    def add_iv_plots(self, ws: Worksheet, device_name: str) -> None:
        """
        Add IV data plots into the Excel worksheet.

        :param ws: The xlsxwriter worksheet object where plots are to be added.
        :param device_name: The name of the device for which the sheet is being created.
        :return: None
        """
        self.iv_chart_details[device_name] = {}
        for i, key in enumerate(self.iv_map_dict.keys()):
            iv_data_plot = self.iv_plotter.create_single_iv_plot(device_name=device_name, column=i,
                                                                 data_start=self.timeline_len + 5,
                                                                 data_end=self.timeline_len * 2 + 4, name=key)
            iv_data_plot_copy = self.iv_plotter.create_single_iv_plot(device_name=device_name, column=i,
                                                                      data_start=self.timeline_len + 5,
                                                                      data_end=self.timeline_len * 2 + 4, name=key)
            self.iv_chart_details[device_name][i] = iv_data_plot_copy
            ws.insert_chart(self.row_first_plot, self.chart_horizontal_spacing * (2 + i), iv_data_plot)

    def write_prediction_add_plots(self, ws: Worksheet, device_name: str) -> None:
        """
        Write IV data predictions based on the yellow color of the die into the Excel worksheet.

        :param ws: The xlsxwriter worksheet object where IV data is to be written.
        :param device_name: The name of the device for which the sheet is being created.
        :return: None
        """
        # Create border formats
        border_thickness = self.settings['ChartsCreator']['colored_border_thickness']
        top_border_format = self.workbook.add_format(
            {'top': border_thickness, 'top_color': 'red', 'left': border_thickness, 'left_color': 'red',
             'right': border_thickness, 'right_color': 'red'})
        bottom_border_format = self.workbook.add_format(
            {'bottom': border_thickness, 'bottom_color': 'red', 'left': border_thickness, 'left_color': 'red',
             'right': border_thickness, 'right_color': 'red'})
        left_right_border_format = self.workbook.add_format(
            {'left': border_thickness, 'left_color': 'red', 'right': border_thickness, 'right_color': 'red'})
        self.iv_prediction_chart_copies[f'{device_name}'] = {}
        for num_of_points in range(self.prediction_start, self.prediction_end):
            # Perform the prediction and store the result in a dictionary
            prediction_result = self.predictor.perform_prediction(num_of_points)

            # Extract headers and data
            prediction_headers = list(prediction_result.keys())
            prediction_data = list(prediction_result.values())

            column_offset = len(prediction_headers) + 1 if len(
                prediction_headers) >= self.chart_horizontal_spacing else self.chart_horizontal_spacing
            column = column_offset * (num_of_points - self.prediction_start)
            start_row = self.timeline_len * 2 + 8 + self.chart_vertical_spacing * 4
            end_row = start_row + num_of_points
            self.write_center_across_selection(ws, (start_row - 2, column),
                                               f'Prediction based on num of points: {num_of_points}',
                                               len(prediction_headers))
            ws.write_row(start_row - 1, column, prediction_headers, self.center)

            for i, value in enumerate(prediction_data):
                ws.write_column(start_row, column + i, value, self.center)

            # Apply top border
            ws.conditional_format(start_row + self.settings['prediction_start_point'], column,
                                  start_row + self.settings['prediction_start_point'], column,
                                  {'type': 'no_errors', 'format': top_border_format})
            # Apply bottom border
            ws.conditional_format(end_row - 1, column, end_row - 1, column,
                                  {'type': 'no_errors', 'format': bottom_border_format})
            # Apply left and right borders for all cells between top and bottom
            ws.conditional_format(start_row + 1 + self.settings['prediction_start_point'], column, end_row - 2, column,
                                  {'type': 'no_errors', 'format': left_right_border_format})

            prediction_complex_chart = (
                self.predictor.create_complex_iv_plot(device_name=device_name,
                                                      j_row_start=self.timeline_len + 5,
                                                      j_row_end=self.timeline_len * 2 + 4,
                                                      row_start=start_row,
                                                      column=column))
            prediction_complex_chart_copy = (
                self.predictor.create_complex_iv_plot(device_name=device_name,
                                                      j_row_start=self.timeline_len + 5,
                                                      j_row_end=self.timeline_len * 2 + 4,
                                                      row_start=start_row,
                                                      column=column))

            self.iv_prediction_chart_copies[f'{device_name}'][
                num_of_points - self.prediction_start] = prediction_complex_chart_copy
            ws.insert_chart(self.timeline_len * 2 + 6 + self.chart_vertical_spacing * 3,
                            self.chart_horizontal_spacing * (num_of_points - self.prediction_start),
                            prediction_complex_chart)

    def insert_rgb_charts_in_row(self, device_name: str, row: int, col_start: int) -> None:
        """
        Inserts RGB charts in a given row.

        :param device_name: A name of the device.
        :param row: Row number.
        :param col_start: Starting column number.
        :return: Next available column after inserting charts.
        """
        device = self.rgb_chart_copies.get(device_name, None)
        lab_chart = self.lab_charts_copy.get(device_name, None)
        if device is None:
            return
        self.worksheet_main.insert_chart(row * self.chart_vertical_spacing,
                                         col_start * self.chart_horizontal_spacing, device)
        if self.settings['LAB_delta_flag']:
            self.worksheet_main.insert_chart((row + self.batches) * self.chart_vertical_spacing,
                                             col_start * self.chart_horizontal_spacing, lab_chart)

    def insert_iv_prediction_charts_in_row(self, device_name: str, row: int, col_start: int) -> None:
        """
        Inserts IV prediction charts in a given row.

        :param device_name: A name of the device.
        :param row: Row number.
        :param col_start: Starting column number.
        """
        device: Optional[Dict[int, ChartScatter]] = self.iv_prediction_chart_copies.get(device_name, None)
        if device is None:
            return
        for num_of_points in range(self.prediction_start, self.prediction_end):
            self.worksheet_main.insert_chart(
                (row + num_of_points - self.prediction_start) * self.chart_vertical_spacing,
                col_start * self.chart_horizontal_spacing,
                device[num_of_points - self.prediction_start])

    def insert_iv_charts_in_row(self, device_name: str, row: int, col_start: int) -> None:
        """
        Inserts IV charts in a given row.

        :param device_name: A name of the device.
        :param row: Row number.
        :param col_start: Starting column number.
        :return: Next available column after inserting charts.
        """
        device: Optional[Dict[int, ChartScatter]] = self.iv_chart_details.get(device_name, None)
        if device is None:
            return
        for i, _ in enumerate(self.iv_map_dict.keys()):
            self.worksheet_main.insert_chart((row + i) * self.chart_vertical_spacing,
                                             col_start * self.chart_horizontal_spacing,
                                             device[i])

    def add_charts_in_main_sheet_and_fill_table_sheet(self) -> None:
        """
        Adds charts to the main worksheet.
        Set Table sheet (optional)

        :param: None.
        :return: None.
        """
        if self.settings['Table_tab'] is not None:
            self.table_sheet_processor(headers=True)
        total_samples = len(self.all_samples_list)
        device_index = 0
        samples_number_per_row = self.samples_number_per_row
        # Keep space for the LAB delta scatters
        ivs_starting_row = self.batches * 2 if self.settings['LAB_delta_flag'] else self.batches
        for row in range(self.batches):
            if row == self.batches - 1:
                samples_number_per_row += self.remainder
            for column in range(samples_number_per_row):
                device_name = self.all_samples_list[device_index]
                if device_index == total_samples:
                    break
                self.insert_rgb_charts_in_row(device_name, row, column)
                if self.settings['Table_tab'] is not None:
                    self.table_sheet_processor(row=row, col=column, device_name=device_name, headers=False)
                if self.settings['prediction_flag']:
                    self.insert_iv_prediction_charts_in_row(device_name, ivs_starting_row, column)
                    self.insert_iv_charts_in_row(device_name,
                                                 ivs_starting_row + self.prediction_end - self.prediction_start, column)
                elif self.iv_flag:
                    self.insert_iv_charts_in_row(device_name, ivs_starting_row, column)

                device_index += 1

    def table_sheet_processor(self, headers: bool = False, row: int = None, col: int = None, device_name: str = None) \
            -> None:
        """
        Fill the tables and values into the Table sheet

        :param headers: Boolean flag to fill headers.
        :param row: An integer representing the row to place the value.
        :param col: An integer representing the column to place the value.
        :param device_name: A name of the device.
        False by default.
        :return: None.
        """
        # Write headers only ones
        if headers:
            self.write_center_across_selection(self.table_sheet, (0, 1),
                                               'Color difference (RGB Euclidian distance) initial vs final',
                                               self.samples_number_per_row)
            self.write_center_across_selection(self.table_sheet, (self.batches + 4, 1),
                                               'Final L* - Initial L*. Positive - lightening, negative - darkening',
                                               self.samples_number_per_row)
            for ind, header in enumerate(self.delta_e_headers, 2):
                self.write_center_across_selection(self.table_sheet, ((self.batches + 4) * ind, 1),
                                                   f'Colour Difference {header} (Initial vs Final)',
                                                   self.samples_number_per_row)
            for iteration in range(len(self.delta_e_headers) + 2):
                formatting = {"type": "3_color_scale", "mid_type": "percent", "min_color": "#00ff00",
                              "mid_color": "#ffff00",
                              "max_color": "#ff0000"}
                if iteration == 1:  # Specific formatting for the second type, which is L* values difference
                    negative_value_format = {'type': 'cell', 'criteria': 'less than', 'value': 0,
                                             'format': self.workbook.add_format({'font_color': 'red'})}
                    self.table_sheet.conditional_format((self.batches + 4) * iteration,
                                                        1,
                                                        (self.batches + 4) * iteration + self.batches + 1,
                                                        1 + self.samples_number_per_row + self.remainder,
                                                        negative_value_format)
                    formatting = {
                        'type': '2_color_scale',
                        'min_type': 'num', 'min_value': 0, 'min_color': '#000080',
                        'max_type': 'num', 'max_value': 0, 'max_color': '#FFFF00'}
                self.table_sheet.conditional_format((self.batches + 4) * iteration,
                                                    1,
                                                    (self.batches + 4) * iteration + self.batches + 1,
                                                    1 + self.samples_number_per_row + self.remainder, formatting)
            return
        # Populate values
        cell_rgb_euclidian = (f"{row_to_excel_col(self.settings['Starting columns']['Initial vs final'] + 2)}"
                              f"{len(self.data[device_name]['Timeline']) + 9}")
        cell_lstar = (f"{row_to_excel_col(self.settings['Starting columns']['Initial vs final'] + 4)}"
                      f"{len(self.data[device_name]['Timeline']) + 9}")
        if row == 0:
            for device_name_to_cell in range(len(self.delta_e_headers) + 2):
                self.table_sheet.write(row + 1 + (self.batches + 4) * device_name_to_cell, col + 1,
                                       remove_pattern(s=device_name), self.center)
                if 'Filters plus sc' in self.highest_path:
                    self.table_sheet.write(row + 1 + (self.batches + 4) * device_name_to_cell, col + 1,
                                           map_name(s=device_name), self.center)
        if col == 0:
            for device_type_counter in range(len(self.delta_e_headers) + 2):
                self.table_sheet.write(row + 2 + (self.batches + 4) * device_type_counter, col, row + 1)
                if 'Filters plus sc' in self.highest_path:
                    device_type = 'Filer' if row == 0 else 'DSSC'
                    self.table_sheet.write(row + 2 + (self.batches + 4) * device_type_counter, col, device_type)
        self.table_sheet.write(row + 2, col + 1, f"='{device_name}'!{cell_rgb_euclidian}")
        self.table_sheet.write(row + 6 + self.batches, col + 1, f"='{device_name}'!{cell_lstar}")
        for color_difference in range(len(self.delta_e_headers)):
            cell_delta_e = \
                (f"{row_to_excel_col(self.settings['Starting columns']['Color Difference'] + 1 + color_difference)}"
                 f"{len(self.data[device_name]['Timeline']) + 6}")
            self.table_sheet.write(row + 2 + (self.batches + 4) * (color_difference + 2), col + 1,
                                   f"='{device_name}'!{cell_delta_e}")
