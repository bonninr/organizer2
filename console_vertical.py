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
from keyboard import generate_keyboard_stack, get_keyboard_dimensions


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
        "Keyboard_cabinet": [
            {"keyboard_cabinet_width_g": 900},      # Width of the keyboard cabinet area (for cheeks)
            {"keyboard_cabinet_depth_g": 400},
            {"keyboard_cabinet_height_g": 200},
            {"keyboard_cabinet_offset_g": 200}
        ],
        "Keyboards": [
            {"keyboard_num_manuals_g": 2},           # Number of keyboards (manuals)
            {"keyboard_total_keys_g": 61},           # Total keys (61 = 5 octaves, standard organ manual)
            {"keyboard_total_width_g": 870},         # Total keyboard width (mm) - should be less than cabinet width for cheeks
            {"keyboard_white_key_length_g": 150},    # Visible white key length (mm)
            {"keyboard_white_key_height_g": 15},     # White key height/thickness (mm)
            {"keyboard_black_key_width_ratio_g": 0.65},  # Black key width as ratio of white key width
            {"keyboard_black_key_length_g": 95},     # Black key length (mm)
            {"keyboard_black_key_height_g": 10},     # Black key height above white (mm)
            {"keyboard_key_gap_g": 0.5},             # Gap between keys (mm)
            {"keyboard_base_thickness_g": 10},       # Base plate thickness (mm)
            {"keyboard_vertical_spacing_g": 80},     # Vertical spacing between manuals (mm)
            {"keyboard_depth_offset_g": 130}         # Each higher manual offset back (mm)
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
        ],
        "Knobs": [
            {"enable_knob_holes_g": False},     # Enable knob holes on register panels
            {"knob_columns_g": 8},              # Number of vertical columns
            {"knob_rows_g": 10},                # Number of holes per column
            {"knob_diameter_g": 25},            # Diameter of each knob hole (mm)
            {"knob_vertical_spacing_g": 50},    # Vertical spacing between holes (mm)
            {"knob_horizontal_spacing_g": 60},  # Horizontal spacing between columns (mm)
            {"knob_stagger_offset_g": 25},      # Vertical offset for stagger pattern (mm)
            {"knob_margin_top_g": 50},          # Top margin from panel edge (mm)
            {"knob_margin_side_g": 30}          # Side margin from panel edge (mm)
        ]
    }


