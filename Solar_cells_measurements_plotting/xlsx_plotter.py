import os
import time
import xlsxwriter
import instruments
from datetime import date

from read_iv import ReadData


class PlotIV(ReadData):
    """
    XLSX workbook constructor. Inherits from ReadIv
    :param path_file: the highest path to create a xlsx file
    :param folder_name: optional parameter for nested folder
    :param open_wb: optional parameter to open the workbook if True
    """
    xlsx_location = None
    xlsx_name = None

    def __init__(self, path_file: str, folder_name='', open_wb=True):
        super().__init__(path_file)

        self.folder_name = folder_name
        self._indicator = os.path.basename(os.path.dirname(self.path_file))  # See scratch.txt. "indicator" here stands
        # for the experiment name

        self.col_start = 0
        self.active_area = 80
        self.workbook = self.create_workbook()
        self.center = self.workbook.add_format({'align': 'center'})
        self.wb_main = self.workbook.add_worksheet('Total')
        self.wb_table = self.workbook.add_worksheet('Tabel_Total')
        self.set_worksheets()
        self.fill_table()
        # Keep this one the last
        self.workbook.close()
        if open_wb:
            time.sleep(0.2)
            instruments.open_file(self.xlsx_name)

    def create_workbook(self):
        """
        Creating new xlsx doc and/or folder for it
        :return: Workbook
        """
        self.xlsx_location = instruments.create_folder(self.path_file, self.folder_name)
        # self.test_name.append(self.xlsx_location)  # Check this line
        self.xlsx_name = self.xlsx_location + str(date.today()) + ' ' + self._indicator + ' ' + "JV plots and " \
                                                                                                "calculations.xlsx"
        self.workbook = xlsxwriter.Workbook(self.xlsx_name, {'strings_to_numbers': True})
        return self.workbook

    def set_worksheets(self):
        self.wb_main.insert_chart(0, 1, self.add_all_together_plot())
        for row_index in range(1, len(self.data) + 1):
            ws = self.workbook.add_worksheet(f"{self.data[f'{row_index}']['File name']}")
            self.wb_table.write(row_index, 0, f"{self.data[f'{row_index}']['File name'].split('.')[0]}")
            ws.write(0, self.col_start, 'I', self.center)
            ws.write(0, self.col_start + 1, 'V', self.center)
            ws.write(0, self.col_start + 2, 'P', self.center)
            ws.write(0, self.col_start + 3, 'Parameters', self.center)
            ws.write(1, self.col_start + 3, 'Isc, mA')
            ws.write(2, self.col_start + 3, 'Voc, mV')
            ws.write(3, self.col_start + 3, 'Ƞ')
            ws.write(4, self.col_start + 3, 'FF')
            ws.write(5, self.col_start + 3, 'Max power, W')
            ws.write(6, self.col_start + 3, 'Active area, mm^2')
            ws.write(6, self.col_start + 4, self.active_area)
            ws.write(0, self.col_start + 4, 'Value', self.center)
            ws.insert_chart(1, 7, self.add_iv_plot(self.data[f'{row_index}']['File name'],
                            len(self.data[f'{row_index}']['IV'].index)))
            self.wb_main.insert_chart(20, (row_index - 1) * 8, self.add_iv_plot(self.data[f'{row_index}']['File name'],
                                      len(self.data[f'{row_index}']['IV'].index)))
            for JV_val in range(len(self.data[f'{row_index}']['IV'].index)):  # Write IV data points
                ws.write_row(JV_val + 1, self.col_start, self.data[f'{row_index}']['IV'].loc[JV_val])
                ws.write_formula(JV_val + 1, self.col_start + 2, f'=A{JV_val + 2}*B{JV_val + 2}')
            # If sign change has been found complete following
            if self.data[f'{row_index}']['Axis crossing']['I'] and self.data[f'{row_index}']['Axis crossing']['V']:
                i_cross_2 = self.data[f'{row_index}']['Axis crossing']['I'] + 2
                i_cross_1 = self.data[f'{row_index}']['Axis crossing']['I'] + 1
                v_cross_1 = self.data[f'{row_index}']['Axis crossing']['V'] + 1
                v_cross_2 = self.data[f'{row_index}']['Axis crossing']['V'] + 2
                ws.write_formula(1, self.col_start + 4, f'=(A{i_cross_2}-A{i_cross_1})/(B{i_cross_2}-B{i_cross_1})*'
                                                        f'(0-B{i_cross_1})+A{i_cross_1}')
                ws.write_formula(2, self.col_start + 4, f'=(B{v_cross_2}-B{v_cross_1})/(A{v_cross_2}-A{v_cross_1})*'
                                                        f'(0-A{v_cross_1})+B{v_cross_1}')
                ws.write_formula(3, self.col_start + 4, f'=E6/E7')
                ws.write_formula(4, self.col_start + 4, f'=E6/(E2*E3)')
                ws.write_formula(5, self.col_start + 4, f'=MAX(C:C)')
            else:
                for little_step in range(1, 6):
                    ws.write_formula(little_step, self.col_start + 4, None)

    def fill_table(self):
        ws = self.wb_table
        ws.write(0, 0, 'Label')
        ws.write(0, 1, 'Sweep')
        ws.write(0, 2, 'Voc, V')
        ws.write(0, 3, 'Jsc, mA/cm^2')
        ws.write(0, 4, 'FF')
        ws.write(0, 5, 'PCE, %')
        ws.write(0, 6, 'Hyst_factor')
        ws.write(0, 7, 'Active area, cm^2')
        for row_index in range(1, len(self.data) + 1):
            sheet_name = self.data[f'{row_index}']['File name']
            ws.write_formula(row_index, 2, f"='{sheet_name}'!E3")
            ws.write_formula(row_index, 3, f"='{sheet_name}'!E2")
            ws.write_formula(row_index, 4, f"='{sheet_name}'!E5")
            ws.write_formula(row_index, 5, f"='{sheet_name}'!E4")
            ws.write_formula(row_index, 7, f"='{sheet_name}'!E7")
        ws.autofilter(0, 0, len(self.data) + 1, 7)

    def add_iv_plot(self, sheet_name, row_len):
        chart_iv = self.workbook.add_chart({'type': 'scatter',
                                            'subtype': 'straight'})  # Delete subtype here to return markers
        chart_iv.add_series({
            'categories': [f'{sheet_name}', 1, 1, row_len, 1],
            'values': [f'{sheet_name}', 1, 0, row_len, 0],
            # 'line': {'width': 2},
        })
        chart_iv.set_title({
            'name': f"{sheet_name}",
            # 'name_font': {
            #     'size': 14,
            #     'italic': False,
            #     'bold': False,
            #     'name': 'Calibri (Body)',
            #     # 'color': ,
            # },
        })
        chart_iv.set_x_axis({
            'name': 'V, mV',
            # 'line': {'color': axis_colour},
            # 'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
            # 'num_font': {'size': num_size, 'color': text_colour},
            # 'min': 0, 'max': max_time,
            # 'minor_unit': 250, 'major_unit': 500,
            # 'major_gridlines': {'visible': False},
            # 'minor_gridlines': {'visible': False},
            'major_tick_mark': 'cross',
            'minor_tick_mark': 'outside',
        })
        chart_iv.set_legend(({'none': True}))
        chart_iv.set_y_axis({
            # 'min': 0, 'max': iv[f'iv_{j}']['max'],
            'name': 'I, mA',
            # 'line': {'color': axis_colour},
            # 'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
            # 'num_font': {'size': num_size, 'color': text_colour},
            'major_gridlines': {'visible': False},
            'minor_gridlines': {'visible': False},
            'major_tick_mark': 'outside',
        })
        # chart_iv.set_plotarea({
        #     'border': {'none': True},
        #     'layout': {
        #         'x': 0.8,
        #         'y': 0.1,
        #         'width': 0.8,
        #         'height': 0.7,
        #     }
        # })
        chart_iv.set_chartarea({'border': {'none': True}})
        chart_iv.set_size({'x_scale': 1, 'y_scale': 1})  # The default chart width x height is 480 x 288 pixels.
        return chart_iv

    def add_all_together_plot(self):

        chart_iv = self.workbook.add_chart({'type': 'scatter',
                                            'subtype': 'straight'})  # Delete subtype here to return markers
        for row_index in range(1, len(self.data) + 1):
            sheet_name = self.data[f'{row_index}']['File name']
            row_len = len(self.data[f'{row_index}']['IV'].index)
            chart_iv.add_series({
                'name': f'{sheet_name}',
                'categories': [f'{sheet_name}', 1, 1, row_len, 1],
                'values': [f'{sheet_name}', 1, 0, row_len, 0],
                # 'line': {'width': 2},
                # 'marker': {
                #     'type': cmyk_lines[f'{i}']['marker'],
                #     'size': marker_size,
                #     # 'border': {'color': CMYK_lines[f'{i}']['colour']},
                #     # 'fill': {'color': CMYK_lines[f'{i}']['colour']},
                # },
                # 'y2_axis': colors[f'cs_{l_v}']['axis'][f'{i}'],
            }),
        chart_iv.set_title({
            'name': 'All together',
            # 'name_font': {
            #     'size': 14,
            #     'italic': False,
            #     'bold': False,
            #     'name': 'Calibri (Body)',
            #     # 'color': ,
            # },
        })
        chart_iv.set_x_axis({
            'name': 'V, mV',
            # 'line': {'color': axis_colour},
            # 'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
            # 'num_font': {'size': num_size, 'color': text_colour},
            # 'min': 0, 'max': max_time,
            # 'minor_unit': 250, 'major_unit': 500,
            # 'major_gridlines': {'visible': False},
            # 'minor_gridlines': {'visible': False},
            'major_tick_mark': 'cross',
            'minor_tick_mark': 'outside',
        })
        chart_iv.set_legend(({'none': False}))
        chart_iv.set_y_axis({
            # 'min': 0, 'max': iv[f'iv_{j}']['max'],
            'name': 'I, mA',
            # 'line': {'color': axis_colour},
            # 'name_font': {'size': axis_size, 'italic': True, 'bold': False, 'color': text_colour},
            # 'num_font': {'size': num_size, 'color': text_colour},
            'major_gridlines': {'visible': False},
            'minor_gridlines': {'visible': False},
            'major_tick_mark': 'outside',
        })
        # chart_iv.set_plotarea({
        #     'border': {'none': True},
        #     'layout': {
        #         'x': 0.8,
        #         'y': 0.1,
        #         'width': 0.8,
        #         'height': 0.7,
        #     }
        # })
        chart_iv.set_chartarea({'border': {'none': True}})
        chart_iv.set_size({'x_scale': 1, 'y_scale': 1})  # The default chart width x height is 480 x 288 pixels.
        return chart_iv
