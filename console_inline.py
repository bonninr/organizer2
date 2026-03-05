"""
Inline Console Generator - build123d Version

Line-style organ console where the keyboard table protrudes forward
beyond the cabinet body:

  console_depth_g (~350 mm): depth of the cabinet body (side panels, back,
                             top lid, volume pedal front panel)
  table_depth_g   (~600 mm): total depth of the keyboard table (extends
                             further forward than the cabinet)

The table is composed of three boards at table_height_g:
  1. Center board  – exactly (keyboard_total_width + 2×board_thickness) wide,
                     full table_depth_g deep.  The extra board_thickness on
                     each side is the cheek seat.
  2. Left fill     – fills the lateral gap between center board and left side
  3. Right fill    – fills the lateral gap between center board and right side

  fill_extend_mode (table_fill_extend_g):
    False (default) – fill boards cover only the extension region
                      (table_depth - console_depth, ~25 cm), sitting flush
                      with the front face of the cabinet sides.
    True            – fill boards go the full table depth (with a notch cut
                      noted in the board list where they meet the side panels).

Staircase cheek boards are stacked on top of the fill area (same width,
same Y-start as fill boards).  Each level sits one board_thickness higher
and its depth shortens by keyboard_depth_offset_g, so the front edge aligns
with the corresponding manual's key tips.  Lower boards are longer.

Usage:
    from console_inline import generate_console, generate_board_list, get_default_parameters
"""

from build123d import *
from utils import DotDict, create_board
from keyboard import generate_keyboard_stack, get_keyboard_dimensions


