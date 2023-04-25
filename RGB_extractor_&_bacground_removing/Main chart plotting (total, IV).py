import colorsys
import json
import os
import sys
import time
from datetime import date
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import xlsxwriter
from icecream import ic
from tqdm import tqdm

# from Predicting import prediction  <- this is not published yet, so it will be upcoming later

# Set pandas' console output width
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# Some initial settings. Check highest_path before each run
start_time = time.time()
today = date.today()
rgb_extension = '.json'  # .xlsx for a previous versions
highest_path = "path/to/your/folder"
if not highest_path.endswith('/'):
    highest_path = highest_path + '/'
iv_parameters = highest_path + 'IV parameters/'
Timeline = 'Timeline'  # Extension part is about to be added in Timeline checking part
full_path_to_file = highest_path + str(f"RGB_plotting/{str(today)} {highest_path.split('/')[-2]} Total RGB and all "
                                       f"others.xlsx")
prediction_flag = 0  # 1 if is prediction and 0 otherwise
num_of_points = 6
ic.configureOutput(prefix='')

RGB_SCALE = 255
CMYK_SCALE = 100

chart_setback = 12
samples_number = 1

# Adjustments of Excel formatting
marker_size = 4
axis_size = 10
title_size = 10.5
num_size = 8
legend_size = 8
max_time = 10
rgb_y_min = 0
rgb_y_max = 255
rgb_line_width = 2
rgb_line_none_appear = None
rgb_title_none = False
rgb_legend_none = False
rgb_axis_none = False
rgb_x_axis_name = 't(h)'
rgb_y_axis_name = 'RGB'

text_colour = '#595959'
axis_colour = '#BFBFBF'
error_bar_type = 'custom'
rgb_scatter_position = 6

major_unit = max_time / 4
minor_unit = major_unit / 2
rgb_chart_x_scale = 0.7
rgb_chart_y_scale = 0.7
rgb_column_chart_x_scale = 0.4
rgb_column_chart_y_scale = 0.6

plot_area_x = 0.8
plot_area_y = 0.1
plot_area_width = 0.8
plot_area_height = 0.7

legend_area_x = 0.75
legend_area_y = 0.45
legend_area_width = 0.25
legend_area_height = 0.3


# Prediction equations are here.


@lru_cache(maxsize=5)
def timeline_detector(sample_name):  # Checking if the file exist
    flag = '.xlsx'  # Here is the extension for timeline file.
    timeline = Path(highest_path + Timeline + flag)  # Specify here the file with timepoints
    if timeline.is_file():
        df = pd.read_excel(timeline, header=None, na_values=["NA"])
        return df
    else:
        print(f'Check the {timeline}')


timeline_len = len(timeline_detector('Detecting the number of photo sessions')) + 5

# Dict with 4 RGB plots settings. Could be adjusted
specs = {'d0': {'counter': 2, 'error': {'0': 'AA', '1': 'AA', '2': 'AA'}, 'name': {'1': 'Area 1', '2': ''},
                'position': f'A{timeline_len + chart_setback}'},
         'd1': {'counter': 6, 'error': {'0': 'AA', '1': 'AA', '2': 'AA'}, 'name': {'1': 'Area 2', '2': ''},
                'position': f'G{timeline_len + chart_setback}'},
         'd2': {'counter': 10, 'error': {'0': 'AA', '1': 'AA', '2': 'AA'}, 'name': {'1': 'Area 3', '2': ''},
                'position': f'M{timeline_len + chart_setback}'},
         'd3': {'counter': 14, 'error': {'0': 'S', '1': 'T', '2': 'U'}, 'name': {'1': 'Average', '2': ''},
                'position': f'A{timeline_len}'},
         'd4': {'counter': 18, 'name': {'1': "Standard deviation with Bessel's correction", '2': ''}},
         'd5': {'counter': 23, 'name': {'0': "Initial values versus final ones", '1': '', '2': ''}}}

# Dict for markers of each series in RGB plot
rgb_plot_lines = {'0': {'counter': 0, 'colour': 'red', 'marker': 'plus', 'transparency': 0},
                  '1': {'counter': 1, 'colour': 'green', 'marker': 'x', 'transparency': 25},
                  '2': {'counter': 2, 'colour': 'blue', 'marker': 'short_dash', 'transparency': 50}}

#  CMYK chart
cmyk_lines = {'0': {'counter': 0, 'colour': '#00FFFF', 'marker': 'triangle'},
              '1': {'counter': 1, 'colour': '#FF00FF', 'marker': 'circle'},
              '2': {'counter': 2, 'colour': '#FFFF00', 'marker': 'x'},
              '3': {'counter': 3, 'colour': 'black', 'marker': 'square'}}

# Dict for CMYK, HSL, HSV curves
colors = {'cs_0': {'column': '', 'name': {'1': 'CMYK', '2': 'CMYK'}, 'unit': 'CMYK',
                   'position': f'A{timeline_len + chart_setback * 2}'},
          'cs_1': {'column': 32, 'name': {'1': 'HSL', '2': 'HSL'}, 'unit': {'1': 'H', '2': 'SL'},
                   'position': f'G{timeline_len + chart_setback * 2}', 'axis': {'0': 1, '1': 0, '2': 0}},
          'cs_2': {'column': 36, 'name': {'1': 'HSV', '2': 'HSV'}, 'unit': {'1': 'H', '2': 'SV'},
                   'position': f'M{timeline_len + chart_setback * 2}', 'axis': {'0': 1, '1': 0, '2': 0}}}


