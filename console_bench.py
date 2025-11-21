"""
Bench Console Generator - build123d Version

This module generates a simple bench-style console with:
- Bench top
- Left and right side panels
- Feet supports
- Internal shelf

Usage:
    from console_bench_new import generate_console, generate_board_list, get_default_parameters

    params = get_default_parameters()
    console_model = generate_console(params)
    board_list = generate_board_list(params)
"""

from build123d import *
from utils import DotDict, create_board


def get_default_parameters():
    """
    Returns the default parameter set for the bench console.

    Returns:
        dict: Nested dictionary with all console parameters organized by category
    """
    return {
        "General_and_base": [
            {"organ_internal_width_g": 1300},
            {"general_board_thickness_g": 18},
            {"base_height_g": 800},
            {"base_depth_g": 350},
            {"base_front_distance_g": 10},
            {"general_board_offset_g": 10},
            {"general_feet_thickness_g": 50}
        ],
        "Bench": [
            {"bench_depth_g": 350},
            {"bench_height_g": 600},
            {"bench_length_g": 900},
            {"bench_shelf_height_g": 100}
        ]
    }


def generate_board_list(parameters):
    """
    Generate a list of all boards with their dimensions and specifications.

    Args:
        parameters: Parameter dictionary

    Returns:
        List of dictionaries containing board specifications
    """
    p = DotDict(parameters)

    board_list = [
        {
            "name": "Bench Top",
            "width": p.bench_depth_g,
            "height": p.bench_length_g,
            "thickness": p.general_board_thickness_g,
            "description": "Top of the bench"
        },
        {
            "name": "Bench Left",
            "width": p.bench_depth_g - 2 * p.general_board_offset_g,
            "height": p.bench_height_g - p.general_board_thickness_g - p.general_feet_thickness_g,
            "thickness": p.general_board_thickness_g,
            "description": "Left panel of the bench"
        },
        {
            "name": "Bench Right",
            "width": p.bench_depth_g - 2 * p.general_board_offset_g,
            "height": p.bench_height_g - p.general_board_thickness_g - p.general_feet_thickness_g,
            "thickness": p.general_board_thickness_g,
            "description": "Right panel of the bench"
        },
        {
            "name": "Bench Left Foot",
            "width": p.bench_depth_g,
            "height": p.general_feet_thickness_g,
            "thickness": p.general_feet_thickness_g,
            "description": "Left foot of the bench"
        },
        {
            "name": "Bench Right Foot",
            "width": p.bench_depth_g,
            "height": p.general_feet_thickness_g,
            "thickness": p.general_feet_thickness_g,
            "description": "Right foot of the bench"
        },
        {
            "name": "Bench Shelf Back Panel",
            "width": p.bench_length_g - 2 * p.general_board_thickness_g - 2 * p.general_board_offset_g,
            "height": p.bench_shelf_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Bench back panel of the shelf"
        },
        {
            "name": "Bench Shelf",
            "width": p.bench_length_g - 2 * p.general_board_thickness_g - 2 * p.general_board_offset_g,
            "height": p.bench_depth_g - 2 * p.general_board_offset_g,
            "thickness": p.general_board_thickness_g,
            "description": "Bench shelf panel"
        },
        {
            "name": "Bench Holder",
            "width": p.bench_length_g - 2 * p.general_board_thickness_g - 2 * p.general_board_offset_g,
            "height": p.bench_shelf_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Bench side panels holder"
        }
    ]

    return board_list


