"""
Bench-Style Organ Console Generator - build123d Version

This module generates a horizontal bench-style organ console with:
- Full keyboard area with note stand
- Left and right register knob panels
- Volume pedals
- Speaker compartments
- Multiple shelves and compartments

Usage:
    from console_bench import generate_console, generate_board_list, get_default_parameters

    params = get_default_parameters()
    console_model = generate_console(params)
    board_list = generate_board_list(params)
"""

import math
from build123d import *
from utils import DotDict, create_board


def get_default_parameters():
    """
    Returns the default parameter set for the bench-style organ console.

    Returns:
        dict: Nested dictionary with all console parameters organized by category
    """
    return {
        "General_and_base": [
            {"organ_internal_width_g": 1600},
            {"general_board_thickness_g": 18},
            {"base_height_g": 800},
            {"base_depth_g": 350},
            {"base_front_distance_g": 150},
            {"general_board_offset_g": 10},
            {"general_feet_thickness_g": 50},
            {"note_stand_height_g": 500},
            {"note_stand_angle_g": 10},
            {"note_shelf_height_g": 70}
        ],
        "Keyboard": [
            {"keyboard_width_g": 840},
            {"keyboard_depth_g": 400},
            {"keyboard_height_g": 200},
            {"keyboard_offset_g": 200}
        ],
        "Speakers": [
            {"front_speaker_width_g": 400},
            {"front_speaker_height_g": 200},
            {"side_speaker_width_g": 100},
            {"side_speaker_height_g": 1500},
            {"enable_lateral_speaker_holes_g": False}
        ],
        "Volume_pedals": [
            {"volume_pedals_width_g": 120},
            {"volume_pedals_height_g": 240},
            {"volume_pedals_number_g": 3},
            {"volume_pedals_spacing_g": 10},
            {"volume_pedals_hole_start_height_g": 140}
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
            "name": "Cabinet Top",
            "width": p.base_depth_g + 2 * p.general_board_thickness_g + p.general_board_offset_g,
            "height": p.organ_internal_width_g,
            "thickness": p.general_board_thickness_g,
            "description": "Top of the cabinet"
        },
        {
            "name": "Cabinet Upper Back Panel",
            "width": p.organ_internal_width_g,
            "height": p.keyboard_height_g + p.note_stand_height_g + p.general_board_thickness_g + p.front_speaker_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Upper back panel of the cabinet"
        },
        {
            "name": "Cabinet Lower Back Panel",
            "width": p.organ_internal_width_g,
            "height": p.base_height_g - p.general_board_thickness_g,
            "thickness": p.general_board_thickness_g,
            "description": "Lower back panel of the cabinet"
        },
        {
            "name": "Cabinet Bottom Shelf",
            "width": p.organ_internal_width_g,
            "height": p.base_depth_g - p.base_front_distance_g + p.general_board_offset_g,
            "thickness": p.general_board_thickness_g,
            "description": "The lower shelf under the pedals"
        },
        {
            "name": "Cabinet Bottom Front Panel",
            "width": p.organ_internal_width_g,
            "height": p.volume_pedals_hole_start_height_g - p.general_board_thickness_g,
            "thickness": p.general_board_thickness_g,
            "description": "The lower front board under the pedals"
        },
        {
            "name": "Cabinet Base Front",
            "width": p.organ_internal_width_g,
            "height": p.base_height_g - p.volume_pedals_hole_start_height_g - p.general_board_thickness_g,
            "thickness": p.general_board_thickness_g,
            "description": "The base front board with the hole for pedals"
        },
        {
            "name": "Cabinet Upper Front Panel",
            "width": p.organ_internal_width_g - 2 * p.front_speaker_width_g,
            "height": p.front_speaker_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Upper front panel between front speakers"
        },
        {
            "name": "Cabinet Speaker Shelf",
            "width": p.base_depth_g + p.general_board_thickness_g + p.general_board_offset_g,
            "height": p.organ_internal_width_g,
            "thickness": p.general_board_thickness_g,
            "description": "The shelf for the speakers"
        },
        {
            "name": "Cabinet Left Knobs Panel",
            "width": (p.organ_internal_width_g - p.keyboard_width_g - 2 * p.general_board_thickness_g) / 2,
            "height": p.keyboard_height_g + p.note_stand_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Left register knobs panel"
        },
        {
            "name": "Cabinet Left Knobs Lateral Panel",
            "width": p.base_depth_g + p.general_board_thickness_g + p.general_board_offset_g,
            "height": p.keyboard_height_g + p.note_stand_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Lateral board for the left register block"
        },
        {
            "name": "Cabinet Right Knobs Panel",
            "width": (p.organ_internal_width_g - p.keyboard_width_g - 2 * p.general_board_thickness_g) / 2,
            "height": p.keyboard_height_g + p.note_stand_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Right register knobs panel"
        },
        {
            "name": "Cabinet Right Knobs Lateral Panel",
            "width": p.base_depth_g + p.general_board_thickness_g + p.general_board_offset_g,
            "height": p.keyboard_height_g + p.note_stand_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Lateral board for the right register block"
        },
        {
            "name": "Cabinet Note Stand Upper Panel",
            "width": p.keyboard_width_g,
            "height": p.note_shelf_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "The board on the top of the note stand section"
        },
        {
            "name": "Cabinet Main Shelf",
            "width": p.keyboard_width_g,
            "height": p.base_depth_g + p.base_front_distance_g,
            "thickness": p.general_board_thickness_g,
            "description": "The main shelf for keyboards"
        },
        {
            "name": "Cabinet Main Shelf (Left Part)",
            "width": (p.organ_internal_width_g - p.keyboard_width_g) / 2,
            "height": p.base_depth_g + 2 * p.general_board_thickness_g + p.general_board_offset_g,
            "thickness": p.general_board_thickness_g,
            "description": "Left part of the main shelf under the knobs block"
        },
        {
            "name": "Cabinet Main Shelf (Right Part)",
            "width": (p.organ_internal_width_g - p.keyboard_width_g) / 2,
            "height": p.base_depth_g + 2 * p.general_board_thickness_g + p.general_board_offset_g,
            "thickness": p.general_board_thickness_g,
            "description": "Right part of the main shelf under the knobs block"
        },
        {
            "name": "Note Stand Front Panel",
            "width": p.keyboard_width_g,
            "height": p.note_shelf_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "The front board between keyboard and the note stand"
        },
        {
            "name": "Note Stand Shelf",
            "width": p.keyboard_width_g,
            "height": (p.note_stand_height_g - p.note_shelf_height_g) / math.cos(math.radians(p.note_stand_angle_g)),
            "thickness": p.general_board_thickness_g,
            "description": "The shelf of the note stand calculated according to slope angle"
        },
        {
            "name": "Note Stand",
            "width": p.keyboard_width_g,
            "height": p.note_stand_height_g - p.note_shelf_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "The shelf of the note stand"
        },
        {
            "name": "Cabinet Left Foot",
            "width": p.base_depth_g + 2 * p.general_board_thickness_g + 4 * p.general_board_offset_g,
            "height": p.general_feet_thickness_g,
            "thickness": p.general_feet_thickness_g,
            "description": "The left foot of the cabinet"
        },
        {
            "name": "Cabinet Right Foot",
            "width": p.base_depth_g + 2 * p.general_board_thickness_g + 4 * p.general_board_offset_g,
            "height": p.general_feet_thickness_g,
            "thickness": p.general_feet_thickness_g,
            "description": "The right foot of the cabinet"
        },
        {
            "name": "Cabinet Left Lateral",
            "width": p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g,
            "height": p.base_height_g + p.keyboard_height_g + p.note_stand_height_g + 2 * p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g,
            "thickness": p.general_board_thickness_g,
            "description": "The left lateral board with the hole for the speaker"
        },
        {
            "name": "Cabinet Right Lateral",
            "width": p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g,
            "height": p.base_height_g + p.keyboard_height_g + p.note_stand_height_g + 2 * p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g,
            "thickness": p.general_board_thickness_g,
            "description": "The right lateral board with the hole for the speaker"
        },
        {
            "name": "Volume Pedals",
            "width": p.volume_pedals_width_g,
            "height": p.volume_pedals_height_g,
            "thickness": p.general_board_thickness_g,
            "description": f"The volume pedals (quantity: {p.volume_pedals_number_g})"
        }
    ]

    return board_list


