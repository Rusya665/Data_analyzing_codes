from xlsxwriter import Workbook
from xlsxwriter.workbook import ChartScatter


class IVPlotsCreator:
    def __init__(self, workbook: Workbook, data: dict, settings: dict, mapping_dict: dict):
        """
        Initialize IVPlotsCreator class.

        :param workbook: The xlsxwriter Workbook object where plots are to be added.
        :param data: A dictionary with the raw data.
        :param settings: A dictionary with the settings.
        :param mapping_dict: A dictionary mapping short headers to the full parameter name.
        """
        self.wb = workbook
        self.high_settings = settings
        self.settings = settings['ChartsCreator']
        self.data = data
        self.mapping_dict = mapping_dict

    def create_single_iv_plot(self, device_name: str, column: int, data_start: int, data_end: int,
                              name: str) -> ChartScatter:
        """
        Create a single IV plot for a given device.

        :param device_name: The name of the device for which the IV plot is being created.
        :param column: Current column for each IV parameter.
        :param data_start: The row number where the data starts.
        :param data_end: The row number where the data ends.
        :param name: The chart name.
        :return: The IV plot chart object
        """
        chart = self.wb.add_chart({'type': 'scatter'})
        # name = self.mapping_dict.get(name_key, 'N/A')
        column += self.high_settings['Starting columns']['IV data']
        chart.add_series({
            'categories': [f'{device_name}', data_start, 0, data_end, 0],
            'values': [f'{device_name}', data_start, column, data_end, column],
            'line': {'width': self.settings['rgb_plot']['line_width'], 'color': 'black'},
            'marker': {
                'type': self.settings['iv_data']['marker']['type'],
                'size': self.settings['iv_data']['marker']['size'],
                'border': {'color': 'black'},
                'fill': {'color': 'white'}}
        })
        chart.set_title({'name': f"{device_name} {name}",
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
        chart.set_legend(({'none': True}))
        chart.set_y_axis({'min': self.settings['iv_data']['y_min'],
                          'name': name,
                          'name_font': {'size': self.settings['axis_font_size'], 'italic': False, 'bold': False},
                          'num_font': {'size': self.settings['num_font_size']},
                          'major_gridlines': {'visible': False}, 'minor_gridlines': {'visible': False},
                          'major_tick_mark': 'outside'})
        chart.set_plotarea({'border': {'none': True},
                            'layout': {'x': 0.8, 'y': 0.1, 'width': 0.8, 'height': 0.7}})
        chart.set_chartarea({'border': {'none': True}})
        chart.set_size({'x_scale': self.high_settings['chart_x_scale'], 'y_scale': self.high_settings['chart_y_scale']})
        return chart
