from xlsxwriter import Workbook
from xlsxwriter.workbook import ChartScatter

from Instruments import row_to_excel_col, remove_pattern


class ColorChartsCreator:
    def __init__(self, workbook: Workbook, data: dict, settings: dict):
        """
        Initialize ChartsCreator class.
        :param workbook: The xlsxwriter Workbook object where plots are to be added.
        :param data: A dictionary with the raw data
        :param settings: A dictionary with the settings
        """
        self.wb = workbook
        self.high_settings = settings
        self.settings = settings['ChartsCreator']
        self.data = data

    def rgb_scatter(self, device_name: str, column_start: int, data_start: int, data_end: int,
                    title: str = None) -> ChartScatter:
        """
        Create an RGB scatter plot in the Excel worksheet.

        :param device_name: The name of the device for which the chart is being created.
        :param column_start: An iterator for each area and/or average one, i.e., a column number.
        :param data_end: The row number where the data starts.
        :param data_start: The row number where the data ends.
        :param title: String title for the plot.
        :return: The scatter chart object
        """
        column = (column_start - 1) * 4 + 2
        chart = self.wb.add_chart({'type': 'scatter'})
        settings = self.settings['rgb_plot']
        # chart.set_style(3)
        colors = ['red', 'green', 'blue']
        for i, color in enumerate(colors):

            # Initialize empty dictionary for y_error_bars
            y_error_bars = {}

            # If the title is provided, add error bars to series
            if title is not None:
                # Convert the column number to Excel-style column letter
                stdev_col_letter = row_to_excel_col(self.high_settings['Starting columns']['STDEV'] + i + 1)

                y_error_bars = {
                    'type': self.settings['error_bar_type'],
                    'plus_values': f"='{device_name}'!${stdev_col_letter}${data_start + 1}:${stdev_col_letter}${data_end + 1}",
                    'minus_values': f"='{device_name}'!${stdev_col_letter}${data_start + 1}:${stdev_col_letter}${data_end + 1}",
                    'line': {'color': color}
                }
            chart.add_series({
                'name': [f'{device_name}', data_start - 1, i + column],
                'categories': [f'{device_name}', data_start, 0, data_end, 0],
                'values': [f'{device_name}', data_start, column + i, data_end, column + i],
                'line': {'color': color, 'width': settings['line_width']},
                'marker': {
                    'type': settings['marker']['type'][i], 'size': self.settings['marker_size'],
                    'border': {'color': color, },
                    'fill': {'color': color, 'transparency': settings['marker']['transparency'][i]}},
                'y_error_bars': y_error_bars,
            })
        if title is None:
            name = f'Area {column_start}'
        else:
            name = title
        chart.set_title({'name': f"{remove_pattern(device_name)} {name} RGB values",
                         'name_font': {'size': self.settings['title_font_size'], 'italic': False, 'bold': False,
                                       'name': 'Calibri (Body)'}})  # 'color': text_colour}})

        chart.set_x_axis({
            'name': self.settings['x_axis_name'],
            'min': self.settings['min_time'], 'max': self.settings['max_time'],
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            'minor_unit': self.settings['minor_unit'], 'major_unit': self.settings['major_unit'],
            'major_tick_mark': 'cross', 'minor_tick_mark': 'outside',
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
        })
        chart.set_y_axis({
            'name': settings['y_axis_name'],
            'min': settings['y_min'], 'max': settings['y_max'],
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
            'major_tick_mark': 'outside',
        })
        chart.set_legend({'position': 'overlay_right',
                          'font': {'size': self.settings['legend_font_size'], 'bold': False},
                          'layout': {'x': self.settings['legend_area_x'], 'y': self.settings['legend_area_y'],
                                     'width': self.settings['legend_area_width'],
                                     'height': self.settings['legend_area_height']}})
        chart.set_plotarea({'border': {'none': True},
                            'layout': {'x': self.settings['plot_area_x'], 'y': self.settings['plot_area_y'],
                                       'width': self.settings['plot_area_width'],
                                       'height': self.settings['plot_area_height']}})
        chart.set_chartarea({'border': {'none': True}})
        chart.set_size({'x_scale': self.high_settings['chart_x_scale'], 'y_scale': self.high_settings['chart_y_scale']})
        return chart

    def cmyk_scatter(self, device_name: str, data_start: int, data_end: int) -> ChartScatter:
        """
        Create a CMYK scatter plot in the Excel worksheet.

        :param device_name: The name of the device for which the chart is being created.
        :param data_end: The row number where the data starts.
        :param data_start: The row number where the data ends.
        :return: The scatter chart object
        """
        chart = self.wb.add_chart({'type': 'scatter'})
        components = ['cyan', 'magenta', 'yellow', 'black']
        column = self.high_settings['Starting columns']['CMYK']
        for i, component in enumerate(components):
            chart.add_series({
                'name': [f'{device_name}', data_start - 1, i + column],
                'categories': [f'{device_name}', data_start, 0, data_end, 0],
                'values': [f'{device_name}', data_start, column + i, data_end, column + i],
                'line': {'color': component, 'width': self.settings['rgb_plot']['line_width']},
                'marker': {
                    'type': self.settings['rgb_plot']['marker']['type'].get(i, 'circle'),
                    'size': self.settings['marker_size'],
                    'border': {'color': component},
                    'fill': {'color': component,
                             'transparency': self.settings['rgb_plot']['marker']['transparency'].get(i, 0)},
                    # Default to 0 if not specified
                },
            })
        chart.set_title({'name': f"{device_name} CMYK values",
                         'name_font': {'size': self.settings['title_font_size'], 'italic': False, 'bold': False,
                                       'name': 'Calibri (Body)'}})

        chart.set_x_axis({
            'name': self.settings['x_axis_name'],
            'min': self.settings['min_time'], 'max': self.settings['max_time'],
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            'minor_unit': self.settings['minor_unit'], 'major_unit': self.settings['major_unit'],
            'major_tick_mark': 'cross', 'minor_tick_mark': 'outside',
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
        })
        chart.set_y_axis({
            'name': 'CMYK components',
            'min': self.settings['CMYK']['y_min'], 'max': self.settings['CMYK']['y_max'],
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            # 'minor_unit': None, 'major_unit': 50,
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
            'major_tick_mark': 'outside',
        })
        chart.set_legend({'position': 'overlay_right',
                          'font': {'size': self.settings['legend_font_size'], 'bold': False},
                          'layout': {'x': self.settings['legend_area_x'], 'y': self.settings['legend_area_y'],
                                     'width': self.settings['legend_area_width'],
                                     'height': self.settings['legend_area_height']}})
        chart.set_plotarea({'border': {'none': True},
                            'layout': {'x': self.settings['plot_area_x'], 'y': self.settings['plot_area_y'],
                                       'width': self.settings['plot_area_width'],
                                       'height': self.settings['plot_area_height']}})
        chart.set_chartarea({'border': {'none': True}})
        chart.set_size({'x_scale': self.high_settings['chart_x_scale'], 'y_scale': self.high_settings['chart_y_scale']})
        return chart

    def hsl_hsv_scatter(self, device_name: str, data_start: int, data_end: int, color_mode: str) -> ChartScatter:
        """
        Create either an HSL or HSV scatter plot in the Excel worksheet based on the color_mode parameter.

        :param device_name: The name of the device for which the chart is being created.
        :param data_end: The row number where the data starts.
        :param data_start: The row number where the data ends.
        :param color_mode: Either 'HSL' or 'HSV' to specify the color mode.
        :return: The scatter chart object
        """
        chart = self.wb.add_chart({'type': 'scatter'})

        if color_mode == 'HSL':
            components = [('hue', 'purple'), ('saturation', 'orange'), ('lightness', 'gray')]
            column = self.high_settings['Starting columns']['HSL']
        elif color_mode == 'HSV':
            components = [('hue', 'purple'), ('saturation', 'orange'), ('value', 'gray')]
            column = self.high_settings['Starting columns']['HSV']
        else:
            raise ValueError("Invalid color_mode. Choose either 'HSL' or 'HSV'.")

        for i, (component, color) in enumerate(components):
            chart.add_series({
                'name': [f'{device_name}', data_start - 1, i + column],
                'categories': [f'{device_name}', data_start, 0, data_end, 0],
                'values': [f'{device_name}', data_start, column + i, data_end, column + i],
                'line': {'color': color, 'width': self.settings['rgb_plot']['line_width']},
                'marker': {
                    'type': self.settings['rgb_plot']['marker']['type'].get(i, 'circle'),
                    'size': self.settings['marker_size'],
                    'border': {'color': color},
                    'fill': {'color': color,
                             'transparency': self.settings['rgb_plot']['marker']['transparency'].get(i, 0)},
                },
                'y2_axis': i == 0,  # Using secondary y-axis for the first component (hue)
            })

        chart.set_title({'name': f"{device_name} {color_mode} values",
                         'name_font': {'size': self.settings['title_font_size'], 'italic': False, 'bold': False,
                                       'name': 'Calibri (Body)'}})

        chart.set_x_axis({
            'name': self.settings['x_axis_name'],
            'min': self.settings['min_time'], 'max': self.settings['max_time'],
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            'minor_unit': self.settings['minor_unit'], 'major_unit': self.settings['major_unit'],
            'major_tick_mark': 'cross', 'minor_tick_mark': 'outside',
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
        })

        chart.set_y_axis({
            'name': f"{color_mode} components",
            'min': self.settings[f'{color_mode}']['y_min'], 'max': self.settings[f'{color_mode}']['y_max'],
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
            'major_tick_mark': 'outside',
        })

        chart.set_y2_axis({
            'name': 'Hue',
            'min': self.settings[f'{color_mode}']['hue_min'], 'max': self.settings[f'{color_mode}']['hue_max'],
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
            'major_tick_mark': 'outside',
        })

        chart.set_legend({'position': 'overlay_right',
                          'font': {'size': self.settings['legend_font_size'], 'bold': False},
                          'layout': {'x': self.settings['legend_area_x'], 'y': self.settings['legend_area_y'] + 0.1,
                                     'width': self.settings['legend_area_width'],
                                     'height': self.settings['legend_area_height']}})

        chart.set_plotarea({'border': {'none': True},
                            'layout': {'x': self.settings['plot_area_x'] - 0.65, 'y': self.settings['plot_area_y'],
                                       'width': self.settings['plot_area_width'] - 0.23,
                                       'height': self.settings['plot_area_height']}})

        chart.set_chartarea({'border': {'none': True}})

        chart.set_size({'x_scale': self.high_settings['chart_x_scale'], 'y_scale': self.high_settings['chart_y_scale']})

        return chart

    def initial_vs_final_column_chart(self, device_name: str, start_row: int) -> ChartScatter:
        """
        Create a column chart for initial vs final comparison.

        :param device_name: The name of the device for which the chart is being created.
        :param start_row: The row number for initial data.
        :return: The column chart object
        """
        chart = self.wb.add_chart({'type': 'column'})
        col_start = self.high_settings['Starting columns']['Initial vs final']
        # Add initial series
        chart.add_series({
            'name': [f'{device_name}', start_row, col_start],
            'categories': [f'{device_name}', start_row - 1, col_start + 1, start_row - 1, col_start + 3],
            'values': [f'{device_name}', start_row, col_start + 1, start_row, col_start + 3],
            'overlap': -27,
            'points': [{'fill': {'color': 'red'}, 'line': {'color': 'red'}},
                       {'fill': {'color': 'green'}, 'line': {'color': 'green'}},
                       {'fill': {'color': 'blue'}, 'line': {'color': 'blue'}}],
        })

        # Add final series
        chart.add_series({
            'name': [f'{device_name}', start_row + 1, col_start],
            'categories': [f'{device_name}', start_row - 1, col_start + 1, start_row - 1, col_start + 3],
            'values': [f'{device_name}', start_row + 1, col_start + 1, start_row + 1, col_start + 3],
            'points': [{'line': {'color': 'red'},
                        'pattern': {'pattern': 'wide_upward_diagonal', 'fg_color': 'red'}},
                       {'line': {'color': 'green'},
                        'pattern': {'pattern': 'wide_upward_diagonal', 'fg_color': 'green'}},
                       {'line': {'color': 'blue'},
                        'pattern': {'pattern': 'wide_upward_diagonal', 'fg_color': 'blue'}}]})

        chart.set_title({'name': f"{device_name} Initial vs Final",
                         'name_font': {'size': self.settings['title_font_size'] - 2, 'italic': False, 'bold': False,
                                       'name': 'Calibri (Body)'}})
        chart.set_x_axis({'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
                          'num_font': {'size': self.settings['num_font_size']}})
        chart.set_y_axis({
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            'min': 0, 'max': 255,

            'minor_unit': None, 'major_unit': 50,
            'major_gridlines': {'visible': False},
            'minor_gridlines': {'visible': False},
            'major_tick_mark': 'outside'})
        chart.set_legend({'none': True})
        chart.set_plotarea({'border': {'none': True},
                            'layout': {'x': 0.8, 'y': 0.15, 'width': 0.8, 'height': 0.7}})
        chart.set_chartarea({'border': {'none': True}})
        chart.set_size({'x_scale': self.settings['rgb_column_chart_x_scale'],
                        'y_scale': self.settings['rgb_column_chart_y_scale']})

        return chart

    def lab_scatter_chart(self, device_name: str, data_start: int, data_end: int) -> ChartScatter:
        """
        Create a CIELAB scatter plot in the Excel worksheet.

        :param device_name: The name of the device for which the chart is being created.
        :param data_end: The row number where the data starts.
        :param data_start: The row number where the data ends.
        :return: The scatter chart object
        """
        chart = self.wb.add_chart({'type': 'scatter'})
        components = [('L*', 'black'), ('a*', 'orange'), ('b*', 'purple')]
        column = self.high_settings['Starting columns']['LAB']

        for i, (component, color) in enumerate(components):
            y_error_bars = {}
            if self.high_settings['LAB_standard_deviation_compute']:
                stdev_col_letter = row_to_excel_col(self.high_settings['Starting columns']['LAB_std_dev'] + i + 1)
                y_error_bars = {
                    'type': self.settings['error_bar_type'],
                    'plus_values': f"='{device_name}'!${stdev_col_letter}${data_start + 1}:"
                                   f"${stdev_col_letter}${data_end + 1}",
                    'minus_values': f"='{device_name}'!${stdev_col_letter}${data_start + 1}:"
                                    f"${stdev_col_letter}${data_end + 1}",
                    'line': {'color': color}
                }
            chart.add_series({
                'name': [f'{device_name}', data_start - 1, i + column],
                'categories': [f'{device_name}', data_start, 0, data_end, 0],
                'values': [f'{device_name}', data_start, column + i, data_end, column + i],
                'line': {'color': color, 'width': self.settings['rgb_plot']['line_width']},
                'marker': {
                    'type': self.settings['rgb_plot']['marker']['type'].get(i, 'circle'),
                    'size': self.settings['marker_size'],
                    'border': {'color': color},
                    'fill': {'color': color,
                             'transparency': self.settings['rgb_plot']['marker']['transparency'].get(i, 0)},
                    # Default to 0 if not specified
                },
                'y_error_bars': y_error_bars,
            })
        chart.set_title({'name': f"{device_name} CIELAB ΔE*",
                         'name_font': {'size': self.settings['title_font_size'], 'italic': False, 'bold': False,
                                       'name': 'Calibri (Body)'}})

        chart.set_x_axis({
            'name': self.settings['x_axis_name'],
            'min': self.settings['min_time'], 'max': self.settings['max_time'],
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            'minor_unit': self.settings['minor_unit'], 'major_unit': self.settings['major_unit'],
            'major_tick_mark': 'cross', 'minor_tick_mark': 'outside',
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
        })
        chart.set_y_axis({
            'name': 'L*a*b*',
            'min': self.settings['LAB']['y_min'], 'max': self.settings['LAB']['y_max'],
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            # 'minor_unit': None, 'major_unit': 50,
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
            'major_tick_mark': 'outside',
        })
        chart.set_legend({'position': 'overlay_right',
                          'font': {'size': self.settings['legend_font_size'], 'bold': False},
                          'layout': {'x': self.settings['legend_area_x'], 'y': self.settings['legend_area_y'],
                                     'width': self.settings['legend_area_width'],
                                     'height': self.settings['legend_area_height']}})
        chart.set_plotarea({'border': {'none': True},
                            'layout': {'x': self.settings['plot_area_x'], 'y': self.settings['plot_area_y'],
                                       'width': self.settings['plot_area_width'],
                                       'height': self.settings['plot_area_height']}})
        chart.set_chartarea({'border': {'none': True}})
        chart.set_size({'x_scale': self.high_settings['chart_x_scale'], 'y_scale': self.high_settings['chart_y_scale']})
        return chart

    def lab_delta_scatter_chart(self, device_name: str, data_start: int, data_end: int) -> ChartScatter:
        """
        Create a CIELAB changes scatter plot in the Excel worksheet.

        :param device_name: The name of the device for which the chart is being created.
        :param data_end: The row number where the data starts.
        :param data_start: The row number where the data ends.
        :return: The scatter chart object
        """
        chart = self.wb.add_chart({'type': 'scatter'})
        # Wrapp a setting's key-value around this:
        components = [('L*', 'black'), ('a*', 'orange'), ('b*', 'purple')]
        # components = [('L*', 'black')] #, ('a*', 'orange'), ('b*', 'purple')]
        # components = [('a*', 'orange')] #, ('b*', 'purple')]
        column = self.high_settings['Starting columns']['LAB delta']

        for i, (component, color) in enumerate(components):
            chart.add_series({
                'name': [f'{device_name}', data_start - 1, i + column],
                'categories': [f'{device_name}', data_start, 0, data_end, 0],
                'values': [f'{device_name}', data_start, column + i, data_end, column + i],
                'line': {'color': color, 'width': self.settings['rgb_plot']['line_width']},
                'marker': {
                    'type': self.settings['rgb_plot']['marker']['type'].get(i, 'circle'),
                    'size': self.settings['marker_size'],
                    'border': {'color': color},
                    'fill': {'color': color,
                             'transparency': self.settings['rgb_plot']['marker']['transparency'].get(i, 0)},
                    # Default to 0 if not specified
                },
            })
        chart.set_title({'name': f"{device_name} CIELAB ΔE* delta",
                         'name_font': {'size': self.settings['title_font_size'], 'italic': False, 'bold': False,
                                       'name': 'Calibri (Body)'}})

        chart.set_x_axis({
            'name': self.settings['x_axis_name'],
            'min': self.settings['min_time'], 'max': self.settings['max_time'],
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            'minor_unit': self.settings['minor_unit'], 'major_unit': self.settings['major_unit'],
            'major_tick_mark': 'cross', 'minor_tick_mark': 'outside',
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
        })
        chart.set_y_axis({
            'name': 'L*a*b*',
            'min': self.settings['LAB_delta']['y_min'], 'max': self.settings['LAB_delta']['y_max'],
            # 'min': -2, 'max': 2,
            'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
            'num_font': {'size': self.settings['num_font_size']},
            # 'minor_unit': None, 'major_unit': 50,
            'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
            'major_tick_mark': 'outside',
        })
        chart.set_legend({'position': 'overlay_right',
                          'font': {'size': self.settings['legend_font_size'], 'bold': False},
                          'layout': {'x': self.settings['legend_area_x'], 'y': self.settings['legend_area_y'],
                                     'width': self.settings['legend_area_width'],
                                     'height': self.settings['legend_area_height']}})
        chart.set_plotarea({'border': {'none': True},
                            'layout': {'x': self.settings['plot_area_x'], 'y': self.settings['plot_area_y'],
                                       'width': self.settings['plot_area_width'],
                                       'height': self.settings['plot_area_height']}})
        chart.set_chartarea({'border': {'none': True}})
        chart.set_size({'x_scale': self.high_settings['chart_x_scale'], 'y_scale': self.high_settings['chart_y_scale']})
        return chart
