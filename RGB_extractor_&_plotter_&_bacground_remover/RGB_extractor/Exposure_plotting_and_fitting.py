"""
This script reads RGB color data from a JSON file and extracts specific RGB values associated with
'rectangle_counter': 1. It then performs exponential curve fitting on the G and B channels using
the Scipy curve_fit function. Finally, it plots both the original RGB data points and the fitted
curves for the G and B channels, saving these plots as PNG files.
"""

import json

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit


# Fit function
def fit_function(x, a, b, c):
    return a * np.exp(b * x) + c


# Reading JSON data
json_path = "your_file.json"
with open(json_path, 'r') as f:
    result_data = json.load(f)

# Extracting G and B values for "rectangle_counter": 1 from each image
g_values = []
b_values = []
r_values = []
counters = []

for counter, image_data in result_data.items():
    for rect_data in image_data['rectangles']:
        if rect_data['rectangle_counter'] == 1:
            channel = rect_data['rectangle_color_type']
            if channel == 'R':
                r_values.append(rect_data['avg_color'])
            elif channel == 'G':
                g_values.append(rect_data['avg_color'])
            elif channel == 'B':
                b_values.append(rect_data['avg_color'])
    counters.append(counter)

# Correcting the exposure_values to match the lengths of g_values and b_values
corrected_exposure_values = np.linspace(-0.3, 0.2, len(g_values))

# Fitting the data for G and B channels
params_g, _ = curve_fit(fit_function, corrected_exposure_values, g_values)
params_b, _ = curve_fit(fit_function, corrected_exposure_values, b_values)

# Generating the high-quality plots

# Plotting original RGB data points
plt.figure(figsize=(10, 6), dpi=300)
plt.scatter(counters, r_values, label='R', color='red', marker='o')
plt.scatter(counters, g_values, label='G', color='green', marker='x')
plt.scatter(counters, b_values, label='B', color='blue', marker='s')
plt.xlabel('Counter')
plt.ylabel('Average Color Value')
plt.title('Main R, G, and B values for "rectangle_counter": 1')
plt.legend()
plt.grid(True)
plt.savefig('original_rgb_data.png')

# Plotting the fitted curves for G and B channels
plt.figure(figsize=(12, 6), dpi=300)

# G channel
plt.subplot(1, 2, 1)
plt.scatter(corrected_exposure_values, g_values, label='Data Points (G)', color='green')
plt.plot(corrected_exposure_values, fit_function(corrected_exposure_values, params_g[0], params_g[1], params_g[2]),
         label='Fitted Curve (G)', color='green')
plt.xlabel('Exposure Correction')
plt.ylabel('G Channel Value')
plt.title('Fitted Curve for G Channel')
plt.legend()
plt.grid(True)

# B channel
plt.subplot(1, 2, 2)
plt.scatter(corrected_exposure_values, b_values, label='Data Points (B)', color='blue')
plt.plot(corrected_exposure_values, fit_function(corrected_exposure_values, params_b[0], params_b[1], params_b[2]),
         label='Fitted Curve (B)', color='blue')
plt.xlabel('Exposure Correction')
plt.ylabel('B Channel Value')
plt.title('Fitted Curve for B Channel')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig('fitted_curves_gb_channels.png')
