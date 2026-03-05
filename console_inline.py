"""
Inline Console Generator - build123d Version

Simple line-style organ console with:
- Single tall side panels (full height and depth)
- Three-board keyboard table at table_height_g:
    1. Center support board: exactly as wide as the keyboard stack
    2. Left fill board: fills from center board to left side panel
    3. Right fill board: fills from center board to right side panel
- Staircase cheek boards: piled horizontally on the fill-board areas.
  Each level is one board_thickness higher and its depth shortens by
  keyboard_depth_offset_g, so the front edge aligns with the key tip
  of the corresponding manual. Lower boards are longer (manual 1 =
  full depth), upper boards progressively shorter.
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
            {"table_height_g": 720}
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

    kbd_dims = get_keyboard_dimensions(parameters)
    kbd_width = kbd_dims['width']

    bt = p.general_board_thickness_g
    fill_width = (p.organ_internal_width_g - kbd_width) / 2
    inner_depth = p.console_depth_g - bt
    num_manuals = int(getattr(p, 'keyboard_num_manuals_g', 2))
    depth_offset = getattr(p, 'keyboard_depth_offset_g', 130)

    board_list = [
        {
            "name": "Left Side Panel",
            "width": p.console_depth_g,
            "height": p.total_height_g,
            "thickness": bt,
            "description": "Left side panel, full height and depth"
        },
        {
            "name": "Right Side Panel",
            "width": p.console_depth_g,
            "height": p.total_height_g,
            "thickness": bt,
            "description": "Right side panel, full height and depth"
        },
        {
            "name": "Back Panel",
            "width": p.organ_internal_width_g,
            "height": p.total_height_g,
            "thickness": bt,
            "description": "Back panel, full width and height"
        },
        {
            "name": "Top Lid",
            "width": p.organ_internal_width_g,
            "height": inner_depth,
            "thickness": bt,
            "description": "Top lid"
        },
        {
            "name": "Center Keyboard Support Board",
            "width": kbd_width,
            "height": inner_depth,
            "thickness": bt,
            "description": "Horizontal board directly under keyboard, just wide enough for keys"
        },
        {
            "name": "Front Panel",
            "width": p.organ_internal_width_g,
            "height": p.table_height_g,
            "thickness": bt,
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
            "thickness": bt,
            "description": f"Volume pedals (quantity: {p.volume_pedals_number_g})"
        }
    ]

    # Fill boards (n=0) + stacked staircase boards (n=1..N-1).
    # Board n sits at the lateral area, has depth = inner_depth - n * depth_offset.
    # n=0 is the lateral fill board at table level (full inner depth).
    # n=1 is stacked one board_thickness higher, reaching manual 2 key tip. Etc.
    num_levels = max(1, num_manuals)
    for n in range(num_levels):
        depth = inner_depth - n * depth_offset
        if depth <= 0:
            break
        label = "fill board (table level)" if n == 0 else f"staircase step {n} (manual {n + 1} key tip)"
        board_list.append({
            "name": f"Left Lateral Board {n + 1}",
            "width": fill_width,
            "height": depth,
            "thickness": bt,
            "description": f"Left {label}"
        })
        board_list.append({
            "name": f"Right Lateral Board {n + 1}",
            "width": fill_width,
            "height": depth,
            "thickness": bt,
            "description": f"Right {label}"
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
    keyboard_y_offset = getattr(p, 'keyboard_y_offset_g', 0)

    bt = p.general_board_thickness_g
    inner_depth = p.console_depth_g - bt

    # Keyboard dimensions drive the center board width
    kbd_dims = get_keyboard_dimensions(parameters)
    kbd_width = kbd_dims['width']
    kbd_depth = kbd_dims['depth']

    fill_width = (p.organ_internal_width_g - kbd_width) / 2

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

    # --- Three-board keyboard table ---

    # Center keyboard support board (exactly keyboard-wide, full inner depth)
    # X spans: [-bt - fill_width - kbd_width, -bt - fill_width]
    parts.append(create_board(
        max_width=kbd_width,
        max_height=inner_depth,
        board_thickness=bt,
        position=(-bt - fill_width, bt, p.table_height_g),
        rotation=(0, 90, 90),
        show_dimensions=show_dims
    ))

    # Staircase fill/cheek boards on each side.
    # n=0: lateral fill board at table level, depth = inner_depth (reaches manual 1 key tip = console front).
    # n=1..N-1: stacked one board_thickness per level, depth shortens by depth_offset per level
    #           so the front edge aligns with the corresponding manual's key tip.
    num_levels = max(1, num_manuals)
    for n in range(num_levels):
        cheek_depth = inner_depth - n * depth_offset
        if cheek_depth <= 0:
            break
        z = p.table_height_g + n * bt  # stacked: each level sits on top of the previous

        # Right lateral/cheek board: X spans [-bt - fill_width, -bt]
        parts.append(create_board(
            max_width=fill_width,
            max_height=cheek_depth,
            board_thickness=bt,
            position=(-bt, bt, z),
            rotation=(0, 90, 90),
            show_dimensions=show_dims
        ))

        # Left lateral/cheek board: X spans [-bt - fill_width - kbd_width - fill_width, -bt - fill_width - kbd_width]
        parts.append(create_board(
            max_width=fill_width,
            max_height=cheek_depth,
            board_thickness=bt,
            position=(-bt - fill_width - kbd_width, bt, z),
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
    pedal_x_span = pedal_hole_w / 2

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
    # Center the keyboard stack over the center support board.
    # Center of organ in X = -bt - organ_internal_width/2 (same as normal console).
    if num_manuals > 0:
        keyboard_position = (
            -bt - p.organ_internal_width_g / 2 - kbd_width / 2,
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
