"""
Organ Console Generator - Utilities Module

Common utilities and functions shared across all console models.
This module provides:
- DotDict: Parameter dictionary accessor
- create_board: Universal board creation function
- Parameter validation and helpers

Usage:
    from utils import DotDict, create_board

    params = DotDict(parameters)
    board = create_board(
        max_width=500,
        max_height=300,
        board_thickness=18,
        position=(0, 0, 0),
        rotation=(0, 0, 0)
    )
"""

import math
from build123d import *


class DotDict:
    """
    Utility class to convert nested dictionaries to dot-notation accessible objects.

    Allows accessing parameters like p.organ_internal_width_g instead of nested dict access.

    Example:
        params = {
            "General": [
                {"width_g": 1300},
                {"height_g": 800}
            ]
        }
        p = DotDict(params)
        print(p.width_g)  # Access directly as attribute
    """
    def __init__(self, nested_dict):
        for category, items in nested_dict.items():
            for item_dict in items:
                for key, value in item_dict.items():
                    setattr(self, key, value)


def create_board(max_width, max_height, board_thickness, position, rotation,
                min_width=0, min_height=0, rectangular_holes=[], circular_holes=[]):
    """
    Create a board with optional slanted edges and holes using build123d.

    This is the universal board creation function used by all console models.
    It supports rectangular boards, trapezoidal boards (with min_width/min_height),
    and boards with various types of holes.

    Args:
        max_width: Maximum width of the board (mm)
        max_height: Maximum height of the board (mm)
        board_thickness: Thickness of the board (mm)
        position: (x, y, z) position tuple (mm)
        rotation: (rx, ry, rz) rotation tuple in degrees
        min_width: Minimum width for slanted edge (0 for rectangular)
        min_height: Minimum height for slanted edge (0 for rectangular)
        rectangular_holes: List of [x, y, width, height] for rectangular holes
        circular_holes: List of [x, y, diameter] for circular holes

    Returns:
        Part object representing the board

    Example:
        # Simple rectangular board
        board = create_board(
            max_width=500,
            max_height=300,
            board_thickness=18,
            position=(0, 0, 0),
            rotation=(0, 0, 0)
        )

        # Trapezoidal board with a hole
        board = create_board(
            max_width=500,
            max_height=300,
            min_width=400,
            min_height=250,
            board_thickness=18,
            position=(0, 0, 0),
            rotation=(0, 0, 0),
            rectangular_holes=[[250, 150, 100, 50]]
        )
    """
    # Set the min height equal to max height if it's zero (for full rectangle)
    if min_height == 0:
        min_height = max_height

    # Create the points for the board shape
    points = [
        (0, 0),
        (max_width, 0),
        (max_width, min_height),
        (min_width, max_height),
        (0, max_height)
    ]

    if min_width == 0:
        points = [points[0], points[1], points[2], points[4]]  # Remove slanted edge

    # Create the board by extruding the shape
    with BuildPart() as board_builder:
        with BuildSketch(Plane.YZ) as sketch:
            with Locations((0, 0)):
                Polygon(*points, align=(Align.MIN, Align.MIN))

        extrude(amount=board_thickness)

        # Calculate the offset from the center to the bottom-left corner
        x_offset = -max_width / 2
        y_offset = -max_height / 2

        # Add rectangular holes
        for hole in rectangular_holes:
            x, y, hole_width, hole_height = hole
            # Create hole on the top face
            with BuildSketch(board_builder.faces().sort_by(Axis.X)[-1]) as hole_sketch:
                with Locations((x + x_offset, y + y_offset)):
                    Rectangle(hole_width, hole_height)
            extrude(amount=-board_thickness, mode=Mode.SUBTRACT)

        # Add circular holes
        for hole in circular_holes:
            x, y, diameter = hole
            with BuildSketch(board_builder.faces().sort_by(Axis.X)[-1]) as hole_sketch:
                with Locations((x + x_offset, y + y_offset)):
                    Circle(diameter / 2)
            extrude(amount=-board_thickness, mode=Mode.SUBTRACT)

    board = board_builder.part

    # Apply rotations
    if rotation[0] != 0:
        board = Rot(rotation[0], 0, 0) * board
    if rotation[1] != 0:
        board = Rot(0, rotation[1], 0) * board
    if rotation[2] != 0:
        board = Rot(0, 0, rotation[2]) * board

    # Apply translation
    board = Pos(position[0], position[1], position[2]) * board

    return board


def validate_parameters(parameters, required_keys):
    """
    Validate that all required parameter keys are present.

    Args:
        parameters: Parameter dictionary to validate
        required_keys: List of required parameter keys

    Returns:
        tuple: (is_valid, missing_keys)

    Example:
        is_valid, missing = validate_parameters(
            params,
            ['organ_internal_width_g', 'base_height_g']
        )
        if not is_valid:
            print(f"Missing parameters: {missing}")
    """
    p = DotDict(parameters)
    missing = []

    for key in required_keys:
        if not hasattr(p, key):
            missing.append(key)

    return len(missing) == 0, missing


def calculate_board_area(board_list):
    """
    Calculate total board area from a board list.

    Args:
        board_list: List of board dictionaries with 'width' and 'height' keys

    Returns:
        float: Total area in square meters

    Example:
        board_list = generate_board_list(params)
        total_area = calculate_board_area(board_list)
        print(f"Total area: {total_area:.2f} m²")
    """
    total_area = 0
    for board in board_list:
        # Convert from mm² to m²
        area_m2 = (board['width'] * board['height']) / 1_000_000
        total_area += area_m2

    return total_area


def merge_parameter_dicts(*param_dicts):
    """
    Merge multiple parameter dictionaries.

    Args:
        *param_dicts: Variable number of parameter dictionaries

    Returns:
        dict: Merged parameter dictionary

    Example:
        base_params = get_base_parameters()
        custom_params = {"General": [{"custom_g": 100}]}
        merged = merge_parameter_dicts(base_params, custom_params)
    """
    result = {}

    for param_dict in param_dicts:
        for category, items in param_dict.items():
            if category not in result:
                result[category] = []
            result[category].extend(items)

    return result