def generate_console(parameters):
    """
    Generate the complete bench-style organ console assembly.

    Args:
        parameters: Parameter dictionary containing all configuration values

    Returns:
        Compound object representing the complete bench console
    """
    p = DotDict(parameters)

    # Set default for show_dimensions if not present
    show_dims = getattr(p, 'show_dimensions_g', False)

    parts = []

    # Cabinet Top
    parts.append(create_board(
        max_width = p.base_depth_g + 2 * p.general_board_thickness_g + p.general_board_offset_g,
        max_height = p.organ_internal_width_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, 0, p.base_height_g + p.keyboard_height_g + p.note_stand_height_g + p.general_board_thickness_g + p.front_speaker_height_g),
        rotation = (0, -90, 0),
        show_dimensions=show_dims
    ))

    # Cabinet Upper Back Panel
    parts.append(create_board(
        max_width = p.organ_internal_width_g,
        max_height = p.keyboard_height_g + p.note_stand_height_g + p.general_board_thickness_g + p.front_speaker_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, 0, p.base_height_g),
        rotation = (0, 0, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Lower Back Panel
    parts.append(create_board(
        max_width = p.organ_internal_width_g,
        max_height = p.base_height_g - p.general_board_thickness_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, 0, 0),
        rotation = (0, 0, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Bottom Shelf
    parts.append(create_board(
        max_width = p.organ_internal_width_g,
        max_height = p.base_depth_g - p.base_front_distance_g + p.general_board_offset_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, p.general_board_thickness_g, p.volume_pedals_hole_start_height_g),
        rotation = (0, 90, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Bottom Front Panel
    parts.append(create_board(
        max_width = p.organ_internal_width_g,
        max_height = p.volume_pedals_hole_start_height_g - p.general_board_thickness_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, p.base_depth_g - p.base_front_distance_g, 0),
        rotation = (0, 0, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Base Front
    parts.append(create_board(
        max_width = p.organ_internal_width_g,
        max_height = p.base_height_g - p.volume_pedals_hole_start_height_g - p.general_board_thickness_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, p.base_depth_g - p.base_front_distance_g, p.volume_pedals_hole_start_height_g),
        rotation = (0, 0, 90),
        rectangular_holes=[[p.organ_internal_width_g/2, p.volume_pedals_hole_start_height_g, p.volume_pedals_number_g * (p.volume_pedals_width_g + p.volume_pedals_spacing_g) + p.volume_pedals_spacing_g, p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g]],
        show_dimensions=show_dims
    ))

    # Cabinet Upper Front Panel
    parts.append(create_board(
        max_width = p.organ_internal_width_g - 2 * p.front_speaker_width_g,
        max_height = p.front_speaker_height_g,
        board_thickness = p.general_board_thickness_g,
        position = ((p.organ_internal_width_g - 2 * p.front_speaker_width_g) / 2, p.base_depth_g + p.general_board_thickness_g, p.base_height_g + p.keyboard_height_g + p.note_stand_height_g + p.general_board_thickness_g),
        rotation = (0, 0, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Speaker Shelf
    parts.append(create_board(
        max_width = p.base_depth_g + p.general_board_thickness_g + p.general_board_offset_g,
        max_height = p.organ_internal_width_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, p.general_board_thickness_g, p.base_height_g + p.keyboard_height_g + p.note_stand_height_g),
        rotation = (0, -90, 0),
        show_dimensions=show_dims
    ))

    # Cabinet Left Knobs Panel
    parts.append(create_board(
        max_width = (p.organ_internal_width_g - p.keyboard_width_g - 2 * p.general_board_thickness_g) / 2,
        max_height = p.keyboard_height_g + p.note_stand_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, p.base_depth_g + p.general_board_thickness_g, p.base_height_g),
        rotation = (0, 0, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Left Knobs Lateral Panel
    parts.append(create_board(
        max_width = p.base_depth_g + p.general_board_thickness_g + p.general_board_offset_g,
        max_height = p.keyboard_height_g + p.note_stand_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.keyboard_width_g / 2, p.general_board_thickness_g, p.base_height_g),
        rotation = (0, 0, 0),
        show_dimensions=show_dims
    ))

    # Cabinet Right Knobs Panel
    parts.append(create_board(
        max_width = (p.organ_internal_width_g - p.keyboard_width_g - 2 * p.general_board_thickness_g) / 2,
        max_height = p.keyboard_height_g + p.note_stand_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (-p.organ_internal_width_g / 2, p.base_depth_g + 2 * p.general_board_thickness_g, p.base_height_g),
        rotation = (0, 0, -90),
        show_dimensions=show_dims
    ))

    # Cabinet Right Knobs Lateral Panel
    parts.append(create_board(
        max_width = p.base_depth_g + p.general_board_thickness_g + p.general_board_offset_g,
        max_height = p.keyboard_height_g + p.note_stand_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (-p.keyboard_width_g / 2 - p.general_board_thickness_g, p.general_board_thickness_g, p.base_height_g),
        rotation = (0, 0, 0),
        show_dimensions=show_dims
    ))

    # Cabinet Note Stand Upper Panel
    parts.append(create_board(
        max_width = p.keyboard_width_g,
        max_height = p.note_shelf_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.keyboard_width_g / 2, p.base_depth_g + p.general_board_thickness_g, p.base_height_g + p.keyboard_height_g + p.note_stand_height_g - p.note_shelf_height_g),
        rotation = (0, 0, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Main Shelf
    parts.append(create_board(
        max_width = p.keyboard_width_g,
        max_height = p.base_depth_g + p.base_front_distance_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.keyboard_width_g / 2, 0, p.base_height_g),
        rotation = (0, 90, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Main Shelf (left part)
    parts.append(create_board(
        max_width = (p.organ_internal_width_g - p.keyboard_width_g) / 2,
        max_height = p.base_depth_g + 2 * p.general_board_thickness_g + p.general_board_offset_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, 0, p.base_height_g),
        rotation = (0, 90, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Main Shelf (right part)
    parts.append(create_board(
        max_width = (p.organ_internal_width_g - p.keyboard_width_g) / 2,
        max_height = p.base_depth_g + 2 * p.general_board_thickness_g + p.general_board_offset_g,
        board_thickness = p.general_board_thickness_g,
        position = (-p.keyboard_width_g / 2, 0, p.base_height_g),
        rotation = (0, 90, 90),
        show_dimensions=show_dims
    ))

    # Note Stand Front Panel
    parts.append(create_board(
        max_width = p.keyboard_width_g,
        max_height = p.note_shelf_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (-p.keyboard_width_g / 2, p.base_depth_g + p.keyboard_offset_g -p.general_board_offset_g - p.general_board_thickness_g - p.keyboard_depth_g, p.base_height_g + p.keyboard_height_g),
        rotation = (0, 0, -90),
        show_dimensions=show_dims
    ))

    # Note Stand Shelf
    parts.append(create_board(
        max_width = p.keyboard_width_g,
        max_height = p.note_shelf_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.keyboard_width_g / 2, p.base_depth_g + p.keyboard_offset_g -p.general_board_offset_g - p.general_board_thickness_g - p.keyboard_depth_g + p.note_shelf_height_g, p.base_height_g + p.keyboard_height_g + p.note_shelf_height_g - p.general_board_thickness_g),
        rotation = (0, -90, 90),
        show_dimensions=show_dims
    ))

    # Note Stand
    parts.append(create_board(
        max_width = p.keyboard_width_g,
        max_height = (p.note_stand_height_g - p.note_shelf_height_g) / math.cos(math.radians(p.note_stand_angle_g)),
        board_thickness = p.general_board_thickness_g,
        position = (-p.keyboard_width_g / 2, p.base_depth_g + p.keyboard_offset_g -p.general_board_offset_g - p.keyboard_depth_g, p.base_height_g + p.keyboard_height_g + p.note_shelf_height_g),
        rotation = (0, p.note_stand_angle_g, -90),
        show_dimensions=show_dims
    ))

    # Cabinet Left Foot
    parts.append(create_board(
        max_width = p.base_depth_g + 2 * p.general_board_thickness_g + 4 * p.general_board_offset_g,
        max_height = p.general_feet_thickness_g,
        board_thickness = p.general_feet_thickness_g,
        position = (p.organ_internal_width_g / 2, 0, 0),
        rotation = (0, 0, 0),
        show_dimensions=show_dims
    ))

    # Cabinet Right Foot
    parts.append(create_board(
        max_width = p.base_depth_g + 2 * p.general_board_thickness_g + 4 * p.general_board_offset_g,
        max_height = p.general_feet_thickness_g,
        board_thickness = p.general_feet_thickness_g,
        position = (-p.organ_internal_width_g / 2 - p.general_feet_thickness_g, 0, 0),
        rotation = (0, 0, 0),
        show_dimensions=show_dims
    ))

    # Cabinet Left Lateral
    left_lateral_holes = []
    if p.enable_lateral_speaker_holes_g:
        left_lateral_holes = [[(p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g) / 2, (p.base_height_g + p.keyboard_height_g + p.note_stand_height_g + p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g) / 2, p.side_speaker_width_g, p.side_speaker_height_g]]

    parts.append(create_board(
        max_width = p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g,
        max_height = p.base_height_g + p.keyboard_height_g + p.note_stand_height_g + 2 * p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, 0, p.general_feet_thickness_g),
        rotation = (0, 0, 0),
        rectangular_holes=left_lateral_holes,
        show_dimensions=show_dims
    ))

    # Cabinet Right Lateral
    right_lateral_holes = []
    if p.enable_lateral_speaker_holes_g:
        right_lateral_holes = [[(p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g) / 2, (p.base_height_g + p.keyboard_height_g + p.note_stand_height_g + p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g) / 2, p.side_speaker_width_g, p.side_speaker_height_g]]

    parts.append(create_board(
        max_width = p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g,
        max_height = p.base_height_g + p.keyboard_height_g + p.note_stand_height_g + 2 * p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g,
        board_thickness = p.general_board_thickness_g,
        position = (-p.organ_internal_width_g / 2 - p.general_board_thickness_g, 0, p.general_feet_thickness_g),
        rotation = (0, 0, 0),
        rectangular_holes=right_lateral_holes,
        show_dimensions=show_dims
    ))

    # Volume pedals
    for i in range(p.volume_pedals_number_g):
        parts.append(create_board(
            max_width = p.volume_pedals_width_g,
            max_height = p.volume_pedals_height_g,
            board_thickness = p.general_board_thickness_g,
            position = ((p.volume_pedals_number_g * (p.volume_pedals_width_g + p.volume_pedals_spacing_g) + p.volume_pedals_spacing_g) / 2 - i * (p.volume_pedals_spacing_g + p.volume_pedals_width_g) - p.volume_pedals_spacing_g, p.base_depth_g - p.base_front_distance_g + p.general_board_thickness_g, p.volume_pedals_hole_start_height_g + 2 * p.volume_pedals_spacing_g),
            rotation = (0, -30, 90),
            show_dimensions=show_dims
        ))

    # Combine all parts into a compound
    result = Compound(children=parts)

    return result


# Main execution for testing
if __name__ == "__main__":
    # Generate the organ console with default parameters
    params = get_default_parameters()
    console = generate_console(params)

    # Display the result (requires ocp_vscode)
    try:
        from ocp_vscode import show
        show(console)
    except ImportError:
        print("Note: Install ocp_vscode to visualize the model")
