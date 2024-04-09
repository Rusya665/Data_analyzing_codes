SETTINGS = {
    'color_temperature': None,
    'iv_json': False,
    'iv_to_color_map': None,  # This activates IV data processing
    'prediction_flag': 0,
    'LAB_delta_flag': 0,
    'LAB_standard_deviation_compute': False,
    'Specific Timeline': {},
    'Table_tab': None,
    'samples_number': 1,
    'num_of_points': 'all',  # int for specific point or 'all' for all
    'min_possible_points_for_prediction': 3,  # <- just a threshold to program to execute properly
    'prediction_start_point': 1,  # 0 <- which point to EXCLUDE then doing prediction modeling
    'concatenate_number': 15,
    'initial_predicted_current_avg_time_range_start': 100,  # 50
    'sweep_key': 'Average',
    'chart_x_scale': 0.8,  # 480 pixels
    'chart_y_scale': 0.85,  # 288 pixels
    'all_in_one_chart_x_scale': 1.7,
    'all_in_one_chart_y_scale': 1.7,
    'Starting columns': {  # In python values
        'Average RGB': 2,
        'STDEV': 6,
        'Initial vs final': 10,
        'RGB_Euclidian': 15,
        'LAB': 19,
        'LAB_std_dev': 23,
        'LAB delta': 27,
        'CMYK': 31,
        'HSL': 36,
        'HSV': 40,
        'Color Difference': 44,
        'IV data': 54,
        'Yellow': 64,
        'Prediction': 0,
    },
    'ChartsCreator': {
        'colored_border_thickness': 1,
        'axis_font_size': 12,
        'title_font_size': 14,
        'num_font_size': 10,
        'legend_font_size': 12,
        'max_time': 1000,
        'min_time': 0,
        'time_to_shift_left': None,
        'text_colour': '#595959',
        'axis_colour': '#BFBFBF',
        'error_bar_type': 'custom',
        'major_unit': 2.5,  # Assuming max_time is 10
        'minor_unit': 1.25,  # Assuming max_time is 10
        'plot_area_x': 0.85,
        'plot_area_y': 0.15,
        'plot_area_width': 0.8,
        'plot_area_height': 0.6,
        'rgb_column_chart_x_scale': 0.5,
        'rgb_column_chart_y_scale': 0.7,
        'legend_area_x': 0.85,
        'legend_area_y': 0.45,
        'legend_area_width': 0.15,
        'legend_area_height': 0.3,
        'marker_size': 4,
        'x_axis_name': 'Time, h',
        'rgb_plot': {
            'y_min': 0,
            'y_max': 255,
            'line_width': 2,
            'y_axis_name': 'RGB',
            'marker': {
                'type': {
                    0: 'plus',
                    1: 'x',
                    2: 'circle',
                    3: 'star',
                },
                'transparency': {
                    0: 0,
                    1: 25,
                    2: 50,
                    4: 75,
                }
            }
        },
        'CMYK': {
            'y_min': 0,
            'y_max': 100,
        },
        'HSL': {
            'y_min': 0,
            'y_max': 100,
            'hue_min': 0,
            'hue_max': 360,
        },
        'HSV': {
            'y_min': 0,
            'y_max': 100,
            'hue_min': 0,
            'hue_max': 360,
        },
        'LAB': {
            'y_min': 0,
            'y_max': 130,
        },
        'LAB_delta': {
            'y_min': -2,
            'y_max': 3,
        },
        'iv_data': {
            'y_min': 0,
            'y_max': 15,
            'marker': {'type': 'circle',
                       'size': 5},
            'prediction_time': {'min': 0,
                                'max': 3000, }
        }
    },
    'iv_full_headers': [
        "Efficiency (%)",
        "Short-circuit current density (mA/cm²)",
        "Open circuit voltage (V)",
        "Fill factor",
        "Maximum power (W)",
        "Voltage at MPP (V)",
        "Current density at MPP (mA/cm²)",
        "Series resistance, Rs (ohm)",
        "Shunt resistance, Rsh (ohm)"
    ]
}
