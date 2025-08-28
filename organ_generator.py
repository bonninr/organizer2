"""
Organ Cabinet Generator Module

This module contains all the CadQuery geometry generation logic for creating
organ cabinet components. It can be used standalone with VSCode CadQuery viewer
for interactive development and testing.

Usage:
    from organ_generator import generate_general_console, get_default_parameters
    
    # Get default parameters
    params = get_default_parameters()
    
    # Generate the organ cabinet
    organ_model = generate_general_console(params)
    
    # For VSCode CadQuery viewer, you can also call individual functions:
    # board = create_board(width=500, height=300, thickness=18, position=(0,0,0), rotation=(0,0,0))
"""

import cadquery as cq
from enum import Enum


class DotDict:
    """
    Utility class to convert nested dictionaries to dot-notation accessible objects.
    Allows accessing parameters like p.organ_internal_width_g instead of nested dict access.
    """
    def __init__(self, nested_dict):
        for category, items in nested_dict.items():
            # For each dictionary in the list
            for item_dict in items:
                # There should be only one key-value pair in each dictionary
                for key, value in item_dict.items():
                    # Add to flattened dictionary
                    setattr(self, key, value)


def get_default_parameters():
    """
    Returns the default parameter set for the organ cabinet.
    This centralizes all configuration in one place.
    """
    return {
        "General_and_base": [
            {"organ_internal_width_g": 1300},
            {"general_board_thickness_g": 18},
            {"base_height_g": 800},
            {"base_depth_g": 350},
            {"base_front_distance_g": 10}
        ],
        "Volume_pedals": [
            {"volume_pedals_width_g": 12},
            {"volume_pedals_height_g": 24},
            {"volume_pedals_number_g": 2},
            {"volume_pedals_hole_start_height_g": 140}
        ],
        "Top": [
            {"top_depth_g": 650},
            {"top_height_g": 350},
            {"top_notch_start_x_g": 350},
            {"top_notch_start_y_g": 150}
        ]
    }


def create_board(max_width, max_height, board_thickness, position, rotation, 
                min_width=0, min_height=0, rectangular_holes=[], circular_holes=[]):
    """
    Create a board with optional slanted edges and holes.
    
    Args:
        max_width: Maximum width of the board
        max_height: Maximum height of the board
        board_thickness: Thickness of the board
        position: (x, y, z) position tuple
        rotation: (rx, ry, rz) rotation tuple in degrees
        min_width: Minimum width for slanted edge (0 for rectangular)
        min_height: Minimum height for slanted edge (0 for rectangular)
        rectangular_holes: List of [x, y, width, height] for rectangular holes
        circular_holes: List of [x, y, diameter] for circular holes
    
    Returns:
        CadQuery Workplane object representing the board
    """
    # Set the min height equal to max height if it's zero (for full rectangle)
    if min_height == 0:
        min_height = max_height

    # Create the points for the board shape
    points = [
        (0, 0),  # Lower left corner
        (max_width, 0),  # Lower right corner
        (max_width, min_height),  # Upper right corner
        (min_width, max_height),  # Transition for slanted edge
        (0, max_height)  # Upper left corner
    ]

    if min_width == 0:
        del points[3]  # Remove slanted edge if min_width is zero

    # Create the board by extruding the slanted rectangle shape
    board = cq.Workplane("YZ").polyline(points).close().extrude(board_thickness)

    # Calculate the offset from the center to the bottom-left corner
    x_offset = -max_width / 2
    y_offset = -max_height / 2

    # Add rectangular holes
    for hole in rectangular_holes:
        x, y, hole_width, hole_height = hole
        # Subtract half the width and height for bottom-left positioning
        hole_wp = board.faces(">X").workplane(centerOption="CenterOfBoundBox") \
            .transformed(offset=cq.Vector(x + x_offset, y + y_offset))
        board = hole_wp.rect(hole_width, hole_height).cutThruAll()

    # Add circular holes
    for hole in circular_holes:
        x, y, diameter = hole
        # Subtract half the width and height for bottom-left positioning
        hole_wp = board.faces(">X").workplane(centerOption="CenterOfBoundBox") \
            .transformed(offset=cq.Vector(x + x_offset, y + y_offset))
        board = hole_wp.circle(diameter / 2).cutThruAll()

    # Apply rotation and translation to position the board
    board = board.rotate((0, 0, 0), (1, 0, 0), rotation[0])
    board = board.rotate((0, 0, 0), (0, 1, 0), rotation[1])
    board = board.rotate((0, 0, 0), (0, 0, 1), rotation[2])

    board = board.translate(position)

    # Return the final CadQuery object
    return board


