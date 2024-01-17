import colorsys
import colour
import numpy as np


def rgb_to_cmyk(r: float, g: float, b: float) -> tuple:
    """
    Convert RGB color to CMYK color.

    :param r: Red component, ranging from 0 to 255.
    :param g: Green component, ranging from 0 to 255.
    :param b: Blue component, ranging from 0 to 255.
    :return: A tuple containing the CMYK components scaled to [0, 100].
    """
    cmyk_scale = 100
    rgb_scale = 255
    if (r, g, b) == (0, 0, 0):
        return 0, 0, 0, cmyk_scale
    c = 1 - r / rgb_scale
    m = 1 - g / rgb_scale
    y = 1 - b / rgb_scale
    min_cmy = min(c, m, y)
    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)
    k = min_cmy
    return c * cmyk_scale, m * cmyk_scale, y * cmyk_scale, k * cmyk_scale


def rgb_to_hsl(r: float, g: float, b: float) -> tuple:
    """
    Convert RGB color to HSL color.

    :param r: Red component, ranging from 0 to 255.
    :param g: Green component, ranging from 0 to 255.
    :param b: Blue component, ranging from 0 to 255.
    :return: A tuple containing the HSL components (H scaled to [0, 360], S and L scaled to [0, 100]).
    """
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return h * 360, s * 100, l * 100


def rgb_to_hsv(r: float, g: float, b: float) -> tuple:
    """
    Convert RGB color to HSV color.

    :param r: Red component, ranging from 0 to 255.
    :param g: Green component, ranging from 0 to 255.
    :param b: Blue component, ranging from 0 to 255.
    :return: A tuple containing the HSV components (H scaled to [0, 360], S and V scaled to [0, 100]).
    """
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return h * 360, s * 100, v * 100


def rgb_to_lab(r: float, g: float, b: float, illuminant: np.ndarray) -> tuple:
    """
    Convert RGB in Adobe RGB (1998) color space color to CIELAB color.

    :param r: Red component, ranging from 0 to 255.
    :param g: Green component, ranging from 0 to 255.
    :param b: Blue component, ranging from 0 to 255.
    :param illuminant: numpy.ndarray representing the CIE xy chromaticity coordinates of the illuminant.
    :return: A tuple containing the CIELAB components (L*, a*, b*).
    """
    # Normalize RGB values to [0, 1] range
    rgb_normalized = np.array([r / 255.0, g / 255.0, b / 255.0])

    # Convert normalized RGB to XYZ in Adobe RGB (1998) color space
    xyz = colour.RGB_to_XYZ(RGB=rgb_normalized, colourspace='Adobe RGB (1998)', illuminant=illuminant)

    # Convert XYZ to LAB
    l, a, b = colour.XYZ_to_Lab(XYZ=xyz, illuminant=illuminant)
    return l, a, b