def get_default_parameters():
    return {
        "General_and_base": [
            {"organ_internal_width_g": 1300},
            {"general_board_thickness_g": 18},
            {"total_height_g": 1050},
            {"console_depth_g": 350},
            {"base_front_distance_g": 10}
        ],
        "Table": [
            {"table_height_g": 720},
            {"table_depth_g": 600},
            {"table_fill_extend_g": False}   # True = fill boards go full table depth
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
    p = DotDict(parameters)

    kbd_dims = get_keyboard_dimensions(parameters)
    kbd_width = kbd_dims['width']

    bt = p.general_board_thickness_g
    center_width = kbd_width + 2 * bt
    fill_width = (p.organ_internal_width_g - center_width) / 2
    fill_extend = bool(getattr(p, 'table_fill_extend_g', False))

    # Fill boards start from back-of-cabinet (extend mode) or cabinet front face (short mode)
    fill_depth = (p.table_depth_g - bt) if fill_extend else (p.table_depth_g - p.console_depth_g)

    num_manuals = int(getattr(p, 'keyboard_num_manuals_g', 2))
    depth_offset = getattr(p, 'keyboard_depth_offset_g', 130)
    num_levels = max(1, num_manuals)

    board_list = [
        {
            "name": "Left Side Panel",
            "width": p.console_depth_g,
            "height": p.total_height_g,
            "thickness": bt,
            "description": "Left side panel (cabinet body depth only)"
        },
        {
            "name": "Right Side Panel",
            "width": p.console_depth_g,
            "height": p.total_height_g,
            "thickness": bt,
            "description": "Right side panel (cabinet body depth only)"
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
            "height": p.console_depth_g - bt,
            "thickness": bt,
            "description": "Top lid, covers cabinet body only"
        },
        {
            "name": "Center Keyboard Support Board",
            "width": center_width,
            "height": p.table_depth_g - bt,
            "thickness": bt,
            "description": f"Horizontal board under keyboards; width = keyboard ({kbd_width}mm) + 2 cheeks ({bt}mm each)"
        },
        {
            "name": "Front Panel",
            "width": p.organ_internal_width_g,
            "height": p.table_height_g,
            "thickness": bt,
            "description": "Front panel of cabinet with volume pedal hole",
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

    # Fill boards (n=0) + stacked staircase cheek boards (n=1..N-1)
    for n in range(num_levels):
        depth = fill_depth - n * depth_offset
        if depth <= 0:
            break
        if n == 0:
            label = f"fill board {'(full depth, notch where side panels meet)' if fill_extend else '(extension only)'}"
        else:
            label = f"staircase step {n}, front edge at manual {n + 1} key tip"
        board_list += [
            {"name": f"Left Lateral Board {n + 1}", "width": fill_width, "height": depth,
             "thickness": bt, "description": f"Left {label}"},
            {"name": f"Right Lateral Board {n + 1}", "width": fill_width, "height": depth,
             "thickness": bt, "description": f"Right {label}"},
        ]

    return board_list


def generate_console(parameters):
    p = DotDict(parameters)

    show_dims = getattr(p, 'show_dimensions_g', False)
    num_manuals = int(getattr(p, 'keyboard_num_manuals_g', 2))
    depth_offset = getattr(p, 'keyboard_depth_offset_g', 130)
    keyboard_y_offset = getattr(p, 'keyboard_y_offset_g', 0)
    fill_extend = bool(getattr(p, 'table_fill_extend_g', False))

    bt = p.general_board_thickness_g

    kbd_dims = get_keyboard_dimensions(parameters)
    kbd_width = kbd_dims['width']
    kbd_depth = kbd_dims['depth']

    # Center board is keyboard-wide plus one board_thickness on each side (cheek seats)
    center_width = kbd_width + 2 * bt
    fill_width = (p.organ_internal_width_g - center_width) / 2

    # Fill / staircase boards: back edge at cabinet front OR at back wall
    fill_py = bt if fill_extend else p.console_depth_g
    fill_depth = (p.table_depth_g - bt) if fill_extend else (p.table_depth_g - p.console_depth_g)

    parts = []

    # ── Cabinet shell ─────────────────────────────────────────────────────────

    # Right side panel  (cabinet body depth only)
    parts.append(create_board(
        max_width=p.console_depth_g, max_height=p.total_height_g, board_thickness=bt,
        position=(-bt, 0, 0), rotation=(0, 0, 0), show_dimensions=show_dims
    ))

    # Left side panel
    parts.append(create_board(
        max_width=p.console_depth_g, max_height=p.total_height_g, board_thickness=bt,
        position=(-(p.organ_internal_width_g + 2 * bt), 0, 0),
        rotation=(0, 0, 0), show_dimensions=show_dims
    ))

    # Back panel
    parts.append(create_board(
        max_width=p.organ_internal_width_g, max_height=p.total_height_g, board_thickness=bt,
        position=(-bt, 0, 0), rotation=(0, 0, 90), show_dimensions=show_dims
    ))

    # Top lid  (covers only cabinet body depth)
    parts.append(create_board(
        max_width=p.organ_internal_width_g, max_height=p.console_depth_g - bt, board_thickness=bt,
        position=(-bt, bt, p.total_height_g), rotation=(0, 90, 90), show_dimensions=show_dims
    ))

    # ── Keyboard table ────────────────────────────────────────────────────────

    # Center board: (kbd_width + 2×bt) wide, full table depth
    # X spans: [-bt - fill_width - center_width,  -bt - fill_width]
    parts.append(create_board(
        max_width=center_width, max_height=p.table_depth_g - bt, board_thickness=bt,
        position=(-bt - fill_width, bt, p.table_height_g),
        rotation=(0, 90, 90), show_dimensions=show_dims
    ))

    # Fill boards (n=0) and stacked staircase cheek boards (n=1..N-1).
    # All boards share the same back Y = fill_py; depth decreases by depth_offset per level.
    # Each level is stacked one board_thickness higher than the previous.
    num_levels = max(1, num_manuals)
    for n in range(num_levels):
        depth = fill_depth - n * depth_offset
        if depth <= 0:
            break
        z = p.table_height_g + n * bt  # stacked: n=0 at table surface, n=1 one layer up, …

        # Right fill / staircase board   X: [-bt - fill_width,  -bt]
        parts.append(create_board(
            max_width=fill_width, max_height=depth, board_thickness=bt,
            position=(-bt, fill_py, z),
            rotation=(0, 90, 90), show_dimensions=show_dims
        ))

        # Left fill / staircase board
        # X: [-bt - fill_width - center_width - fill_width,  -bt - fill_width - center_width]
        parts.append(create_board(
            max_width=fill_width, max_height=depth, board_thickness=bt,
            position=(-bt - fill_width - center_width, fill_py, z),
            rotation=(0, 90, 90), show_dimensions=show_dims
        ))

    # ── Front panel (cabinet face) with volume pedal hole ─────────────────────
    pedal_hole_w = (p.volume_pedals_number_g * (p.volume_pedals_width_g + p.volume_pedals_spacing_g)
                    + p.volume_pedals_spacing_g)
    pedal_hole_h = p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g
    pedal_hole_x = p.organ_internal_width_g / 2
    pedal_hole_y = p.volume_pedals_hole_start_height_g + pedal_hole_h / 2

    parts.append(create_board(
        max_width=p.organ_internal_width_g, max_height=p.table_height_g, board_thickness=bt,
        position=(-bt, p.console_depth_g - p.base_front_distance_g, 0),
        rotation=(0, 0, 90),
        rectangular_holes=[[pedal_hole_x, pedal_hole_y, pedal_hole_w, pedal_hole_h]],
        show_dimensions=show_dims
    ))

    # ── Volume pedals ─────────────────────────────────────────────────────────
    pedal_x_center = -bt - p.organ_internal_width_g / 2
    pedal_x_span = pedal_hole_w / 2

    for i in range(p.volume_pedals_number_g):
        px = (pedal_x_center + pedal_x_span
              - i * (p.volume_pedals_spacing_g + p.volume_pedals_width_g)
              - p.volume_pedals_spacing_g)
        parts.append(create_board(
            max_width=p.volume_pedals_width_g, max_height=p.volume_pedals_height_g,
            board_thickness=bt,
            position=(px,
                      p.console_depth_g - p.base_front_distance_g + bt,
                      p.volume_pedals_hole_start_height_g + 2 * p.volume_pedals_spacing_g),
            rotation=(0, -30, 90), show_dimensions=show_dims
        ))

    # ── Keyboards ─────────────────────────────────────────────────────────────
    # Keyboard stack is centered in the console (same X formula as normal console).
    # The keyboard sits on top of the center table board; front of keys at table_depth_g.
    if num_manuals > 0:
        keyboard_position = (
            -bt - p.organ_internal_width_g / 2 - kbd_width / 2,
            p.table_depth_g - kbd_depth + keyboard_y_offset,
            p.table_height_g
        )
        keyboard_stack = generate_keyboard_stack(parameters, base_position=keyboard_position)
        parts.append(keyboard_stack)

    return Compound(children=parts)


if __name__ == "__main__":
    params = get_default_parameters()
    console = generate_console(params)
    try:
        from ocp_vscode import show
        show(console)
    except ImportError:
        print("Note: Install ocp_vscode to visualize the model")