def create_2d_board(max_width, max_height, min_width=0, min_height=0, 
                   rectangular_holes=[], circular_holes=[]):
    """
    Create a 2D representation of a board with holes for DXF export.
    
    Args:
        max_width: Maximum width of the board
        max_height: Maximum height of the board
        min_width: Minimum width for slanted edge (0 for rectangular)
        min_height: Minimum height for slanted edge (0 for rectangular)
        rectangular_holes: List of [x, y, width, height] for rectangular holes
        circular_holes: List of [x, y, diameter] for circular holes
    
    Returns:
        CadQuery Workplane object representing the 2D board profile
    """
    # Set the min height equal to max height if it's zero (for full rectangle)
    if min_height == 0:
        min_height = max_height

    # Create the points for the board shape
    points = [
        (0, 0),  # Lower left corner
        (max_width, 0),  # Lower right corner
        (max_width, min_height),  # Upper right corner
        (min_width, max_height),  # Transition for slanted edge
        (0, max_height)  # Upper left corner
    ]

    if min_width == 0:
        del points[3]  # Remove slanted edge if min_width is zero

    # Create the 2D board shape
    board = cq.Workplane("XY").polyline(points).close()

    # Add rectangular holes
    for hole in rectangular_holes:
        x, y, hole_width, hole_height = hole
        # Calculate the bottom-left corner of the rectangle
        x_bl = x - hole_width / 2
        y_bl = y - hole_height / 2
        # Create the rectangular hole
        rect_points = [
            (x_bl, y_bl),
            (x_bl + hole_width, y_bl),
            (x_bl + hole_width, y_bl + hole_height),
            (x_bl, y_bl + hole_height)
        ]
        hole = cq.Workplane("XY").polyline(rect_points).close()
        board = board.cut(hole)

    # Add circular holes
    for hole in circular_holes:
        x, y, diameter = hole
        circle = cq.Workplane("XY").circle(diameter / 2).center(x, y)
        board = board.cut(circle)

    return board


def generate_board_list(parameters):
    """
    Generate a list of all boards with their dimensions and specifications.
    
    Args:
        parameters: Parameter dictionary (will be converted to DotDict)
    
    Returns:
        List of dictionaries containing board specifications
    """
    p = DotDict(parameters)
    
    board_list = [
        {
            "name": "Base Right Table",
            "width": p.base_depth_g,
            "height": p.base_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Right side panel of the base"
        },
        {
            "name": "Base Left Table",
            "width": p.base_depth_g,
            "height": p.base_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Left side panel of the base"
        },
        {
            "name": "Base Back",
            "width": p.organ_internal_width_g,
            "height": p.base_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Back panel of the base"
        },
        {
            "name": "Base Front",
            "width": p.organ_internal_width_g,
            "height": p.base_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Front panel of the base with access hole",
            "rectangular_holes": [[p.organ_internal_width_g/2, 300, 300, 300]]
        },
        {
            "name": "Base Horizontal",
            "width": p.organ_internal_width_g,
            "height": p.top_depth_g,
            "thickness": p.general_board_thickness_g,
            "description": "Horizontal divider between base and top sections"
        },
        {
            "name": "Top Lateral Left",
            "width": p.top_depth_g,
            "height": p.top_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Left side panel of the top section with notch",
            "notes": f"Notch at: X={p.top_notch_start_x_g}mm, Y={p.top_notch_start_y_g}mm",
            "min_width": p.top_notch_start_x_g,
            "min_height": p.top_notch_start_y_g
        },
        {
            "name": "Top Lateral Right",
            "width": p.top_depth_g,
            "height": p.top_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Right side panel of the top section with notch",
            "notes": f"Notch at: X={p.top_notch_start_x_g}mm, Y={p.top_notch_start_y_g}mm",
            "min_width": p.top_notch_start_x_g,
            "min_height": p.top_notch_start_y_g
        },
        {
            "name": "Top Back",
            "width": p.organ_internal_width_g,
            "height": p.top_height_g - 2 * p.general_board_thickness_g,
            "thickness": p.general_board_thickness_g,
            "description": "Back panel of the top section"
        },
        {
            "name": "Top Front",
            "width": p.organ_internal_width_g,
            "height": p.top_height_g - 2 * p.general_board_thickness_g,
            "thickness": p.general_board_thickness_g,
            "description": "Front panel of the top section"
        },
        {
            "name": "Top Lid",
            "width": p.organ_internal_width_g,
            "height": p.base_depth_g,
            "thickness": p.general_board_thickness_g,
            "description": "Lid covering the top section"
        }
    ]
    
    return board_list


