from math import log10


def padding(val: int):
    return int(log10(val)) + 1