def rgb_to_cmyk(r, g, b):
    if (r, g, b) == (0, 0, 0):
        # black
        return 0, 0, 0, CMYK_SCALE
    # rgb [0,255] -> cmy [0,1]
    c = 1 - r / RGB_SCALE
    m = 1 - g / RGB_SCALE
    y = 1 - b / RGB_SCALE
    # extract out k [0, 1]
    min_cmy = min(c, m, y)
    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)
    k = min_cmy
    # rescale to the range [0,CMYK_SCALE]
    return c * CMYK_SCALE, m * CMYK_SCALE, y * CMYK_SCALE, k * CMYK_SCALE


def rgb_to_hsl(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return h * 360, s * 100, l * 100


def rgb_to_hsv(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return h * 360, s * 100, v * 100


# noinspection PyArgumentList
@lru_cache(maxsize=5)
def rgb_reading(current_file, path_to):  # Reading RGB values
    df_rgb = None
    final_path = os.path.join(path_to, current_file)
    if rgb_extension == '.xlsx':
        df_rgb = pd.read_excel(final_path, header=None, na_values=["NA"])
        try:
            df_rgb = df_rgb.drop(df_rgb.columns[0], axis=1)  # Dropping first column with numbers
        except IndexError:
            print(f'Please check the {final_path}. It seems to be empty. If so, delete it or recreate. Thank you. \n'
                  f' You are awesome as always')
    if rgb_extension == '.json':
        with open(final_path, 'r') as f:
            data = json.load(f)
        df_rgb = pd.DataFrame(columns=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"])
        for i in range(len(data)):
            row = []
            for area in data[str(i)]:
                rgb = data[str(i)][area]["RGB"]
                row.append(rgb['R'])
                row.append(rgb['G'])
                row.append(rgb['B'])
                if not area == 'Area 3':
                    row.append(None)
            df_rgb.loc[i] = row
    df_rgb = df_rgb.replace({np.nan: None})  # Filling NaN with None
    return df_rgb


def averaging_rgb(data_frame, row_num):
    try:
        r = data_frame.iloc[row_num, [0, 4, 8]].mean(axis=0)
        g = data_frame.iloc[row_num, [1, 5, 9]].mean(axis=0)
        b = data_frame.iloc[row_num, [2, 6, 10]].mean(axis=0)
    except IndexError:
        r = data_frame.iloc[row_num, [0]]
        g = data_frame.iloc[row_num, [1]]
        b = data_frame.iloc[row_num, [2]]
    return float(r), float(g), float(b)


def iv_reading(csv):
    current_csv_file = iv_parameters + csv
    df_iv = pd.read_csv(current_csv_file, header=None, na_values=["NA"])
    df_iv = df_iv.replace({np.nan: 0})
    return df_iv


@lru_cache(maxsize=5)
def create_folder(current_folder):  # Creating new folder for storing new data
    if not os.path.exists(current_folder + "RGB_plotting"):
        m = current_folder + "RGB_plotting/"
        os.makedirs(m)
        return m
    else:
        return str(current_folder + "RGB_plotting/")


@lru_cache(maxsize=5)
def add_column_chart(path_to_file, sheet_name, num):
    sample_name = str(os.path.basename(os.path.dirname(path_to_file)))
    chart = workbook.add_chart({'type': 'column'})
    chart.add_series({'name': [f'{sheet_name}', 2, 22],
                      'categories': [f'{sheet_name}', 1, 23, 1, 25],
                      'values': [f'{sheet_name}', 2, 23, 2, 25],
                      'overlap': -27,
                      'points': [{'fill': {'color': 'red'}, 'line': {'color': 'red'}},
                                 {'fill': {'color': 'green'}, 'line': {'color': 'green'}},
                                 {'fill': {'color': 'blue'}, 'line': {'color': 'blue'}}]})
    chart.add_series({
        'name': [f'{sheet_name}', 3, 22],
        'categories': [f'{sheet_name}', 1, 23, 1, 25],
        'values': [f'{sheet_name}', 3, 23, 3, 25],
        'points': [{'line': {'color': 'red'}, 'pattern': {'pattern': 'wide_upward_diagonal', 'fg_color': 'red'}},
                   {'line': {'color': 'green'}, 'pattern': {'pattern': 'wide_upward_diagonal', 'fg_color': 'green'}},
                   {'line': {'color': 'blue'}, 'pattern': {'pattern': 'wide_upward_diagonal', 'fg_color': 'blue'}}]})
    chart.set_title({'name': f"{sample_name}{specs['d5']['name'][f'{num}']} Initial vs Final",
                     'name_font': {'size': title_size, 'italic': False, 'bold': False, 'name': 'Calibri (Body)',
                                   'color': text_colour, 'layout': {'x': 0.4}}})
    chart.set_x_axis({'line': {'color': axis_colour},
                      'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
                      'num_font': {'size': num_size, 'color': text_colour}})
    chart.set_y_axis({'line': {'color': axis_colour},
                      'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
                      'min': 0, 'max': 255,
                      'num_font': {'size': num_size, 'color': text_colour},
                      'minor_unit': None, 'major_unit': 50,
                      'major_gridlines': {'visible': False},
                      'minor_gridlines': {'visible': False},
                      'major_tick_mark': 'outside'})
    chart.set_legend({'none': True})
    chart.set_plotarea({'border': {'none': True},
                        'layout': {'x': 0.8, 'y': 0.15, 'width': 0.8, 'height': 0.7}})
    chart.set_chartarea({'border': {'none': True}})
    chart.set_size({'x_scale': rgb_column_chart_x_scale, 'y_scale': rgb_column_chart_y_scale})
    return chart


@lru_cache(maxsize=5)
def add_rgb_scatter(path_to_file, counter, j, sheet_name, num):
    sample_name = str(os.path.basename(os.path.dirname(path_to_file)))
    chart = workbook.add_chart({'type': 'scatter'})
    chart.set_style(3)

    for i in range(3):
        chart.add_series({
            'name': [f'{sheet_name}', 1, i + specs[f'd{j}']['counter']],
            'categories': [f'{sheet_name}', 2, 0, counter + 1, 0],
            'values': [f'{sheet_name}', 2, i + specs[f'd{j}']['counter'], counter + 1, i + specs[f'd{j}']['counter']],
            'line': {'color': rgb_plot_lines[f'{i}']['colour'], 'width': rgb_line_width},
            # rgb_line_none_appear   'none': None,
            'marker': {
                'type': rgb_plot_lines[f'{i}']['marker'],
                'size': marker_size,
                'border': {'color': rgb_plot_lines[f'{i}']['colour'],
                           'transparency': rgb_plot_lines[f'{i}']['transparency']},
                # 'fill': {'color': rgb_plot_lines[f'{i}']['colour']}, Turn this on only if you are about to use
                # marker's type including the filling parameter (for example, circle, rectangle etc)
            },
            'y_error_bars': {'type': error_bar_type,
                             'plus_values': f"='{sheet_name}'!${specs[f'd{j}']['error'][f'{i}']}$3:"
                                            f"${specs[f'd{j}']['error'][f'{i}']}$"f"{counter + 2}",
                             'minus_values': f"='{sheet_name}'!${specs[f'd{j}']['error'][f'{i}']}$3:"
                                             f"${specs[f'd{j}']['error'][f'{i}']}$"f"{counter + 2}",
                             'line': {'color': rgb_plot_lines[f'{i}']['colour']}},
        })
    chart.set_title({'none': rgb_title_none,
                     'name': f"{sample_name} {specs[f'd{j}']['name'][f'{num}']} RGB values",
                     'name_font': {'size': title_size, 'italic': False, 'bold': False, 'name': 'Calibri (Body)',
                                   'color': text_colour}})
    chart.set_x_axis({'name': rgb_x_axis_name,
                      'line': {'color': axis_colour},
                      'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
                      'num_font': {'size': num_size, 'color': text_colour},
                      'min': 0, 'max': max_time,
                      'minor_unit': minor_unit, 'major_unit': major_unit,
                      'major_gridlines': {'visible': False},
                      'minor_gridlines': {'visible': False},
                      'major_tick_mark': 'cross',
                      'minor_tick_mark': 'outside'})
    chart.set_y_axis({'name': rgb_y_axis_name,
                      'line': {'color': axis_colour},
                      'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
                      'min': rgb_y_min, 'max': rgb_y_max,
                      'num_font': {'size': num_size, 'color': text_colour},
                      'minor_unit': None, 'major_unit': 50,
                      'major_gridlines': {'visible': False},
                      'minor_gridlines': {'visible': False},
                      'major_tick_mark': 'outside'})
    chart.set_legend({'none': rgb_legend_none,
                      'position': 'overlay_right',
                      'font': {'size': legend_size, 'bold': False, 'color': text_colour},
                      'layout': {'x': legend_area_x, 'y': legend_area_y, 'width': legend_area_width,
                                 'height': legend_area_height}})
    chart.set_plotarea({'border': {'none': True},
                        'layout': {'x': plot_area_x, 'y': plot_area_y, 'width': plot_area_width,
                                   'height': plot_area_height}})

    chart.set_chartarea({'border': {'none': True}})
    chart.set_size({'x_scale': rgb_chart_x_scale, 'y_scale': rgb_chart_y_scale})
    # The default chart width x height is 480 x 288 pixels.
    return chart


def add_cmyk(path_to_file, counter, sheet_name, num):
    sample_name = str(os.path.basename(os.path.dirname(path_to_file)))
    chart = workbook.add_chart({'type': 'scatter'})

    for i in range(4):
        chart.add_series({'name': [f'{sheet_name}', 1, i + 27],
                          'categories': [f'{sheet_name}', 2, 0, counter + 1, 0],
                          'values': [f'{sheet_name}', 2, i + 27, counter + 1, i + 27],
                          'line': {'color': cmyk_lines[f'{i}']['colour'], 'width': 2},
                          'marker': {'type': cmyk_lines[f'{i}']['marker'], 'size': marker_size,
                                     'border': {'color': cmyk_lines[f'{i}']['colour']},
                                     'fill': {'color': cmyk_lines[f'{i}']['colour']}}}),
    chart.set_title({'name': f"{sample_name} {colors[f'cs_0']['name'][f'{num}']} values",
                     'name_font': {'size': title_size, 'italic': False, 'bold': False, 'name': 'Calibri (Body)',
                                   'color': text_colour}})
    chart.set_x_axis({'name': 't(h)',
                      'line': {'color': axis_colour},
                      'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
                      'num_font': {'size': num_size, 'color': text_colour},
                      'min': 0, 'max': max_time,
                      'minor_unit': 250, 'major_unit': 500,
                      'major_gridlines': {'visible': False},
                      'minor_gridlines': {'visible': False},
                      'major_tick_mark': 'cross',
                      'minor_tick_mark': 'outside'})
    chart.set_y_axis({'name': 'CMYK',
                      'line': {'color': axis_colour},
                      'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
                      'min': 0, 'max': 100,
                      'num_font': {'size': num_size, 'color': text_colour},
                      'minor_unit': None, 'major_unit': 50,
                      'major_gridlines': {'visible': False},
                      'minor_gridlines': {'visible': False},
                      'major_tick_mark': 'outside'})
    chart.set_legend({'position': 'overlay_right',
                      'font': {'size': legend_size, 'bold': False, 'color': text_colour},
                      'layout': {'x': 0.75, 'y': 0.45, 'width': 0.25, 'height': 0.4}})
    chart.set_plotarea({'border': {'none': True},
                        'layout': {'x': 0.8, 'y': 0.1, 'width': 0.8, 'height': 0.7}})
    chart.set_chartarea({'border': {'none': True}})
    chart.set_size({'x_scale': 0.7, 'y_scale': 0.7})  # The default chart width x height is 480 x 288 pixels.
    return chart


def add_hsl_hsv(path_to_file, counter, sheet_name, l_v, num):
    sample_name = str(os.path.basename(os.path.dirname(path_to_file)))
    chart = workbook.add_chart({'type': 'scatter'})

    for i in range(3):
        chart.add_series({'name': [f'{sheet_name}', 1, i + colors[f'cs_{l_v}']['column']],
                          'categories': [f'{sheet_name}', 2, 0, counter + 1, 0],
                          'values': [f'{sheet_name}', 2, i + colors[f'cs_{l_v}']['column'], counter + 1,
                                     i + colors[f'cs_{l_v}']['column']],
                          'line': {'width': 2},
                          'marker': {
                              'type': cmyk_lines[f'{i}']['marker'],
                              'size': marker_size,
                              # 'border': {'color': CMYK_lines[f'{i}']['colour']},
                              # 'fill': {'color': CMYK_lines[f'{i}']['colour']},
                          },
                          'y2_axis': colors[f'cs_{l_v}']['axis'][f'{i}']}),
    chart.set_title({'name': f"{sample_name} {colors[f'cs_{l_v}']['name'][f'{num}']} values",
                     'name_font': {'size': title_size, 'italic': False, 'bold': False, 'name': 'Calibri (Body)',
                                   'color': text_colour}})
    chart.set_x_axis({'name': 't(h)',
                      'line': {'color': axis_colour},
                      'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
                      'num_font': {'size': num_size, 'color': text_colour},
                      'min': 0, 'max': max_time,
                      'minor_unit': 250, 'major_unit': 500,
                      'major_gridlines': {'visible': False},
                      'minor_gridlines': {'visible': False},
                      'major_tick_mark': 'cross',
                      'minor_tick_mark': 'outside'})
    chart.set_y_axis({'name': colors[f'cs_{l_v}']['unit']['2'],
                      'line': {'color': axis_colour},
                      'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
                      'min': 0, 'max': 100,
                      'num_font': {'size': num_size, 'color': text_colour},
                      'minor_unit': None, 'major_unit': 50,
                      'major_gridlines': {'visible': False},
                      'minor_gridlines': {'visible': False},
                      'major_tick_mark': 'outside'})
    chart.set_y2_axis({'name': colors[f'cs_{l_v}']['unit']['1'],
                       'line': {'color': axis_colour},
                       'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
                       'min': 0, 'max': 360,
                       'num_font': {'size': num_size, 'color': text_colour},
                       'minor_unit': 50, 'major_unit': 100,
                       'major_gridlines': {'visible': False},
                       'minor_gridlines': {'visible': False},
                       'major_tick_mark': 'outside'})
    chart.set_legend({'position': 'overlay_right',
                      'font': {'size': legend_size, 'bold': False, 'color': text_colour},
                      'layout': {'x': 0.75, 'y': 0.45, 'width': 0.25, 'height': 0.3}})
    chart.set_plotarea({'border': {'none': True},
                        'layout': {'x': 0.8, 'y': 0.1, 'width': 0.8, 'height': 0.7}})
    chart.set_chartarea({'border': {'none': True}})
    chart.set_size({'x_scale': 0.7, 'y_scale': 0.7})  # The default chart width x height is 480 x 288 pixels.
    return chart


@lru_cache(maxsize=5)
def add_iv_scatters(path_to_file, counter, j, sheet_name, num):
    sample_name = str(os.path.basename(os.path.dirname(path_to_file)))
    chart_iv = workbook.add_chart({'type': 'scatter', 'subtype': 'straight'})  # Delete subtype here to return markers

    chart_iv.add_series({
        'categories': [f'{sheet_name}', 2, 0, counter + 1, 0],
        'values': [f'{sheet_name}', 2, iv[f'iv_{j}']['column'], counter + 1, iv[f'iv_{j}']['column']],
        'line': {'width': 2},
    })
    chart_iv.set_title({'name': f"{sample_name} {iv[f'iv_{j}']['name'][f'{num}']}",
                        'name_font': {'size': title_size, 'italic': False, 'bold': False, 'name': 'Calibri (Body)',
                                      'color': text_colour}})
    chart_iv.set_x_axis({'name': 't(h)',
                         'line': {'color': axis_colour},
                         'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
                         'num_font': {'size': num_size, 'color': text_colour},
                         'min': 0, 'max': max_time,
                         'minor_unit': 250, 'major_unit': 500,
                         'major_gridlines': {'visible': False},
                         'minor_gridlines': {'visible': False},
                         'major_tick_mark': 'cross',
                         'minor_tick_mark': 'outside'})
    chart_iv.set_legend(({'none': True}))
    chart_iv.set_y_axis({'min': 0, 'max': iv[f'iv_{j}']['max'],
                         'name': iv[f'iv_{j}']['unit'],
                         'line': {'color': axis_colour},
                         'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
                         'num_font': {'size': num_size, 'color': text_colour},
                         'major_gridlines': {'visible': False},
                         'minor_gridlines': {'visible': False},
                         'major_tick_mark': 'outside'})
    chart_iv.set_plotarea({'border': {'none': True},
                           'layout': {'x': 0.8, 'y': 0.1, 'width': 0.8, 'height': 0.7}})
    chart_iv.set_chartarea({'border': {'none': True}})
    chart_iv.set_size({'x_scale': 0.7, 'y_scale': 0.7})  # The default chart width x height is 480 x 288 pixels.
    return chart_iv


def add_iv_prediction(path_to_file, counter, j, sheet_name, num, points):
    sample_name = str(os.path.basename(os.path.dirname(path_to_file)))
    chart_iv = workbook.add_chart({'type': 'scatter', 'subtype': 'straight'})  # Delete subtype here to return markers

    chart_iv.add_series({'categories': [f'{sheet_name}', 2, 0, counter + 1, 0],
                         'values': [f'{sheet_name}', 2, iv['iv_1']['column'], counter + 1, iv['iv_1']['column']],
                         'line': {'width': 2}})
    # Max slope
    chart_iv.add_series({'categories': [f'{sheet_name}', 2 + points, 0, counter + 1, 0],  # X-axis
                         'values': [f'{sheet_name}', 2 + points, iv['iv_4']['column'], counter + 1,
                                    iv['iv_4']['column']],  # Y-axis
                         'line': {'color': 'red', 'width': 2}})
    # Min slope
    chart_iv.add_series({'categories': [f'{sheet_name}', 2 + points, 0, counter + 1, 0],  # X-axis
                         'values': [f'{sheet_name}', 2 + points, iv['iv_4']['column'] + 1, counter + 1,
                                    iv['iv_4']['column'] + 1],  # Y-axis
                         'line': {'color': 'green', 'width': 2}})
    chart_iv.set_title({'name': f"{sample_name} {iv['iv_4']['name'][f'{num}']}",
                        'name_font': {'size': title_size, 'italic': False, 'bold': False, 'name': 'Calibri (Body)',
                                      'color': text_colour}})
    chart_iv.set_x_axis({'name': 't(h)',
                         'line': {'color': axis_colour},
                         'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
                         'num_font': {'size': num_size, 'color': text_colour},
                         'min': 0, 'max': max_time,
                         'minor_unit': 250, 'major_unit': 500,
                         'major_gridlines': {'visible': False},
                         'minor_gridlines': {'visible': False},
                         'major_tick_mark': 'cross',
                         'minor_tick_mark': 'outside'})
    chart_iv.set_legend(({'none': True}))
    chart_iv.set_y_axis({  # 'min': iv['iv_4']['min'], 'max': iv[f'iv_{j}']['max'],
        'name': iv[f'iv_{j}']['unit'],
        'line': {'color': axis_colour},
        'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
        'num_font': {'size': num_size, 'color': text_colour},
        'major_gridlines': {'visible': False},
        'minor_gridlines': {'visible': False},
        'major_tick_mark': 'outside'})
    chart_iv.set_plotarea({'border': {'none': True},
                           'layout': {'x': 0.8, 'y': 0.1, 'width': 0.8, 'height': 0.7}})
    chart_iv.set_chartarea({'border': {'none': True}})
    chart_iv.set_size({'x_scale': 0.7, 'y_scale': 0.7})  # The default chart width x height is 480 x 288 pixels.
    return chart_iv


def row_selecting_total(sample_indexing, specification):
    rgb_setback = (len(samples)) // samples_number
    for h in range(0, rgb_setback):  # Here is h stands for local indexing var
        if specification == 'rgb':
            if samples_number * h <= sample_indexing < samples_number * (h + 1):
                return int(chart_setback * rgb_setback + chart_setback * h)
            if sample_indexing >= samples_number * rgb_setback:
                return int(chart_setback * rgb_setback + chart_setback * (rgb_setback - 1))
        if specification == 'col':
            if samples_number * h <= sample_indexing < samples_number * (h + 1):
                return int(chart_setback * h)
            if sample_indexing >= samples_number * rgb_setback:
                return int(chart_setback * (rgb_setback - 1))


def col_selecting_total(sample_indexing):
    rgb_setback = (len(samples)) // samples_number
    for h in range(0, rgb_setback):  # Here is h stands for local indexing var
        if samples_number * h <= sample_indexing < samples_number * (h + 1):
            return sample_indexing - samples_number * h
        if sample_indexing >= samples_number * rgb_setback:
            return sample_indexing - samples_number * (rgb_setback - 1)


@lru_cache(maxsize=5)
def main_rgb_plotting(dir_path_for_it, current_file_rgb, current_worksheet, current_sample, sample_index):
    center = workbook.add_format({'align': 'center'})
    across_selection = workbook.add_format()
    across_selection.set_center_across()
    time_line = timeline_detector(current_sample)
    rgb_values = rgb_reading(current_file_rgb, dir_path_for_it)

    for o in range(6):
        current_worksheet.write(0, specs[f'd{o}']['counter'], specs[f'd{o}']['name']['1'], across_selection)
        current_worksheet.write_blank(0, specs[f'd{o}']['counter'] + 1, '', across_selection)
        current_worksheet.write_blank(0, specs[f'd{o}']['counter'] + 2, '', across_selection)

    for i in range(2, 19, 4):  # Adding headlines for columns
        current_worksheet.write(1, 0, 'Hours', center)
        current_worksheet.write(1, i, 'R', center)
        current_worksheet.write(1, i + 1, 'G', center)
        current_worksheet.write(1, i + 2, 'B', center)

    flag_iv = 0
    df_yellow = pd.DataFrame([None])
    c = 0  # c represents here the timepoints
    while c < len(time_line):
        if c in rgb_values.index:
            current_worksheet.write(c + 2, 0, time_line.iat[c, 0])
            r, g, b = averaging_rgb(rgb_values, c)
            current_worksheet.write_row(c + 2, 27, rgb_to_cmyk(r, g, b))
            current_worksheet.write_row(c + 2, 32, rgb_to_hsl(r, g, b))
            current_worksheet.write_row(c + 2, 36, rgb_to_hsv(r, g, b))
            current_worksheet.write_row(c + 2, 2, rgb_values.loc[c])  # Writing entire row from Pandas dataframe

            if prediction_flag == 1:  # Creating a pandas dataframe with Y channel values for the further usage
                df_yellow.loc[c] = 255 - b
                # df_yellow.loc[c] = rgb_to_cmyk(r, g, b)[2]
            else:
                pass

            if big_flag == 1:
                try:
                    iv_pd = iv_reading(iv_list[c])
                    try:  # Checking if the IV have enough data rows
                        for ch_in in range(4):
                            if float(iv_pd.iat[sample_index + 1, 1 + ch_in]) >= 0.0:  # Replacing negative elements
                                # with 0
                                current_worksheet.write(c + 2, iv['iv_0']['column'] + ch_in, iv_pd.iat[sample_index + 1,
                                                                                                       1 + ch_in])
                            else:
                                current_worksheet.write(c + 2, iv['iv_0']['column'] + ch_in, 0)
                    except IndexError:
                        flag_iv = 1
                except IndexError:
                    sys.exit("Check the number of IV_parameters files")
        else:
            print(f'Check the {current_file_rgb}. It seems like the datapoint'
                  f' {len(time_line) - (len(time_line) - c)} is missing')
            pass
        current_worksheet.write_formula(c + 2, 14, f'=AVERAGE(C{c + 3},G{c + 3},K{c + 3})')
        current_worksheet.write_formula(c + 2, 15, f'=AVERAGE(D{c + 3},H{c + 3},L{c + 3})')
        current_worksheet.write_formula(c + 2, 16, f'=AVERAGE(E{c + 3},I{c + 3},M{c + 3})')

        current_worksheet.write_formula(c + 2, 18, f'=_xlfn.STDEV.S(C{c + 3},G{c + 3},K{c + 3})')
        current_worksheet.write_formula(c + 2, 19, f'=_xlfn.STDEV.S(D{c + 3},H{c + 3},L{c + 3})')
        current_worksheet.write_formula(c + 2, 20, f'=_xlfn.STDEV.S(E{c + 3},I{c + 3},M{c + 3})')
        c += 1

    current_worksheet.write(1, 23, f'R{current_sample}', center)
    current_worksheet.write(1, 24, f'G{current_sample}', center)
    current_worksheet.write(1, 25, f'B{current_sample}', center)
    current_worksheet.write(2, 22, 'Initial')
    current_worksheet.write(3, 22, 'Final')
    current_worksheet.write_formula(2, 23, '=O3')
    current_worksheet.write_formula(2, 24, '=P3')
    current_worksheet.write_formula(2, 25, '=Q3')
    current_worksheet.write_formula(3, 23, f'=O{len(rgb_values) + 2}')
    current_worksheet.write_formula(3, 24, f'=P{len(rgb_values) + 2}')
    current_worksheet.write_formula(3, 25, f'=Q{len(rgb_values) + 2}')

    current_worksheet.write(1, 27, 'C', center)
    current_worksheet.write(1, 28, 'M', center)
    current_worksheet.write(1, 29, 'Y', center)
    current_worksheet.write(1, 30, 'K', center)
    current_worksheet.write(1, 32, 'H', center)
    current_worksheet.write(1, 33, 'S', center)
    current_worksheet.write(1, 34, 'L', center)
    current_worksheet.write(1, 36, 'H', center)
    current_worksheet.write(1, 37, 'S', center)
    current_worksheet.write(1, 38, 'V', center)
    current_worksheet.write(0, 27, f"{colors['cs_0']['name']['1']}", across_selection)
    current_worksheet.write(0, 32, f"{colors['cs_1']['name']['1']}", across_selection)
    current_worksheet.write(0, 36, f"{colors['cs_2']['name']['1']}", across_selection)
    for m in range(3):
        current_worksheet.write_blank(0, 28 + m, '', across_selection)
    for n in range(2):
        current_worksheet.write_blank(0, 33 + n, '', across_selection)
        current_worksheet.write_blank(0, 37 + n, '', across_selection)

    for j in range(4):  # Adding 4 RGB plots
        current_worksheet.insert_chart(specs[f'd{j}']['position'], add_rgb_scatter(dir_path_for_it, len(time_line),
                                                                                   j, current_sample, 1))
    current_worksheet.insert_chart(f'H{timeline_len}', add_column_chart(dir_path_for_it, current_sample, 1))
    current_worksheet.insert_chart(colors['cs_0']['position'], add_cmyk(dir_path_for_it, len(time_line),
                                                                        current_sample, 1))
    for b in range(1, 3):
        current_worksheet.insert_chart(colors[f'cs_{b}']['position'], add_hsl_hsv(dir_path_for_it, len(time_line),
                                                                                  current_sample, b, 1))

    worksheet_main.insert_chart(row_selecting_total(sample_index, 'rgb'), col_selecting_total(sample_index) *
                                rgb_scatter_position,
                                add_rgb_scatter(dir_path_for_it, len(time_line), 3, current_sample, 2))
    worksheet_main.insert_chart(row_selecting_total(sample_index, 'col'),
                                col_selecting_total(sample_index) * rgb_scatter_position + 1,
                                add_column_chart(dir_path_for_it, current_sample, 2))

    if big_flag == 1:
        if flag_iv == 0:
            for j in range(4):  # Adding 4 IV plots
                current_worksheet.write(1, iv[f'iv_{j}']['column'], f"{iv[f'iv_{j}']['name']['1']}" + ', '
                                        + f"{iv[f'iv_{j}']['unit']}", center)
                current_worksheet.insert_chart(iv[f'iv_{j}']['position'], add_iv_scatters(dir_path_for_it,
                                                                                          len(time_line), j,
                                                                                          current_sample, 1))
                if j == 1 and prediction_flag == 1:  # Do not plot the IV curve without prediction
                    continue
                worksheet_main.insert_chart(iv[f'iv_{j}']['total_position'], sample_index * 6,
                                            add_iv_scatters(dir_path_for_it, len(time_line), j, current_sample, 2))
            if prediction_flag == 1:
                # Python
                linear_fit = np.polyfit(time_line.iloc[:num_of_points, 0].astype('float64'),
                                        df_yellow.iloc[:num_of_points, 0].astype('float64'), 1)
                current_worksheet.write(timeline_len + 1, 32, 'Lin_fit', across_selection)
                current_worksheet.write_blank(timeline_len + 1, 33, '', across_selection)
                current_worksheet.write(timeline_len + 1, 34, 'Jlim_max')
                current_worksheet.write(timeline_len + 1, 35, 'Jlim_min')
                current_worksheet.write(timeline_len + 1, 36, 'Jlim0_max')
                current_worksheet.write(timeline_len + 1, 37, 'Jlim0_min')
                current_worksheet.write(timeline_len + 2, 31, 'Python')
                current_worksheet.write(timeline_len + 2, 32, linear_fit[0])
                current_worksheet.write(timeline_len + 2, 33, linear_fit[1])
                # current_worksheet.write(timeline_len + 2, 34, prediction_var)
                # current_worksheet.write(timeline_len + 2, 35, prediction_var)
                # current_worksheet.write(timeline_len + 2, 36, prediction_var)
                # current_worksheet.write(timeline_len + 2, 37, prediction_var)

                # Excel
                for tic in range(num_of_points + 1, len(time_line) + 1):
                    current_worksheet.write(timeline_len + 3 + tic - num_of_points, 32,
                                            f'=A{2 + tic} * AG20 * AI20 + AK20')
                    current_worksheet.write(timeline_len + 3 + tic - num_of_points, 33,
                                            f'=A{2 + tic} * AG20 * AJ20 + AL20')
                current_worksheet.write(timeline_len + 3, 31, 'Excel')
                for tac in range(len(time_line)):
                    current_worksheet.write(timeline_len + 2 + tac, 29, f'=255-Q{3 + tac}')
                current_worksheet.write(timeline_len + 3, 32, f'=SLOPE(AD{timeline_len + 3}:'
                                                              f'AD{timeline_len + 2 + num_of_points},'
                                                              f'A3:A{num_of_points + 2})')

                # External code Python
                # temporary = prediction(time_line, df_yellow, num_of_points)
                # for prediction_min_max in range(2):
                #     current_worksheet.write_column(2 + num_of_points, iv['iv_4']['column'] + prediction_min_max,
                #                                    temporary[prediction_min_max], center)
                current_worksheet.insert_chart(iv['iv_4']['position'], add_iv_prediction(dir_path_for_it,
                                                                                         len(time_line), 4,
                                                                                         current_sample, 1,
                                                                                         num_of_points))
                worksheet_main.insert_chart(iv['iv_4']['total_position'], sample_index * 6,
                                            add_iv_prediction(dir_path_for_it, len(time_line), 4, current_sample, 1,
                                                              num_of_points))
            else:
                pass
        else:
            pass
    else:
        pass


def list_comprehension(list_of_samples, new_element):  # Filtering if new element has the same as previous file name
    # prefix
    if new_element > 0:
        if list_of_samples[new_element] == list_of_samples[new_element - 1]:
            return 1
        else:
            return 0
    else:
        return 0


sample_list, iv_list, samples, directories = [], [], [], []
workbook = xlsxwriter.Workbook(create_folder(highest_path) + str(today) + f" {highest_path.split('/')[-2]} Total RGB "
                                                                          f"and all others.xlsx",
                               {'strings_to_numbers': True})
worksheet_main = workbook.add_worksheet('Total')

try:
    iv_list_sorting = sorted(os.listdir(iv_parameters), key=lambda filename: int(filename.split(' IV')[0]))
    big_flag = 1
    for csv_file in iv_list_sorting:
        iv_list.append(csv_file)
except FileNotFoundError:
    big_flag = 0

for dir_path, dir_names, files in os.walk(highest_path):
    for RGB_file in files:
        if RGB_file.endswith(rgb_extension) and 'Results' in RGB_file and 'ColorCheckers' not in dir_path:
            if not RGB_file.startswith('Timeline'):  # Specify here the file with timepoints
                sample_list.append(RGB_file)
                ind = sample_list.index(RGB_file)  # Getting numerical order of each sample
                samples.append(os.path.basename(Path(dir_path).parents[0]))
                directories.append(dir_path)
                if list_comprehension(samples, ind) == 1:  # Filtering to get only the last file if multiple is given
                    samples.pop(ind - 1)
                    sample_list.pop(ind - 1)
                    directories.pop(ind - 1)

rgb_setback_check = (len(samples)) / samples_number
if not rgb_setback_check.is_integer():
    print(f'Check the samples number and the batch ratio\n Samples = {len(samples)} and batch = {samples_number}')
########################################################################################################################
iv = {
    'iv_0': {'max': 4, 'column': 40, 'name': {'1': 'Efficiency', '2': 'Efficiency'}, 'unit': '%',
             'position': f'R{timeline_len}',
             'total_position': chart_setback * (1 + (len(samples)) // samples_number * 2)},
    'iv_1': {'max': 9, 'column': 41, 'name': {'1': 'Isc', '2': 'Isc'}, 'unit': 'mA/cm^2',
             'position': f'L{timeline_len}',
             'total_position': chart_setback * (0 + (len(samples)) // samples_number * 2)},
    'iv_2': {'max': 1.1, 'column': 42, 'name': {'1': 'Voc', '2': 'Voc'}, 'unit': 'V', 'position': f'X{timeline_len}',
             'total_position': chart_setback * (2 + (len(samples)) // samples_number * 2)},
    'iv_3': {'max': 1, 'column': 43, 'name': {'1': 'FF', '2': 'FF'}, 'unit': '',
             'position': f'S{timeline_len + chart_setback}',
             'total_position': chart_setback * (3 + (len(samples)) // samples_number * 2)},
    'iv_4': {'max': 9, 'min': 0, 'column': 45, 'name': {'1': 'Isc', '2': 'Isc'}, 'unit': 'mA/cm^2',
             'position': f'S{timeline_len + chart_setback + chart_setback}',
             'total_position': chart_setback * (0 + (len(samples)) // samples_number * 2)},
}

pbar = tqdm(range(len(samples)), desc='Working on sample 1', unit=' analyzing', ncols=100, position=0, colour='blue')
for member in pbar:
    worksheet = workbook.add_worksheet(f'{samples[member]}')
    main_rgb_plotting(directories[member], sample_list[member], worksheet, samples[member], member)
    time.sleep(0.01)
    pbar.set_description(f'Working on sample {member + 1}')

workbook.close()
time.sleep(.2)
os.startfile(full_path_to_file)
print("\n", "--- %s seconds ---" % (time.time() - start_time))