def generate_general_console(parameters):
    """
    Generate the complete organ cabinet assembly.
    
    Args:
        parameters: Parameter dictionary containing all configuration values
    
    Returns:
        CadQuery Assembly object representing the complete organ cabinet
    """
    p = DotDict(parameters)
    
    # Base right table
    base_right_table = create_board(
        max_width=p.base_depth_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(- p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 0)
    )

    # Base left table
    base_left_table = create_board(
        max_width=p.base_depth_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.organ_internal_width_g - 2* p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 0)
    )

    # Base back
    base_back = create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 90)
    )

    # Base front
    base_front = create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.base_depth_g-100, 0),
        rotation=(0, 0, 90),
        rectangular_holes=[[p.organ_internal_width_g/2, 300, 300, 300]]
    )

    # Base horizontal
    base_horizontal = create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_depth_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.general_board_thickness_g, p.base_height_g),
        rotation=(0, 90, 90)
    )

    # Top lateral left
    top_lateral_left = create_board(
        max_width=p.top_depth_g,
        max_height=p.top_height_g,
        min_width=p.top_notch_start_x_g,
        min_height=p.top_notch_start_y_g,
        board_thickness=p.general_board_thickness_g,
        position=(- p.general_board_thickness_g, 0, p.base_height_g),
        rotation=(0, 0, 0)
    )

    # Top lateral right
    top_lateral_right = create_board(
        max_width=p.top_depth_g,
        max_height=p.top_height_g,
        min_width=p.top_notch_start_x_g,
        min_height=p.top_notch_start_y_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.organ_internal_width_g - 2* p.general_board_thickness_g, 0, p.base_height_g),
        rotation=(0, 0, 0)
    )

    # Top back
    top_back = create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_height_g - 2 * p.general_board_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, p.base_height_g + p.general_board_thickness_g),
        rotation=(0, 0, 90)
    )

    # Top front
    top_front = create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_height_g - 2 * p.general_board_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.base_depth_g, p.base_height_g + p.general_board_thickness_g),
        rotation=(0, 0, 90)
    )

    # Top lid
    top_lid = create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_depth_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, p.base_height_g + p.top_height_g - p.general_board_thickness_g),
        rotation=(0, 90, 90)
    )

    # Combine all parts
    result = base_right_table.add(base_left_table).add(base_back).add(base_front).add(base_horizontal)
    result = result.add(top_lateral_left).add(top_lateral_right).add(top_back).add(top_front).add(top_lid)
    
    return result


# For VSCode CadQuery viewer compatibility - you can uncomment these lines to test
# if __name__ == "__main__":
#     # Example usage for VSCode CadQuery viewer
#     params = get_default_parameters()
#     organ_cabinet = generate_general_console(params)
#     
#     # You can also test individual boards:
#     # test_board = create_board(500, 300, 18, (0, 0, 0), (0, 0, 0))
#     
#     # The 'organ_cabinet' or 'test_board' variable will be displayed in VSCode CadQuery viewer
