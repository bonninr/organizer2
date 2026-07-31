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

import math
from build123d import *
from utils import DotDict, create_board
from keyboard import (generate_keyboard_stack, get_keyboard_dimensions,
                      generate_keyboard_cheeks, get_keyboard_cheek_steps,
                      generate_piston_rails, get_piston_rail_specs,
                      get_cheek_layers, generate_rocker_tabs, get_rocker_tab_layout,
                      generate_piston_buttons)


def _keyboard_base_position(parameters):
    """
    Base position of the manual stack: minimum X, back edge Y, base Z.

    Table boards are placed by their top face, so the table surface is at
    table_height_g and the manuals sit one board thickness above it.
    """
    p = DotDict(parameters)
    bt = p.general_board_thickness_g
    kd = get_keyboard_dimensions(parameters)

    return (
        -bt - p.organ_internal_width_g / 2 - kd['width'] / 2,
        p.table_depth_g - kd['depth'] + getattr(p, 'keyboard_y_offset_g', 0),
        p.table_height_g + bt + getattr(p, 'keyboard_initial_height_gap_g', 0)
    )


def _cheek_clearance(parameters):
    """
    Height of each cheek step above its own manual's base.

    The keyboard's own height is the top of its black keys, so using it finishes
    each cheek flush with the black keys of the manual it flanks.
    table_cheek_height_g adds any extra rise above that.
    """
    p = DotDict(parameters)

    return (get_keyboard_dimensions(parameters)['height']
            + getattr(p, 'table_cheek_height_g', 0))


def generate_music_stand(parameters):
    """
    Generate the music desk: an angled board standing on the console top,
    leaning back, with a small ledge at its foot to hold the music.

    Args:
        parameters: Parameter dictionary

    Returns:
        List of Part objects (empty when disabled)
    """
    p = DotDict(parameters)

    if not getattr(p, 'music_stand_enabled_g', False):
        return []

    bt = p.general_board_thickness_g
    width = getattr(p, 'music_stand_width_g', 700)
    height = getattr(p, 'music_stand_height_g', 280)
    angle = getattr(p, 'music_stand_angle_g', 15)
    pos_y = getattr(p, 'music_stand_pos_y_g', 150)
    ledge = getattr(p, 'music_stand_ledge_g', 40)
    if width <= 0 or height <= 0:
        return []

    center_x = -bt - p.organ_internal_width_g / 2
    top_z = p.total_height_g
    parts = []

    # Angled back board. max_height is the sloped length so the vertical rise
    # stays 'height' whatever the recline angle.
    board_len = height / math.cos(math.radians(angle))
    parts.append(create_board(
        max_width=width, max_height=board_len, board_thickness=bt,
        position=(center_x + width / 2, pos_y, top_z),
        rotation=(0, -angle, 90)
    ))

    # Ledge at the foot, a shallow horizontal lip in front of the board
    if ledge > 0:
        parts.append(create_board(
            max_width=width, max_height=ledge, board_thickness=bt,
            position=(center_x + width / 2, pos_y, top_z),
            rotation=(0, 90, 90)
        ))

    return parts