def generate_console(parameters):
    """
    Generate the complete bench console assembly.

    Args:
        parameters: Parameter dictionary containing all configuration values

    Returns:
        Compound object representing the complete bench console
    """
    p = DotDict(parameters)

    # Set default for show_dimensions if not present
    show_dims = getattr(p, 'show_dimensions_g', False)

    parts = []

    # Bench top
    parts.append(create_board(
        max_width = p.bench_depth_g,
        max_height = p.bench_length_g,
        board_thickness = p.general_board_thickness_g,
        position = (-p.bench_length_g / 2, 0, p.bench_height_g),
        rotation = (0, 90, 0),
        show_dimensions=show_dims
    ))

    # Bench left panel
    parts.append(create_board(
        max_width = p.bench_depth_g - 2 * p.general_board_offset_g,
        max_height = p.bench_height_g - p.general_board_thickness_g - p.general_feet_thickness_g,
        board_thickness = p.general_board_thickness_g,
        position = (-p.bench_length_g / 2 + p.general_board_offset_g, p.general_board_offset_g, p.general_feet_thickness_g),
        rotation = (0, 0, 0),
        show_dimensions=show_dims
    ))

    # Bench right panel
    parts.append(create_board(
        max_width = p.bench_depth_g - 2 * p.general_board_offset_g,
        max_height = p.bench_height_g - p.general_board_thickness_g - p.general_feet_thickness_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.bench_length_g / 2 - p.general_board_offset_g - p.general_board_thickness_g, p.general_board_offset_g, p.general_feet_thickness_g),
        rotation = (0, 0, 0),
        show_dimensions=show_dims
    ))

    # Bench left foot
    parts.append(create_board(
        max_width = p.bench_depth_g,
        max_height = p.general_feet_thickness_g,
        board_thickness = p.general_feet_thickness_g,
        position = (-p.general_feet_thickness_g / 2 - p.bench_length_g / 2 + p.general_board_offset_g + p.general_board_thickness_g / 2, p.general_board_offset_g, 0),
        rotation = (0, 0, 0),
        show_dimensions=show_dims
    ))

    # Bench right foot
    parts.append(create_board(
        max_width = p.bench_depth_g,
        max_height = p.general_feet_thickness_g,
        board_thickness = p.general_feet_thickness_g,
        position = (-p.general_feet_thickness_g / 2 + p.bench_length_g / 2 - p.general_board_offset_g - p.general_board_thickness_g / 2, p.general_board_offset_g, 0),
        rotation = (0, 0, 0),
        show_dimensions=show_dims
    ))

    # Bench shelf back panel
    parts.append(create_board(
        max_width = p.bench_shelf_height_g,
        max_height = p.bench_length_g - 2 * p.general_board_thickness_g - 2 * p.general_board_offset_g,
        board_thickness = p.general_board_thickness_g,
        position = (-p.bench_length_g / 2 + p.general_board_offset_g + p.general_board_thickness_g, 2 * p.general_board_offset_g, p.bench_height_g - p.bench_shelf_height_g - p.general_board_thickness_g),
        rotation = (90, 0, 90),
        show_dimensions=show_dims
    ))

    # Bench shelf
    parts.append(create_board(
        max_width = p.bench_depth_g - 2 * p.general_board_offset_g,
        max_height = p.bench_length_g - 2 * p.general_board_thickness_g - 2 * p.general_board_offset_g,
        board_thickness = p.general_board_thickness_g,
        position = (-p.bench_length_g / 2 + p.general_board_offset_g + p.general_board_thickness_g, p.general_board_offset_g, p.bench_height_g - p.bench_shelf_height_g - p.general_board_thickness_g),
        rotation = (0, 90, 0),
        show_dimensions=show_dims
    ))

    # Bench holder
    parts.append(create_board(
        max_width = p.bench_length_g - 2 * p.general_board_thickness_g - 2 * p.general_board_offset_g,
        max_height = p.bench_shelf_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.bench_length_g / 2 - p.general_board_offset_g - p.general_board_thickness_g, -p.general_board_thickness_g / 2 + p.bench_depth_g / 2, p.bench_height_g / 2 - p.bench_shelf_height_g / 2),
        rotation = (0, 0, 90),
        show_dimensions=show_dims
    ))

    # Combine all parts into a compound
    result = Compound(children=parts)

    return result


# Main execution for testing
if __name__ == "__main__":
    # Generate the bench console with default parameters
    params = get_default_parameters()
    console = generate_console(params)

    # Display the result (requires ocp_vscode)
    try:
        from ocp_vscode import show
        show(console)
    except ImportError:
        print("Note: Install ocp_vscode to visualize the model")
