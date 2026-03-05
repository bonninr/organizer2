"""
Inline Console Generator - build123d Version

Simple line-style organ console with:
- Single tall side panels (full height and depth)
- Center keyboard table board + staircase cheek boards on each side
  The cheek boards are horizontal, one per keyboard manual level.
  Each board's depth goes from the back wall to the key tip of that manual.
  Lower manuals are more forward so their cheek boards are longer;
  upper manuals step back so their cheek boards are shorter.
- Volume pedals behind a front panel
- Multiple keyboard manuals

Usage:
    from console_inline import generate_console, generate_board_list, get_default_parameters

    params = get_default_parameters()
    console_model = generate_console(params)
    board_list = generate_board_list(params)
"""

from build123d import *
from utils import DotDict, create_board
from keyboard import generate_keyboard_stack, get_keyboard_dimensions


def get_default_parameters():
    """
    Returns the default parameter set for the inline console.

    Returns:
        dict: Nested dictionary with all console parameters organized by category
    """
    return {
        "General_and_base": [
            {"organ_internal_width_g": 1300},
            {"general_board_thickness_g": 18},
            {"total_height_g": 1050},
            {"console_depth_g": 600},
            {"base_front_distance_g": 10}
        ],
        "Table": [
            {"table_height_g": 720},
            {"keyboard_section_width_g": 900}
        ],
        "Volume_pedals": [
            {"volume_pedals_width_g": 120},
            {"volume_pedals_height_g": 240},
            {"volume_pedals_number_g": 3},
            {"volume_pedals_spacing_g": 10},
            {"volume_pedals_hole_start_height_g": 140}
        ],
        "Keyboards": [
            {"keyboard_num_manuals_g": 2},
            {"keyboard_total_keys_g": 61},
            {"keyboard_total_width_g": 870},
            {"keyboard_white_key_length_g": 150},
            {"keyboard_white_key_height_g": 15},
            {"keyboard_black_key_width_ratio_g": 0.65},
            {"keyboard_black_key_length_g": 95},
            {"keyboard_black_key_height_g": 10},
            {"keyboard_key_gap_g": 0.5},
            {"keyboard_base_thickness_g": 10},
            {"keyboard_vertical_spacing_g": 80},
            {"keyboard_depth_offset_g": 130},
            {"keyboard_y_offset_g": 0}
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

    lateral_width = (p.organ_internal_width_g - p.keyboard_section_width_g) / 2
    inner_depth = p.console_depth_g - p.general_board_thickness_g
    num_manuals = int(getattr(p, 'keyboard_num_manuals_g', 2))
    depth_offset = getattr(p, 'keyboard_depth_offset_g', 130)

    board_list = [
        {
            "name": "Left Side Panel",
            "width": p.console_depth_g,
            "height": p.total_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Left side panel, full height and depth"
        },
        {
            "name": "Right Side Panel",
            "width": p.console_depth_g,
            "height": p.total_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Right side panel, full height and depth"
        },
        {
            "name": "Back Panel",
            "width": p.organ_internal_width_g,
            "height": p.total_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Back panel, full width and height"
        },
        {
            "name": "Top Lid",
            "width": p.organ_internal_width_g,
            "height": inner_depth,
            "thickness": p.general_board_thickness_g,
            "description": "Top lid"
        },
        {
            "name": "Center Table Board",
            "width": p.keyboard_section_width_g,
            "height": inner_depth,
            "thickness": p.general_board_thickness_g,
            "description": "Horizontal board under keyboard area"
        },
        {
            "name": "Front Panel",
            "width": p.organ_internal_width_g,
            "height": p.table_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Front panel with volume pedal hole",
            "rectangular_holes": [[
                p.organ_internal_width_g / 2,
                p.volume_pedals_hole_start_height_g + (p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g) / 2,
                p.volume_pedals_number_g * (p.volume_pedals_width_g + p.volume_pedals_spacing_g) + p.volume_pedals_spacing_g,
                p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g
            ]]
        },
        {
            "name": "Volume Pedals",
            "width": p.volume_pedals_width_g,
            "height": p.volume_pedals_height_g,
            "thickness": p.general_board_thickness_g,
            "description": f"Volume pedals (quantity: {p.volume_pedals_number_g})"
        }
    ]

    # Staircase cheek boards: one pair per manual level
    # The N-th board (0-indexed) has depth = inner_depth - N * depth_offset
    # Lower manual (N=0): longest. Upper manuals: progressively shorter.
    num_cheek_levels = max(1, num_manuals)
    for n in range(num_cheek_levels):
        cheek_depth = inner_depth - n * depth_offset
        if cheek_depth <= 0:
            break
        level_label = f"(manual {n + 1})" if num_manuals > 0 else "(table level)"
        board_list.append({
            "name": f"Left Lateral/Cheek Board {n + 1}",
            "width": lateral_width,
            "height": cheek_depth,
            "thickness": p.general_board_thickness_g,
            "description": f"Left staircase cheek board {level_label}, depth to key tip"
        })
        board_list.append({
            "name": f"Right Lateral/Cheek Board {n + 1}",
            "width": lateral_width,
            "height": cheek_depth,
            "thickness": p.general_board_thickness_g,
            "description": f"Right staircase cheek board {level_label}, depth to key tip"
        })

    return board_list


def generate_console(parameters):
    """
    Generate the complete inline console assembly.

    Args:
        parameters: Parameter dictionary containing all configuration values

    Returns:
        Compound object representing the complete inline console
    """
    p = DotDict(parameters)

    show_dims = getattr(p, 'show_dimensions_g', False)
    num_manuals = int(getattr(p, 'keyboard_num_manuals_g', 2))
    depth_offset = getattr(p, 'keyboard_depth_offset_g', 130)
    vertical_spacing = getattr(p, 'keyboard_vertical_spacing_g', 80)
    keyboard_y_offset = getattr(p, 'keyboard_y_offset_g', 0)

    bt = p.general_board_thickness_g
    lateral_width = (p.organ_internal_width_g - p.keyboard_section_width_g) / 2
    inner_depth = p.console_depth_g - bt

    parts = []

    # --- Structural shell ---

    # Right side panel (full height, full depth)
    parts.append(create_board(
        max_width=p.console_depth_g,
        max_height=p.total_height_g,
        board_thickness=bt,
        position=(-bt, 0, 0),
        rotation=(0, 0, 0),
        show_dimensions=show_dims
    ))

    # Left side panel (full height, full depth)
    parts.append(create_board(
        max_width=p.console_depth_g,
        max_height=p.total_height_g,
        board_thickness=bt,
        position=(-(p.organ_internal_width_g + 2 * bt), 0, 0),
        rotation=(0, 0, 0),
        show_dimensions=show_dims
    ))

    # Back panel (full width, full height)
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.total_height_g,
        board_thickness=bt,
        position=(-bt, 0, 0),
        rotation=(0, 0, 90),
        show_dimensions=show_dims
    ))

    # Top lid (horizontal, full width, inner depth)
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=inner_depth,
        board_thickness=bt,
        position=(-bt, bt, p.total_height_g),
        rotation=(0, 90, 90),
        show_dimensions=show_dims
    ))

    # --- Keyboard table area ---

    # Center table board (horizontal at table_height, under keyboards and between cheeks)
    parts.append(create_board(
        max_width=p.keyboard_section_width_g,
        max_height=inner_depth,
        board_thickness=bt,
        position=(-bt - lateral_width, bt, p.table_height_g),
        rotation=(0, 90, 90),
        show_dimensions=show_dims
    ))

    # Staircase cheek boards on each side.
    # For each keyboard level N (0-indexed):
    #   - Height (Z) = table_height_g + N * vertical_spacing_g
    #   - Depth (Y) = inner_depth - N * depth_offset_g
    #     (the board reaches from back wall to the key tip of manual N+1)
    # Board 0 serves as the lateral table board (at table level, full inner depth).
    # Boards 1..N-1 are the stepped cheek boards above.
    num_cheek_levels = max(1, num_manuals)
    for n in range(num_cheek_levels):
        cheek_depth = inner_depth - n * depth_offset
        if cheek_depth <= 0:
            break
        z_level = p.table_height_g + n * vertical_spacing

        # Right lateral/cheek board
        # X spans: [-bt - lateral_width, -bt]
        parts.append(create_board(
            max_width=lateral_width,
            max_height=cheek_depth,
            board_thickness=bt,
            position=(-bt, bt, z_level),
            rotation=(0, 90, 90),
            show_dimensions=show_dims
        ))

        # Left lateral/cheek board
        # X spans: [-bt - lateral_width - keyboard_section_width - lateral_width, -bt - lateral_width - keyboard_section_width]
        parts.append(create_board(
            max_width=lateral_width,
            max_height=cheek_depth,
            board_thickness=bt,
            position=(-bt - lateral_width - p.keyboard_section_width_g, bt, z_level),
            rotation=(0, 90, 90),
            show_dimensions=show_dims
        ))

    # --- Front panel with volume pedal hole ---
    pedal_hole_x = p.organ_internal_width_g / 2
    pedal_hole_y = p.volume_pedals_hole_start_height_g + (p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g) / 2
    pedal_hole_w = (p.volume_pedals_number_g * (p.volume_pedals_width_g + p.volume_pedals_spacing_g)
                    + p.volume_pedals_spacing_g)
    pedal_hole_h = p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g

    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.table_height_g,
        board_thickness=bt,
        position=(-bt, p.console_depth_g - p.base_front_distance_g, 0),
        rotation=(0, 0, 90),
        rectangular_holes=[[pedal_hole_x, pedal_hole_y, pedal_hole_w, pedal_hole_h]],
        show_dimensions=show_dims
    ))

    # --- Volume pedals ---
    pedal_x_center = -bt - p.organ_internal_width_g / 2
    pedal_x_span = (p.volume_pedals_number_g * (p.volume_pedals_width_g + p.volume_pedals_spacing_g)
                    + p.volume_pedals_spacing_g) / 2

    for i in range(p.volume_pedals_number_g):
        pedal_x = (pedal_x_center + pedal_x_span
                   - i * (p.volume_pedals_spacing_g + p.volume_pedals_width_g)
                   - p.volume_pedals_spacing_g)
        parts.append(create_board(
            max_width=p.volume_pedals_width_g,
            max_height=p.volume_pedals_height_g,
            board_thickness=bt,
            position=(pedal_x,
                      p.console_depth_g - p.base_front_distance_g + bt,
                      p.volume_pedals_hole_start_height_g + 2 * p.volume_pedals_spacing_g),
            rotation=(0, -30, 90),
            show_dimensions=show_dims
        ))

    # --- Keyboards ---
    if num_manuals > 0:
        kbd_dims = get_keyboard_dimensions(parameters)
        kbd_width = kbd_dims['width']
        kbd_depth = kbd_dims['depth']

        # Center keyboards in the keyboard section (X), front at console front (Y),
        # sitting on top of the center table board (Z = table_height_g)
        kbd_section_center_x = -bt - lateral_width - p.keyboard_section_width_g / 2
        keyboard_position = (
            kbd_section_center_x - kbd_width / 2,
            p.console_depth_g - kbd_depth + keyboard_y_offset,
            p.table_height_g
        )

        keyboard_stack = generate_keyboard_stack(parameters, base_position=keyboard_position)
        parts.append(keyboard_stack)

    return Compound(children=parts)


# Main execution for testing
if __name__ == "__main__":
    params = get_default_parameters()
    console = generate_console(params)

    try:
        from ocp_vscode import show
        show(console)
    except ImportError:
        print("Note: Install ocp_vscode to visualize the model")