def generate_knob_holes(panel_width, panel_height, parameters):
    """
    Generate staggered knob hole positions for register panels.

    Args:
        panel_width: Width of the panel (mm)
        panel_height: Height of the panel (mm)
        parameters: Parameter dictionary

    Returns:
        List of [x, y, diameter] for circular holes
    """
    p = DotDict(parameters)

    holes = []

    # Calculate starting position (centered horizontally, with top margin)
    total_width = (p.knob_columns_g - 1) * p.knob_horizontal_spacing_g
    start_x = (panel_width - total_width) / 2
    start_y = p.knob_margin_top_g

    for col in range(p.knob_columns_g):
        # Alternate the stagger: even columns start at base, odd columns offset
        y_offset = (col % 2) * p.knob_stagger_offset_g

        for row in range(p.knob_rows_g):
            x = start_x + col * p.knob_horizontal_spacing_g
            y = start_y + y_offset + row * p.knob_vertical_spacing_g

            # Check if hole is within panel bounds
            if y + p.knob_diameter_g / 2 <= panel_height:
                holes.append([x, y, p.knob_diameter_g])

    return holes


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
            "height": p.keyboard_cabinet_height_g + p.note_stand_height_g + p.general_board_thickness_g + p.front_speaker_height_g,
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
            "width": (p.organ_internal_width_g - p.keyboard_cabinet_width_g - 2 * p.general_board_thickness_g) / 2,
            "height": p.keyboard_cabinet_height_g + p.note_stand_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Left register knobs panel"
        },
        {
            "name": "Cabinet Left Knobs Lateral Panel",
            "width": p.base_depth_g + p.general_board_thickness_g + p.general_board_offset_g,
            "height": p.keyboard_cabinet_height_g + p.note_stand_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Lateral board for the left register block"
        },
        {
            "name": "Cabinet Right Knobs Panel",
            "width": (p.organ_internal_width_g - p.keyboard_cabinet_width_g - 2 * p.general_board_thickness_g) / 2,
            "height": p.keyboard_cabinet_height_g + p.note_stand_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Right register knobs panel"
        },
        {
            "name": "Cabinet Right Knobs Lateral Panel",
            "width": p.base_depth_g + p.general_board_thickness_g + p.general_board_offset_g,
            "height": p.keyboard_cabinet_height_g + p.note_stand_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Lateral board for the right register block"
        },
        {
            "name": "Cabinet Note Stand Upper Panel",
            "width": p.keyboard_cabinet_width_g,
            "height": p.note_shelf_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "The board on the top of the note stand section"
        },
        {
            "name": "Cabinet Main Shelf",
            "width": p.keyboard_cabinet_width_g,
            "height": p.base_depth_g + p.base_front_distance_g,
            "thickness": p.general_board_thickness_g,
            "description": "The main shelf for keyboards"
        },
        {
            "name": "Cabinet Main Shelf (Left Part)",
            "width": (p.organ_internal_width_g - p.keyboard_cabinet_width_g) / 2,
            "height": p.base_depth_g + 2 * p.general_board_thickness_g + p.general_board_offset_g,
            "thickness": p.general_board_thickness_g,
            "description": "Left part of the main shelf under the knobs block"
        },
        {
            "name": "Cabinet Main Shelf (Right Part)",
            "width": (p.organ_internal_width_g - p.keyboard_cabinet_width_g) / 2,
            "height": p.base_depth_g + 2 * p.general_board_thickness_g + p.general_board_offset_g,
            "thickness": p.general_board_thickness_g,
            "description": "Right part of the main shelf under the knobs block"
        },
        {
            "name": "Note Stand Front Panel",
            "width": p.keyboard_cabinet_width_g,
            "height": p.note_shelf_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "The front board between keyboard and the note stand"
        },
        {
            "name": "Note Stand Shelf",
            "width": p.keyboard_cabinet_width_g,
            "height": (p.note_stand_height_g - p.note_shelf_height_g) / math.cos(math.radians(p.note_stand_angle_g)),
            "thickness": p.general_board_thickness_g,
            "description": "The shelf of the note stand calculated according to slope angle"
        },
        {
            "name": "Note Stand",
            "width": p.keyboard_cabinet_width_g,
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
            "height": p.base_height_g + p.keyboard_cabinet_height_g + p.note_stand_height_g + 2 * p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g,
            "thickness": p.general_board_thickness_g,
            "description": "The left lateral board with the hole for the speaker"
        },
        {
            "name": "Cabinet Right Lateral",
            "width": p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g,
            "height": p.base_height_g + p.keyboard_cabinet_height_g + p.note_stand_height_g + 2 * p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g,
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
        position = (p.organ_internal_width_g / 2, 0, p.base_height_g + p.keyboard_cabinet_height_g + p.note_stand_height_g + p.general_board_thickness_g + p.front_speaker_height_g),
        rotation = (0, -90, 0),
        show_dimensions=show_dims
    ))

    # Cabinet Upper Back Panel
    parts.append(create_board(
        max_width = p.organ_internal_width_g,
        max_height = p.keyboard_cabinet_height_g + p.note_stand_height_g + p.general_board_thickness_g + p.front_speaker_height_g,
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
        position = ((p.organ_internal_width_g - 2 * p.front_speaker_width_g) / 2, p.base_depth_g + p.general_board_thickness_g, p.base_height_g + p.keyboard_cabinet_height_g + p.note_stand_height_g + p.general_board_thickness_g),
        rotation = (0, 0, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Speaker Shelf
    parts.append(create_board(
        max_width = p.base_depth_g + p.general_board_thickness_g + p.general_board_offset_g,
        max_height = p.organ_internal_width_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, p.general_board_thickness_g, p.base_height_g + p.keyboard_cabinet_height_g + p.note_stand_height_g),
        rotation = (0, -90, 0),
        show_dimensions=show_dims
    ))

    # Cabinet Left Knobs Panel
    left_panel_width = (p.organ_internal_width_g - p.keyboard_cabinet_width_g - 2 * p.general_board_thickness_g) / 2
    left_panel_height = p.keyboard_cabinet_height_g + p.note_stand_height_g
    left_knob_holes = generate_knob_holes(left_panel_width, left_panel_height, parameters) if p.enable_knob_holes_g else []

    parts.append(create_board(
        max_width = left_panel_width,
        max_height = left_panel_height,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, p.base_depth_g + p.general_board_thickness_g, p.base_height_g),
        rotation = (0, 0, 90),
        circular_holes = left_knob_holes,
        show_dimensions=show_dims
    ))

    # Cabinet Left Knobs Lateral Panel
    parts.append(create_board(
        max_width = p.base_depth_g + p.general_board_thickness_g + p.general_board_offset_g,
        max_height = p.keyboard_cabinet_height_g + p.note_stand_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.keyboard_cabinet_width_g / 2, p.general_board_thickness_g, p.base_height_g),
        rotation = (0, 0, 0),
        show_dimensions=show_dims
    ))

    # Cabinet Right Knobs Panel
    right_panel_width = (p.organ_internal_width_g - p.keyboard_cabinet_width_g - 2 * p.general_board_thickness_g) / 2
    right_panel_height = p.keyboard_cabinet_height_g + p.note_stand_height_g
    right_knob_holes = generate_knob_holes(right_panel_width, right_panel_height, parameters) if p.enable_knob_holes_g else []

    parts.append(create_board(
        max_width = right_panel_width,
        max_height = right_panel_height,
        board_thickness = p.general_board_thickness_g,
        position = (-p.organ_internal_width_g / 2, p.base_depth_g + 2 * p.general_board_thickness_g, p.base_height_g),
        rotation = (0, 0, -90),
        circular_holes = right_knob_holes,
        show_dimensions=show_dims
    ))

    # Cabinet Right Knobs Lateral Panel
    parts.append(create_board(
        max_width = p.base_depth_g + p.general_board_thickness_g + p.general_board_offset_g,
        max_height = p.keyboard_cabinet_height_g + p.note_stand_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (-p.keyboard_cabinet_width_g / 2 - p.general_board_thickness_g, p.general_board_thickness_g, p.base_height_g),
        rotation = (0, 0, 0),
        show_dimensions=show_dims
    ))

    # Cabinet Note Stand Upper Panel
    parts.append(create_board(
        max_width = p.keyboard_cabinet_width_g,
        max_height = p.note_shelf_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.keyboard_cabinet_width_g / 2, p.base_depth_g + p.general_board_thickness_g, p.base_height_g + p.keyboard_cabinet_height_g + p.note_stand_height_g - p.note_shelf_height_g),
        rotation = (0, 0, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Main Shelf
    parts.append(create_board(
        max_width = p.keyboard_cabinet_width_g,
        max_height = p.base_depth_g + p.base_front_distance_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.keyboard_cabinet_width_g / 2, 0, p.base_height_g),
        rotation = (0, 90, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Main Shelf (left part)
    parts.append(create_board(
        max_width = (p.organ_internal_width_g - p.keyboard_cabinet_width_g) / 2,
        max_height = p.base_depth_g + 2 * p.general_board_thickness_g + p.general_board_offset_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, 0, p.base_height_g),
        rotation = (0, 90, 90),
        show_dimensions=show_dims
    ))

    # Cabinet Main Shelf (right part)
    parts.append(create_board(
        max_width = (p.organ_internal_width_g - p.keyboard_cabinet_width_g) / 2,
        max_height = p.base_depth_g + 2 * p.general_board_thickness_g + p.general_board_offset_g,
        board_thickness = p.general_board_thickness_g,
        position = (-p.keyboard_cabinet_width_g / 2, 0, p.base_height_g),
        rotation = (0, 90, 90),
        show_dimensions=show_dims
    ))

    # Generate keyboards (manuals) on top of the main shelf
    num_manuals = getattr(p, 'keyboard_num_manuals_g', 2)
    if num_manuals > 0:
        # Calculate keyboard dimensions for positioning
        kbd_dims = get_keyboard_dimensions(parameters)
        kbd_width = kbd_dims['width']
        kbd_depth = kbd_dims['depth']

        # Position keyboards centered on the keyboard cabinet area, on top of main shelf
        # Main shelf is at Z = base_height_g, with thickness general_board_thickness_g
        # Cabinet area X runs from -keyboard_cabinet_width_g/2 to +keyboard_cabinet_width_g/2
        # Y runs from 0 (back) to base_depth_g + base_front_distance_g (front)
        # Player sits at high Y values, keys extend toward player (+Y direction)

        # Position keyboard at front of main shelf, centered in the cabinet opening
        shelf_front_y = p.base_depth_g + p.base_front_distance_g
        keyboard_position = (
            -kbd_width / 2,  # Centered in X (keyboard is narrower than cabinet for cheeks)
            shelf_front_y - kbd_depth,  # Back edge positioned so front is at shelf front
            p.base_height_g + p.general_board_thickness_g  # On top of main shelf
        )

        keyboard_stack = generate_keyboard_stack(parameters, base_position=keyboard_position)
        parts.append(keyboard_stack)

    # Note Stand Front Panel
    parts.append(create_board(
        max_width = p.keyboard_cabinet_width_g,
        max_height = p.note_shelf_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (-p.keyboard_cabinet_width_g / 2, p.base_depth_g + p.keyboard_cabinet_offset_g -p.general_board_offset_g - p.general_board_thickness_g - p.keyboard_cabinet_depth_g, p.base_height_g + p.keyboard_cabinet_height_g),
        rotation = (0, 0, -90),
        show_dimensions=show_dims
    ))

    # Note Stand Shelf
    parts.append(create_board(
        max_width = p.keyboard_cabinet_width_g,
        max_height = p.note_shelf_height_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.keyboard_cabinet_width_g / 2, p.base_depth_g + p.keyboard_cabinet_offset_g -p.general_board_offset_g - p.general_board_thickness_g - p.keyboard_cabinet_depth_g + p.note_shelf_height_g, p.base_height_g + p.keyboard_cabinet_height_g + p.note_shelf_height_g - p.general_board_thickness_g),
        rotation = (0, -90, 90),
        show_dimensions=show_dims
    ))

    # Note Stand
    parts.append(create_board(
        max_width = p.keyboard_cabinet_width_g,
        max_height = (p.note_stand_height_g - p.note_shelf_height_g) / math.cos(math.radians(p.note_stand_angle_g)),
        board_thickness = p.general_board_thickness_g,
        position = (-p.keyboard_cabinet_width_g / 2, p.base_depth_g + p.keyboard_cabinet_offset_g -p.general_board_offset_g - p.keyboard_cabinet_depth_g, p.base_height_g + p.keyboard_cabinet_height_g + p.note_shelf_height_g),
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
        left_lateral_holes = [[(p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g) / 2, (p.base_height_g + p.keyboard_cabinet_height_g + p.note_stand_height_g + p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g) / 2, p.side_speaker_width_g, p.side_speaker_height_g]]

    parts.append(create_board(
        max_width = p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g,
        max_height = p.base_height_g + p.keyboard_cabinet_height_g + p.note_stand_height_g + 2 * p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g,
        board_thickness = p.general_board_thickness_g,
        position = (p.organ_internal_width_g / 2, 0, p.general_feet_thickness_g),
        rotation = (0, 0, 0),
        rectangular_holes=left_lateral_holes,
        show_dimensions=show_dims
    ))

    # Cabinet Right Lateral
    right_lateral_holes = []
    if p.enable_lateral_speaker_holes_g:
        right_lateral_holes = [[(p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g) / 2, (p.base_height_g + p.keyboard_cabinet_height_g + p.note_stand_height_g + p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g) / 2, p.side_speaker_width_g, p.side_speaker_height_g]]

    parts.append(create_board(
        max_width = p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g,
        max_height = p.base_height_g + p.keyboard_cabinet_height_g + p.note_stand_height_g + 2 * p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g,
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
