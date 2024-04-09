from __future__ import annotations

import warnings
from typing import Any, Iterable

import numpy as np
import pandas as pd
from icecream import ic
from numpy import ndarray, dtype, floating
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit, OptimizeWarning
from xlsxwriter import Workbook
from xlsxwriter.workbook import ChartScatter


class YellowChannelPredictor:
    """
    Class for predicting values based on the Y channel and time data.
    """

    def __init__(self, workbook: Workbook, settings: dict, df_time: pd.DataFrame, df_yellow: pd.DataFrame,
                 j_sc_dict: dict,
                 j_lim_per_yellow_max: float = 0.398,
                 j_lim_per_yellow_min: float = 0.286,
                 distance: float = 30,
                 initial_concentration: float = 0.05,
                 concentration_per_yellow_max: float = 0.000909,
                 concentration_per_yellow_min: float = 0.000654, ):
        """
        Initialize the predictor with given constants.

        :param workbook: The xlsxwriter Workbook object where plots are to be added.
        :param settings: A dictionary with the settings
        :param df_time: DataFrame containing time information.
        :param df_yellow: DataFrame containing yellow channel information.
        :param j_sc_dict: DataFrame containing Short-circuit current information.
        :param j_lim_per_yellow_max: Maximum limit for J.
        :param j_lim_per_yellow_min: Minimum limit for J.
        :param distance: Distance constant.
        :param initial_concentration: Initial concentration is constant.
        """
        self.wb = workbook
        self.df_yellow = df_yellow
        self.df_time = df_time

        self.settings = settings['ChartsCreator']
        self.high_settings = settings
        self.j_lim_per_yellow_max = j_lim_per_yellow_max
        self.j_lim_per_yellow_min = j_lim_per_yellow_min
        self.distance = distance
        self.initial_concentration = initial_concentration
        self.diffusion_coefficient_max = 7.5e-6
        self.diffusion_coefficient_min = 6.8e-6
        self.concentration_per_yellow_min = concentration_per_yellow_min
        self.concentration_per_yellow_max = concentration_per_yellow_max

        # Populating Jsc values
        sweep_key = settings['sweep_key']
        raw_data = []
        for time_point, time_data in j_sc_dict.items():
            raw_data.append(time_data['Parameters'][sweep_key]['Short-circuit current density (mA/cm²)'])
        self.df_j_sc = pd.DataFrame(raw_data)

        # Plotting variables
        self.min_time = self.settings['iv_data']['prediction_time']['min']
        self.max_time = self.settings['iv_data']['prediction_time']['max']
        self.num_of_points = 0
        self.data_len = 0
        self.intersection_index = 0

    def perform_prediction(
            self,
            num_of_points,
    ) -> dict[
        str, list[Any] |
        ndarray[Any, dtype[Any]] |
        ndarray | Iterable | int |
        float | ndarray[Any, dtype[floating[Any]]] |
        list[ndarray[Any, dtype[Any]] |
             Any]]:
        """
        Perform prediction based on the Y channel values and time data.

        :param num_of_points: Number of points to consider for prediction.
        :return: A dictionary containing labels as keys and data as values.
        """
        self.num_of_points = num_of_points
        start_index = self.high_settings['prediction_start_point']

        j_lim_0_max = 4 * 96485 * self.diffusion_coefficient_max * self.initial_concentration / (self.distance * 1e-4)
        j_lim_0_min = 4 * 96485 * self.diffusion_coefficient_min * self.initial_concentration / (self.distance * 1e-4)

        self.j_lim_per_yellow_max = 4 * 96485 * self.diffusion_coefficient_max * self.concentration_per_yellow_max / (
                self.distance * 1e-4)
        self.j_lim_per_yellow_min = 4 * 96485 * self.diffusion_coefficient_min * self.concentration_per_yellow_min / (
                self.distance * 1e-4)
        try:
            fit_coefficients = np.polyfit(self.df_time.iloc[start_index:self.num_of_points, 0].astype('float64'),
                                          self.df_yellow.iloc[start_index:self.num_of_points, 0].astype('float64'), 1)
        except Exception as e:
            print(e)
            fit_coefficients = [1, 1]
        # Calculate two points for max and min slopes
        initial_time_max_slope = self.df_time.iat[self.num_of_points, 0]
        initial_time_min_slope = self.df_time.iat[self.num_of_points, 0]
        final_time = self.df_time.iat[-1, 0]
        max_slope = fit_coefficients[0] * self.j_lim_per_yellow_max
        min_slope = fit_coefficients[0] * self.j_lim_per_yellow_min

        initial_max_slope = initial_time_max_slope * max_slope + j_lim_0_max
        final_max_slope = final_time * max_slope + j_lim_0_max

        initial_min_slope = initial_time_min_slope * min_slope + j_lim_0_min
        final_min_slope = final_time * min_slope + j_lim_0_min

        # Calculate where the max and min slopes intersect with the x-axis, if they are above it
        if final_max_slope > 0:
            intercept = j_lim_0_max
            final_time_max_slope = -(intercept / max_slope)
            final_max_slope = 0
        else:
            final_time_max_slope = final_time

        if final_min_slope > 0:
            intercept = j_lim_0_min
            final_time_min_slope = -(intercept / min_slope)
            final_min_slope = 0
        else:
            final_time_min_slope = final_time

        # Calculate prediction line values (y = mx + b)
        prediction_slope = (max_slope + min_slope) / 2
        prediction_intercept = (j_lim_0_max + j_lim_0_min) / 2

        # Prepare the vertical line indictment based on how many hours prediction was made
        vertical_line_time = [self.df_time.iat[self.num_of_points - 1, 0].astype('float64')] * 2
        vertical_line_value = [self.settings['iv_data']['y_min'], self.settings['iv_data']['y_max']]

        # Extend the x-axis
        time = self.df_time.to_numpy()
        new_extended_time = np.concatenate(
            [time[:-1], np.linspace(time[-1], max(final_time_max_slope, final_time_min_slope) * 1.01,
                                    self.high_settings['concatenate_number'])])

        self.data_len = len(new_extended_time)

        # Reassign the min and max time values
        # self.min_time = new_extended_time[0]
        # self.max_time = new_extended_time[-1]

        # Calculate initial current (horizontal line)
        start_index = (self.df_time -
                       self.high_settings['initial_predicted_current_avg_time_range_start']).abs().idxmin().iloc[0]
        average_sliced_j_sc = self.df_j_sc.iloc[start_index:num_of_points].astype('float64')
        average_sliced_j_sc_deviation = np.std(average_sliced_j_sc, ddof=1)
        average_sliced_j_sc_value = average_sliced_j_sc.mean().iloc[0]
        if pd.isna(average_sliced_j_sc_value):
            average_sliced_j_sc_value = self.df_j_sc.iat[start_index, 0].astype('float64')

        # Find the time point where average_sliced_j_sc intersects with the prediction line
        intersection_time = (average_sliced_j_sc_value - prediction_intercept) / prediction_slope

        # average_sliced_j_sc_time = [self.min_time, intersection_time]

        # Recalculate prediction and slopes values and times
        final_time_prediction = - (prediction_intercept / prediction_slope)
        # final_time_prediction = (final_time_max_slope + final_time_min_slope) / 2
        # initial_prediction =
        # initial_time_min_slope = intersection_time
        # initial_time_max_slope = intersection_time
        # initial_min_slope = initial_time_min_slope * min_slope + j_lim_0_min
        # initial_max_slope = initial_time_max_slope * max_slope + j_lim_0_max
        initial_max_slope = average_sliced_j_sc_value - average_sliced_j_sc_deviation
        initial_min_slope = average_sliced_j_sc_value + average_sliced_j_sc_deviation
        initial_time_min_slope = (initial_min_slope - j_lim_0_min) / min_slope
        initial_time_max_slope = (initial_max_slope - j_lim_0_max) / max_slope

        # Calculate fit line
        def fit_func(x, a, b, c):
            return a * x ** 2 + b * x + c

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=OptimizeWarning)
            # params, _ = curve_fit(fit_func,
            #                       self.df_time.iloc[start_index:self.num_of_points, 0].astype('float64').values,
            #                       self.df_j_sc.iloc[start_index:self.num_of_points, 0].astype('float64').values)
            params, _ = curve_fit(fit_func, self.df_time.iloc[start_index:, 0].astype('float64').values,
                                  self.df_j_sc.iloc[start_index:, 0].astype('float64').values)

        fit_line = fit_func(new_extended_time, params[0], params[1], params[2])

        return {
            'Time, h': list(new_extended_time),
            'LinFit': list(fit_line),
            'MinSlopeTime, h': [0, initial_time_min_slope, final_time_min_slope],
            'MinSlopeValue': [initial_min_slope, initial_min_slope, final_min_slope],
            'MaxSlopeTime, h': [0, initial_time_max_slope, final_time_max_slope],
            'MaxSlopeValue': [initial_max_slope, initial_max_slope, final_max_slope],
            'PredictionTime, h': [intersection_time, final_time_prediction],
            'PredictionValue': [average_sliced_j_sc_value, 0],
            'VerticalLineTime, h': vertical_line_time,
            'VerticalLineValue': vertical_line_value,
            'Avg Current Time, h': [self.min_time, intersection_time, final_time_prediction],
            'Average Jsc': [average_sliced_j_sc_value, average_sliced_j_sc_value, 0]
        }

    def create_complex_iv_plot(self, device_name: str, j_row_start: int, j_row_end: int, row_start: int,
                               column: int) -> ChartScatter:
        """
        Create a complex IV plot with additional slopes and prediction lines.

        :param device_name: The name of the device for which the IV plot is being created.
        :param j_row_start: The row number where the Jsd data starts.
        :param j_row_end: The row number where the Jsd data ends.
        :param row_start: The row number where the prediction data starts.
        :param column: The column number of the prediction data.
        :return: The complex IV plot chart object.
        """
        chart = self.wb.add_chart({'type': 'scatter'})
        j_column = self.high_settings['Starting columns']['IV data'] + 1
        y_column = self.high_settings['Starting columns']['Yellow']
        major_unit = (self.max_time - self.min_time) // 4
        minor_unit = major_unit / 2
        row_end = row_start + self.data_len - 1

        # Add Jsc data
        chart.add_series({
            'name': [f'{device_name}', j_row_start - 1, j_column],
            'categories': [f'{device_name}', j_row_start, 0, j_row_end, 0],
            'values': [f'{device_name}', j_row_start, j_column, j_row_end, j_column],
            'line': {'width': self.settings['rgb_plot']['line_width'], 'color': 'blue'},
            'marker': {'type': 'none'}
            #         'type': self.settings['iv_data']['marker']['type'],
            #         'size': self.settings['iv_data']['marker']['size'],
            #         'border': {'color': 'black'},
            #         'fill': {'color': 'white'}}
        })

        # Add linear fitting.
        chart.add_series({
            'name': [f'{device_name}', row_start - 1, column + 1],
            'categories': [f'{device_name}', row_start, column, row_end, column],
            'values': [f'{device_name}', row_start, column + 1, row_end, column + 1],
            'line': {'color': 'cyan', 'width': self.settings['rgb_plot']['line_width'], 'dash_type': 'dash_dot'},
            'marker': {'type': 'none'}
        })

        row_start_fitted = row_start + self.intersection_index if \
            row_start + self.intersection_index >= row_start + self.num_of_points - 1 else \
            row_start + self.num_of_points - 1

        # Add the min slope.
        chart.add_series({
            'name': [f'{device_name}', row_start - 1, column + 3],
            'categories': [f'{device_name}', row_start, column + 2, row_start + 2, column + 2],
            'values': [f'{device_name}', row_start, column + 3, row_start + 2, column + 3],
            'line': {'color': 'green', 'width': self.settings['rgb_plot']['line_width']},
            'marker': {'type': 'none'}
        })

        # Add the max slope.
        chart.add_series({
            'name': [f'{device_name}', row_start - 1, column + 5],
            'categories': [f'{device_name}', row_start, column + 4, row_start + 2, column + 4],
            'values': [f'{device_name}', row_start, column + 5, row_start + 2, column + 5],
            'line': {'color': 'red', 'width': self.settings['rgb_plot']['line_width']},
            'marker': {'type': 'none'}
        })

        # Add prediction.
        chart.add_series({
            'name': [f'{device_name}', row_start - 1, column + 7],
            'categories': [f'{device_name}', row_start, column + 6, row_start + 2, column + 6],
            'values': [f'{device_name}', row_start, column + 7, row_start + 2, column + 7],
            'line': {'color': 'purple', 'width': self.settings['rgb_plot']['line_width']},
            'marker': {'type': 'none'}
        })

        # Add vertical line representing time used for prediction.
        chart.add_series({
            'name': [f'{device_name}', row_start - 1, column + 9],
            'categories': [f'{device_name}', row_start, column + 8, row_start + 1, column + 8],
            'values': [f'{device_name}', row_start, column + 9, row_start + 1, column + 9],
            'line': {'color': '#D3D3D3', 'width': self.settings['rgb_plot']['line_width'] - 0.5, 'dash_type': 'dash'},
            'marker': {'type': 'none'}
        })

        # Add horizontal line representing average current density value based on the measured data.
        chart.add_series({
            'name': [f'{device_name}', row_start - 1, column + 11],
            'categories': [f'{device_name}', row_start, column + 10, row_start + 2, column + 10],
            'values': [f'{device_name}', row_start, column + 11, row_start + 2, column + 11],
            'line': {'color': 'purple', 'width': self.settings['rgb_plot']['line_width'] - 0.5, 'dash_type': 'dash'},
            'marker': {'type': 'none'}
        })

        chart.set_title({'name': f"{device_name} Jsc prediction: {self.num_of_points}",
                         'name_font': {'size': self.settings['title_font_size'], 'italic': False, 'bold': False,
                                       'name': 'Calibri (Body)'}})
        chart.set_x_axis({
            'name': self.settings['x_axis_name'],
            # 'min': 0,
            'min': self.min_time,
            'max': self.max_time,
            # 'max': 500,
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            'minor_unit': minor_unit, 'major_unit': minor_unit,
            'major_tick_mark': 'cross', 'minor_tick_mark': 'outside',
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
        })
        chart.set_legend({'position': 'overlay_right',
                          'font': {'size': self.settings['legend_font_size'] - 2, 'bold': False},
                          'layout': {'x': self.settings['legend_area_x'], 'y': self.settings['legend_area_y'] - 0.2,
                                     'width': self.settings['legend_area_width'] + 0.2,
                                     'height': self.settings['legend_area_height'] + 0.2}})
        chart.set_y_axis({'min': self.settings['iv_data']['y_min'],
                          'max': self.settings['iv_data']['y_max'],
                          'name': 'Jsc, mA/cm²',
                          'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
                          'num_font': {'size': self.settings['num_font_size']},
                          'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
                          'major_tick_mark': 'outside'})

        # Add Y data
        chart.add_series({
            'name': [f'{device_name}', j_row_start - 1, y_column],
            'categories': [f'{device_name}', j_row_start, 0, j_row_end, 0],
            'values': [f'{device_name}', j_row_start, y_column, j_row_end, y_column],
            'line': {'width': self.settings['rgb_plot']['line_width'], 'color': 'orange'},
            'marker': {'type': 'none'},
            'y2_axis': True
        })
        chart.set_y2_axis({
            'name': 'Yellow',
            'min': self.settings['rgb_plot']['y_min'], 'max': self.settings['rgb_plot']['y_max'],
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
            'major_tick_mark': 'outside',
        })

        chart.set_plotarea({'border': {'none': True},
                            'layout': {'x': 0.8, 'y': 0.1, 'width': 0.8, 'height': 0.7}})
        chart.set_chartarea({'border': {'none': True}})
        chart.set_size({'x_scale': self.high_settings['chart_x_scale'], 'y_scale': self.high_settings['chart_y_scale']})
        return chart
