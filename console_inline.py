"""
Inline Console Generator - build123d Version

Line-style organ console. The keyboard table protrudes forward beyond
the cabinet body:

  console_depth_g (~350 mm): depth of the cabinet body (side panels, back,
                             top lid, front panels).
  table_depth_g   (~600 mm): total depth of the keyboard table.

Table structure (all boards share the same full table depth, back to front):
  ┌──────────────────────────────────────────────────────┐
  │ left fill │  cheek │  center board  │ cheek │ right fill │
  └──────────────────────────────────────────────────────┘
  center board width = keyboard_total_width + 2 × board_thickness
  cheeks = vertical boards at the inner edges of the center board,
           spanning full table depth, rising table_cheek_height_g above the table
  fill boards = horizontal boards at each keyboard level height,
                decreasing depth per level (staircase), one pair per manual

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
            {"table_cheek_height_g": 150}   # height of keyboard cheek boards above table
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
    table_inner_depth = p.table_depth_g - bt      # all table boards share this depth
    cheek_height = getattr(p, 'table_cheek_height_g', 150)

    num_manuals = int(getattr(p, 'keyboard_num_manuals_g', 2))
    depth_offset = getattr(p, 'keyboard_depth_offset_g', 130)
    num_levels = max(1, num_manuals)

    board_list = [
        {"name": "Left Side Panel", "width": p.console_depth_g, "height": p.total_height_g,
         "thickness": bt, "description": "Left side panel (cabinet body depth)"},
        {"name": "Right Side Panel", "width": p.console_depth_g, "height": p.total_height_g,
         "thickness": bt, "description": "Right side panel (cabinet body depth)"},
        {"name": "Back Panel", "width": p.organ_internal_width_g, "height": p.total_height_g,
         "thickness": bt, "description": "Back panel, full width and height"},
        {"name": "Top Lid", "width": p.organ_internal_width_g,
         "height": p.console_depth_g - bt, "thickness": bt,
         "description": "Top lid, covers cabinet body only"},
        {"name": "Upper Front Wall",
         "width": p.organ_internal_width_g,
         "height": p.total_height_g - p.table_height_g,
         "thickness": bt,
         "description": "Front wall above keyboard table, closes off the interior"},
        {"name": "Center Keyboard Support Board",
         "width": center_width, "height": table_inner_depth, "thickness": bt,
         "description": f"Horizontal board under keyboards; width = kbd ({kbd_width}mm) + 2×cheek seats ({bt}mm each)"},
        {"name": "Left Keyboard Cheek",
         "width": table_inner_depth, "height": cheek_height, "thickness": bt,
         "description": "Vertical side wall at left edge of keyboard section, full table depth"},
        {"name": "Right Keyboard Cheek",
         "width": table_inner_depth, "height": cheek_height, "thickness": bt,
         "description": "Vertical side wall at right edge of keyboard section, full table depth"},
        {"name": "Front Panel",
         "width": p.organ_internal_width_g, "height": p.table_height_g, "thickness": bt,
         "description": "Lower front panel with volume pedal hole",
         "rectangular_holes": [[
             p.organ_internal_width_g / 2,
             p.volume_pedals_hole_start_height_g + (p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g) / 2,
             p.volume_pedals_number_g * (p.volume_pedals_width_g + p.volume_pedals_spacing_g) + p.volume_pedals_spacing_g,
             p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g
         ]]},
        {"name": "Volume Pedals", "width": p.volume_pedals_width_g,
         "height": p.volume_pedals_height_g, "thickness": bt,
         "description": f"Volume pedals (quantity: {p.volume_pedals_number_g})"},
    ]

    # Staircase fill boards: one pair per keyboard level.
    # Level n is at keyboard height n; depth decreases by depth_offset per level.
    for n in range(num_levels):
        depth = table_inner_depth - n * depth_offset
        if depth <= 0:
            break
        label = "table level (manual 1)" if n == 0 else f"staircase step, front at manual {n + 1} key tip"
        board_list += [
            {"name": f"Left Fill Board {n + 1}", "width": fill_width, "height": depth,
             "thickness": bt, "description": f"Left {label}"},
            {"name": f"Right Fill Board {n + 1}", "width": fill_width, "height": depth,
             "thickness": bt, "description": f"Right {label}"},
        ]

    return board_list


def generate_console(parameters):
    p = DotDict(parameters)

    show_dims = getattr(p, 'show_dimensions_g', False)
    num_manuals = int(getattr(p, 'keyboard_num_manuals_g', 2))
    depth_offset = getattr(p, 'keyboard_depth_offset_g', 130)
    vertical_spacing = getattr(p, 'keyboard_vertical_spacing_g', 80)
    keyboard_y_offset = getattr(p, 'keyboard_y_offset_g', 0)
    cheek_height = getattr(p, 'table_cheek_height_g', 150)

    bt = p.general_board_thickness_g
    table_inner_depth = p.table_depth_g - bt   # all table boards: from Y=bt to Y=table_depth_g

    kbd_dims = get_keyboard_dimensions(parameters)
    kbd_width = kbd_dims['width']
    kbd_depth = kbd_dims['depth']

    center_width = kbd_width + 2 * bt
    fill_width = (p.organ_internal_width_g - center_width) / 2

    parts = []

    # ── Cabinet shell ─────────────────────────────────────────────────────────

    # Right side panel (cabinet body depth only)
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
    # Top lid (cabinet body depth only)
    parts.append(create_board(
        max_width=p.organ_internal_width_g, max_height=p.console_depth_g - bt, board_thickness=bt,
        position=(-bt, bt, p.total_height_g), rotation=(0, 90, 90), show_dimensions=show_dims
    ))
    # Upper front wall — closes the interior above the keyboard table
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.total_height_g - p.table_height_g,
        board_thickness=bt,
        position=(-bt, p.console_depth_g - p.base_front_distance_g, p.table_height_g),
        rotation=(0, 0, 90), show_dimensions=show_dims
    ))

    # ── Keyboard table ────────────────────────────────────────────────────────

    # Center support board (full table depth, kbd_width + 2×bt wide)
    # X spans: [-bt - fill_width - center_width,  -bt - fill_width]
    parts.append(create_board(
        max_width=center_width, max_height=table_inner_depth, board_thickness=bt,
        position=(-bt - fill_width, bt, p.table_height_g),
        rotation=(0, 90, 90), show_dimensions=show_dims
    ))

    # Right keyboard cheek — vertical board at right inner edge of center board.
    # Sits on the center board, faces inward, spans full table depth.
    # X spans: [-(2bt + fill_width),  -(bt + fill_width)]
    parts.append(create_board(
        max_width=table_inner_depth, max_height=cheek_height, board_thickness=bt,
        position=(-(2 * bt + fill_width), bt, p.table_height_g),
        rotation=(0, 0, 0), show_dimensions=show_dims
    ))
    # Left keyboard cheek — at left inner edge of center board.
    # X spans: [-(3bt + fill_width + kbd_width),  -(2bt + fill_width + kbd_width)]
    parts.append(create_board(
        max_width=table_inner_depth, max_height=cheek_height, board_thickness=bt,
        position=(-(3 * bt + fill_width + kbd_width), bt, p.table_height_g),
        rotation=(0, 0, 0), show_dimensions=show_dims
    ))

    # Staircase fill boards (horizontal, in the lateral fill areas).
    # Level n is at keyboard surface height n (n × vertical_spacing above the table).
    # Depth decreases by depth_offset per level so the front edge aligns with manual n+1 key tip.
    num_levels = max(1, num_manuals)
    for n in range(num_levels):
        depth = table_inner_depth - n * depth_offset
        if depth <= 0:
            break
        z = p.table_height_g + n * vertical_spacing   # at keyboard level n height

        # Right fill board   X: [-bt - fill_width,  -bt]
        parts.append(create_board(
            max_width=fill_width, max_height=depth, board_thickness=bt,
            position=(-bt, bt, z),
            rotation=(0, 90, 90), show_dimensions=show_dims
        ))
        # Left fill board   X: [-bt - fill_width - center_width - fill_width,  -bt - fill_width - center_width]
        parts.append(create_board(
            max_width=fill_width, max_height=depth, board_thickness=bt,
            position=(-bt - fill_width - center_width, bt, z),
            rotation=(0, 90, 90), show_dimensions=show_dims
        ))

    # ── Lower front panel with volume pedal hole ──────────────────────────────
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
    for i in range(p.volume_pedals_number_g):
        px = (pedal_x_center + pedal_hole_w / 2
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