def get_default_parameters():
    return {
        "General_and_base": [
            {"organ_internal_width_g": 1100},
            {"general_board_thickness_g": 18},
            {"total_height_g": 1000},
            {"console_depth_g": 250},
            {"base_front_distance_g": 10}
        ],
        "Table": [
            {"table_height_g": 720},
            {"table_depth_g": 550},
            {"keyboard_cheeks_enabled_g": True},  # vertical boards flanking the manuals
            {"keyboard_cheek_layers_g": 2},       # boards laminated side by side per cheek
            {"table_cheek_height_g": 0},         # extra cheek rise above the black keys
            {"fill_notch_g": True},               # full-depth lateral boards with a diagonal notch toward the player
            {"fill_notch_start_depth_g": 350},   # depth from back where notch slant begins (~console_depth - bt)
            {"fill_notch_front_width_g": 20}     # fill board width at the front of the notch (mm)
        ],
        "Volume_pedals": [
            {"volume_pedals_width_g": 120},
            {"volume_pedals_height_g": 240},
            {"volume_pedals_number_g": 3},
            {"volume_pedals_spacing_g": 10},
            {"volume_pedals_hole_start_height_g": 140}
        ],
        "Pistons": [
            {"pistons_enabled_g": True},   # Combination piston rail under each manual
            {"piston_count_g": 9},         # Number of pistons per rail
            {"piston_diameter_g": 15},     # Piston hole diameter (mm)
            {"piston_spacing_g": 45},      # Centre-to-centre spacing (mm)
            {"piston_rail_height_g": 38},  # Rail face height (mm); rail 1 is auto-sized to reach the table
            {"piston_buttons_enabled_g": True},   # Plastic buttons through the rail holes
            {"piston_button_protrusion_g": 11},   # How far each button stands proud of the rail (mm)
            {"piston_button_clearance_g": 1},     # Button diameter = hole diameter - clearance (mm)
            {"piston_button_material_g": "plastic"}
        ],
        "Rocker_tabs": [
            {"rocker_tabs_enabled_g": True},   # Rocker (stop) tab bank on the upper front panel
            {"rocker_tab_groups_g": 4},        # Number of groups (register families)
            {"rocker_tab_group_size_g": 8},    # Tabs per group
            {"rocker_tab_width_g": 25},        # Width of each tab (mm)
            {"rocker_tab_height_g": 70},       # Height of each tab (mm)
            {"rocker_tab_depth_g": 7},         # How far each tab stands off the panel (mm)
            {"rocker_tab_gap_g": 2},           # Gap between tabs within a group (mm)
            {"rocker_tab_group_gap_g": 10},    # Gap between groups (mm)
            {"rocker_tab_material_g": "plastic"},  # Tab material (white plastic)
            {"rocker_tab_standoff_g": 0.5}     # Gap from the panel face (avoids z-fighting)
        ],
        "Music_stand": [
            {"music_stand_enabled_g": True},   # Angled music desk on the console top
            {"music_stand_width_g": 490},      # Width of the desk (mm)
            {"music_stand_height_g": 196},     # Vertical rise of the desk (mm)
            {"music_stand_angle_g": 15},       # Recline from vertical (degrees)
            {"music_stand_pos_y_g": 150},      # Y of the desk foot, from the back (mm)
            {"music_stand_ledge_g": 40}        # Depth of the music ledge at the foot (mm)
        ],
        "Keyboards": [
            {"keyboard_num_manuals_g": 2},
            {"keyboard_total_keys_g": 61},
            {"keyboard_total_width_g": 870},
            {"keyboard_white_key_length_g": 150},
            {"keyboard_white_key_height_g": 15},
            {"keyboard_white_key_front_cut_depth_g": 20},
            {"keyboard_white_key_front_cut_height_g": 8},
            {"keyboard_black_key_width_ratio_g": 0.65},
            {"keyboard_black_key_length_g": 95},
            {"keyboard_black_key_height_g": 10},
            {"keyboard_key_gap_g": 0.5},
            {"keyboard_base_thickness_g": 10},
            # 73 = board_thickness + manual lift + manual height, which makes every
            # cheek step the same height (the first spans table -> manual 1 black
            # keys, each later one spans a single manual rise)
            {"keyboard_vertical_spacing_g": 73},
            {"keyboard_depth_offset_g": 130},
            {"keyboard_y_offset_g": 0},
            {"keyboard_initial_height_gap_g": 20}
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
    step_height = getattr(p, 'table_cheek_height_g', 60)
    fill_notch = getattr(p, 'fill_notch_g', False)
    fill_notch_start = getattr(p, 'fill_notch_start_depth_g', p.console_depth_g - bt)
    fill_notch_front_width = getattr(p, 'fill_notch_front_width_g', 100)

    num_manuals = int(getattr(p, 'keyboard_num_manuals_g', 2))
    depth_offset = getattr(p, 'keyboard_depth_offset_g', 130)
    num_levels = max(1, num_manuals)

    if fill_notch:
        fill_depth = table_inner_depth
        fill_desc = f"Horizontal fill board, full table depth with notch from {fill_notch_start:.0f}mm"
    else:
        fill_depth = p.console_depth_g - bt
        fill_desc = "Horizontal fill board, short (cabinet body depth only)"

    fill_entry_extra = {"min_width": fill_notch_front_width, "min_height": fill_notch_start} if fill_notch else {}

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
        {"name": "Left Fill Board", "width": fill_width, "height": fill_depth,
         "thickness": bt, "description": fill_desc, **fill_entry_extra},
        {"name": "Right Fill Board", "width": fill_width, "height": fill_depth,
         "thickness": bt, "description": fill_desc, **fill_entry_extra},
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

    # Staircase keyboard cheeks: one step per manual level, each finishing flush
    # with its manual's black keys. Sizes are position-independent, so measure
    # against a table surface at z=0 with the same back edge the model uses.
    if getattr(p, 'keyboard_cheeks_enabled_g', False):
        kbd_base = _keyboard_base_position(parameters)
        steps = get_keyboard_cheek_steps(
            parameters, (0, kbd_base[1], kbd_base[2] - p.table_height_g), bt,
            cheek_z=0, back_y=bt, cheek_height=_cheek_clearance(parameters)
        )
        for n, step in enumerate(steps):
            for side in ("Left", "Right"):
                # Each cheek is laminated from several boards side by side
                for layer in range(step['layers']):
                    board_list.append({
                        "name": f"{side} Keyboard Cheek Step {n + 1} Board {layer + 1}",
                        "width": step['depth'], "height": step['height'], "thickness": bt,
                        "description": f"{side} cheek step {n + 1}, lamination "
                                       f"{layer + 1} of {step['layers']}, "
                                       f"depth={step['depth']:.0f}mm, "
                                       f"height={step['height']:.0f}mm, flush with manual "
                                       f"{n + 1} black keys"
                    })


    # Combination piston rails - one per manual, holes drilled through the face
    _first_rail_max = bt + getattr(p, 'keyboard_initial_height_gap_g', 0)
    for n, spec in enumerate(get_piston_rail_specs(parameters, bt, _first_rail_max)):
        board_list.append({
            "name": f"Combination Piston Rail {n + 1}",
            "width": spec['width'],
            "height": spec['height'],
            "thickness": spec['thickness'],
            "description": f"Piston rail under manual {n + 1}, "
                           f"{len(spec['holes'])} holes of "
                           f"{spec['holes'][0][2]:.0f}mm" if spec['holes']
                           else f"Piston rail under manual {n + 1}",
            "circular_holes": spec['holes'],
        })


    # Music desk boards
    if getattr(p, 'music_stand_enabled_g', False):
        import math as _m
        msw=getattr(p,'music_stand_width_g',700); msh=getattr(p,'music_stand_height_g',280)
        msa=getattr(p,'music_stand_angle_g',15); msl=getattr(p,'music_stand_ledge_g',40)
        board_list.append({"name":"Music Desk","width":msw,
            "height": msh/_m.cos(_m.radians(msa)),"thickness":bt,
            "description":f"Angled music desk, {msa:.0f} deg recline"})
        if msl>0:
            board_list.append({"name":"Music Desk Ledge","width":msw,"height":msl,
                "thickness":bt,"description":"Ledge at the foot of the music desk"})

    return board_list


def generate_console(parameters):
    p = DotDict(parameters)

    show_dims = getattr(p, 'show_dimensions_g', False)
    num_manuals = int(getattr(p, 'keyboard_num_manuals_g', 2))
    depth_offset = getattr(p, 'keyboard_depth_offset_g', 130)
    vertical_spacing = getattr(p, 'keyboard_vertical_spacing_g', 80)
    keyboard_y_offset = getattr(p, 'keyboard_y_offset_g', 0)
    bt = p.general_board_thickness_g
    fill_notch = getattr(p, 'fill_notch_g', False)
    fill_notch_start = getattr(p, 'fill_notch_start_depth_g', p.console_depth_g - bt)
    fill_notch_front_width = getattr(p, 'fill_notch_front_width_g', 100)
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

    # Fill boards — horizontal surfaces at table height on each side of the keyboard section.
    # Style: notch = full table depth with trapezoidal slant; short = ends at cabinet body depth.
    if fill_notch:
        fill_depth = table_inner_depth
        fill_min_w = fill_notch_front_width
        fill_min_h = fill_notch_start
    else:
        fill_depth = p.console_depth_g - bt
        fill_min_w = 0
        fill_min_h = 0

    # Right fill board — notch flipped to inner side for correct orientation
    parts.append(create_board(
        max_width=fill_width, max_height=fill_depth, board_thickness=bt,
        min_width=fill_min_w, min_height=fill_min_h,
        position=(-bt, bt, p.table_height_g),
        rotation=(0, 90, 90), flip_notch=fill_notch, show_dimensions=show_dims
    ))
    # Left fill board — notch on default side (outer/Z=max_width) for correct orientation
    parts.append(create_board(
        max_width=fill_width, max_height=fill_depth, board_thickness=bt,
        min_width=fill_min_w, min_height=fill_min_h,
        position=(-bt - fill_width - center_width, bt, p.table_height_g),
        rotation=(0, 90, 90), show_dimensions=show_dims
    ))

    # Staircase keyboard cheeks — one vertical step per manual level.
    # Each step finishes flush with its own manual's black keys, so it tracks the
    # manual heights rather than rising by a fixed amount. They stand on the
    # table surface and run the full table depth (back_y at the table's back
    # edge), unlike the normal/vertical cheeks which only flank the manuals.
    parts.extend(generate_keyboard_cheeks(
        parameters, _keyboard_base_position(parameters), bt,
        cheek_z=p.table_height_g,
        back_y=bt,
        cheek_height=_cheek_clearance(parameters),
        show_dimensions=show_dims
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
        keyboard_stack = generate_keyboard_stack(
            parameters, base_position=_keyboard_base_position(parameters))
        parts.append(keyboard_stack)

        # Combination piston rail under each manual
        parts.extend(generate_piston_rails(
            parameters, _keyboard_base_position(parameters), bt,
            rail_base_z=p.table_height_g, show_dimensions=show_dims
        ))

        # Plastic buttons through the rail holes
        parts.extend(generate_piston_buttons(
            parameters, _keyboard_base_position(parameters), bt,
            rail_base_z=p.table_height_g
        ))

    # Music desk on the console top
    parts.extend(generate_music_stand(parameters))

    # Rocker (stop) tab bank on the upper front wall, centred between the top of
    # the highest manual and the top of that wall.
    if num_manuals > 0:
        kd = get_keyboard_dimensions(parameters)
        top_manual_top = (_keyboard_base_position(parameters)[2]
                          + (num_manuals - 1) * getattr(p, 'keyboard_vertical_spacing_g', 73)
                          + kd['height'])
        wall_front_y = p.console_depth_g - p.base_front_distance_g + bt
        parts.extend(generate_rocker_tabs(
            parameters,
            front_y=wall_front_y,
            center_x=-bt - p.organ_internal_width_g / 2,
            z_center=(top_manual_top + p.total_height_g) / 2
        ))

    return Compound(children=parts)


if __name__ == "__main__":
    params = get_default_parameters()
    console = generate_console(params)
    try:
        from ocp_vscode import show
        show(console)
    except ImportError:
        print("Note: Install ocp_vscode to visualize the model")
