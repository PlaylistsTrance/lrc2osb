from math import log10


def padding(val: int):
    return int(log10(val)) + 1


def rgb2hex(r: int, g: int, b: int):
    if min(r, g, b) < 0 or max(r, g, b) > 255:
        raise ValueError("Invalid RGB value(s) (accepted range: 0-255)")
    return f"{r:02x}{g:02x}{b:02x}"
