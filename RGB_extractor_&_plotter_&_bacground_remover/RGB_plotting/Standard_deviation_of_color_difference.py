from __future__ import annotations

import numpy as np
from typing import List, Tuple


class StandardDeviationForEuclidianDistance:
    def __init__(self, avg_color_per_time_point: List[Tuple[float, ...]],
                 standard_deviation_per_time_point: List[Tuple[float, ...]]):
        """
        Initialize the calculation of the standard deviation for the color difference
        between two sets of color values at different time points in any 3D color space.
        This class calculates the Euclidean distance between average color values to quantify
        the uncertainty in color difference measurement over time.

        :param avg_color_per_time_point: A nested list where each sublist contains the average
                                         color values for a specific time point as a list of three floats
                                         (representing the three dimensions of the color space).
        :param standard_deviation_per_time_point: A list of tuples where each tuple contains the standard
                                                  deviations of the color values for a corresponding time point.
        """
        # Color values for different areas before and after the test
        self.standard_deviation_per_time_point = standard_deviation_per_time_point
        self.avg_color_per_time_point = avg_color_per_time_point
        # Calculating the average color for before and after
        self.average_before = np.asarray(self.avg_color_per_time_point[0][:3], dtype='float32')
        self.average_after = np.asarray(self.avg_color_per_time_point[-1][:3], dtype='float32')

        # Calculating the sample standard deviation for before (matching Excel's STDEV.S)
        self.std_dev_before_sample = np.asarray(self.standard_deviation_per_time_point[0], dtype='float32')
        self.std_dev_after_sample = np.asarray(self.standard_deviation_per_time_point[-1], dtype='float32')
        # Calculating the Euclidean distance for color difference
        self.color_difference = np.sqrt(np.sum((self.average_after - self.average_before) ** 2))

    def direct_standard_deviation_propagation(self):
        """
        Calculate the standard deviation of the color difference using direct standard deviation propagation.

        This method applies the propagation of uncertainty formula to compute the standard deviation of the Euclidean
        color difference, taking into account the variances of the average color values before and after a certain point
        in time.

        :return: The standard deviation of the color difference.
        """
        # Calculate the squared differences for the average color space values
        squared_differences = (self.average_after - self.average_before) ** 2

        # Calculate the combined variances for each color space component
        combined_variances = (self.std_dev_before_sample ** 2) + (self.std_dev_after_sample ** 2)
        # Use the squared differences to weight the combined variances for each color space component
        weighted_variances = squared_differences / self.color_difference ** 2 * combined_variances

        # The variance of the color difference is the sum of the weighted variances
        variance_color_difference = np.sum(weighted_variances)

        # The standard deviation of the color difference is the square root of the variance
        std_dev_color_difference_propagated = np.sqrt(variance_color_difference)
        return std_dev_color_difference_propagated

    def partial_derivative_method(self):
        """
        Calculate the standard deviation of the color difference using the partial derivative method.

        This method uses the partial derivatives of the Euclidean distance formula with respect to each color value
        to compute the standard deviation of the color difference, incorporating the standard deviations of the
        color space values before and after the time point.

        :return: The standard deviation of the Euclidean distance between color space values.
        """
        # Calculating the uncertainty in the Euclidean distance using error propagation
        # Partial derivatives of the Euclidean distance formula with respect to each color space value
        partial_derivatives = (self.average_before - self.average_after) / self.color_difference

        # Squaring each component of the standard deviation and multiplying by the square of the corresponding
        # partial derivative
        variance_before = (partial_derivatives ** 2) * (self.std_dev_before_sample ** 2)
        variance_after = (partial_derivatives ** 2) * (self.std_dev_after_sample ** 2)

        # Summing the variances and taking the square root to get the standard deviation
        total_variance = np.sum(variance_before + variance_after)
        std_dev_distance = np.sqrt(total_variance)
        return std_dev_distance

    def monte_carlo_simulation(self):
        """
        Calculate the standard deviation of the color difference using Monte Carlo simulation.

        This method performs a Monte Carlo simulation to estimate the standard deviation of the color difference
        between color values before and after a time point. It generates random samples based on the average color
        values and their standard deviations, then calculates the color differences for these simulated pairs.

        :return: The standard deviation of the simulated color differences.
        """
        # Define the number of simulations for the Monte Carlo method
        num_simulations = 10000

        # Generate random samples for 'before' and 'after' color values based on their means and standard deviations
        before_samples = np.random.normal(self.average_before, self.std_dev_before_sample, (num_simulations, 3))
        after_samples = np.random.normal(self.average_after, self.std_dev_after_sample, (num_simulations, 3))

        # Calculate the color differences for all the simulated pairs
        simulated_color_differences = np.linalg.norm(after_samples - before_samples, axis=1)

        # Compute the standard deviation of the simulated color differences
        std_dev_simulated = np.std(simulated_color_differences)
        return std_dev_simulated
