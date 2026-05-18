from enum import Enum

"""
This file houses all the enums used in the fluidics system
"""


class Direction(Enum):
    """
    This enum represents the 2 directions the pump can be in: forward, reverse
    """
    FORWARD = 0
    REVERSE = 1
