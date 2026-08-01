"""
Normal Console Generator - build123d Version

This module generates a normal (tower-style) organ console with:
- Base section with storage
- Upper section with notched side panels
- Keyboard manuals on the horizontal divider
- Simpler design than vertical console
- Suitable for compact spaces

Usage:
    from console_normal import generate_console, generate_board_list, get_default_parameters

    params = get_default_parameters()
    console_model = generate_console(params)
    board_list = generate_board_list(params)
"""

import math
from build123d import *
from utils import DotDict, create_board
from keyboard import (generate_keyboard_stack, get_keyboard_dimensions,
                      get_keyboard_stack_dimensions, generate_keyboard_cheeks,
                      get_keyboard_cheek_steps, generate_piston_rails,
                      get_piston_rail_specs, get_cheek_thickness,
                      get_cheek_layers, generate_rocker_tabs, get_rocker_tab_layout,
                      generate_piston_buttons)


def get_knob_stair_specs(parameters):
    """
    Calculate the Cavaille-Coll style terraced drawknob jambs.

    A jamb is a staircase standing on the keyboard table, one on each side of
    the manuals, stepping up and back away from the player. Each step is a
    vertical riser carrying the drawknob holes plus the horizontal tread behind
    it. The staircase spans from the front of the keyboard table back to the
    upper front board, which it finishes against, and that depth is divided
    evenly between the steps.

    Everything is sized to the space that actually exists: the jamb width is
    whatever the table has left beside the manuals and their cheeks, and the
    knob grid is derived from the hole spacing that fits a riser face.

    Args:
        parameters: Parameter dictionary

    Returns:
        dict with 'width', 'step_depth', 'step_height', 'steps' and
        'x_right'/'x_left' (the maximum-X edge of each jamb), or None when the
        jambs are disabled or do not fit. Each step carries 'riser_z',
        'front_y', 'tread_depth' and 'holes'.
    """
    p = DotDict(parameters)

    if not getattr(p, 'knob_stairs_enabled_g', False):
        return None

    steps = int(getattr(p, 'knob_stair_steps_g', 4))
    step_height = getattr(p, 'knob_stair_step_height_g', 70)
    diameter = getattr(p, 'knob_stair_hole_diameter_g', 25)
    spacing = getattr(p, 'knob_stair_hole_spacing_g', 55)
    gap = getattr(p, 'knob_stair_gap_g', 20)
    front_inset = getattr(p, 'knob_stair_front_inset_g', 20)
    if steps <= 0 or step_height <= 0:
        return None

    bt = p.general_board_thickness_g
    kbd_width = get_keyboard_dimensions(parameters)['width']
    cheek = get_cheek_thickness(parameters, bt)

    # Space the table has left either side of the manuals and their cheeks. Out
    # of it comes the gap back to the cheek and a stringer at each end of the
    # staircase; the terraces span between them. Carrying its own stringer on
    # both sides rather than leaning on the console's lateral board makes each
    # staircase a standalone assembly that can be built off the console.
    side_space = (p.organ_internal_width_g - kbd_width - 2 * cheek) / 2
    width = side_space - gap
    # Risers and treads run the full width, covering the stringers at each end.
    # Knobs can only pass where there is no stringer behind the riser, so the
    # holes are confined to the clear span between them.
    clear_span = width - 2 * bt
    if clear_span <= 0:
        return None

    # The staircase runs back to the upper front board, which it finishes
    # against. That board is placed at base_depth_g - thickness and extends
    # forward, so its front face - and the rear face of the staircase - is at
    # base_depth_g. At the other end the bottom riser is set back from the table
    # edge by front_inset, so the terraces stand on the table rather than
    # finishing flush with its lip. The depth between those two is therefore
    # determined, not chosen, and is divided evenly between the steps.
    table_front_y = bt + p.top_depth_g    # front edge of the keyboard table
    front_y = table_front_y - front_inset
    back_y = p.base_depth_g               # front face of the upper front board
    total_depth = front_y - back_y
    if total_depth <= 0:
        return None

    step_depth = total_depth / steps
    tread_depth = step_depth - bt
    table_top_z = p.base_height_g + bt

    # A hole must leave material all round, or it saws the riser into pieces
    margin = 2
    hole_d = min(diameter, step_height - 2 * margin, clear_span - 2 * margin)

    def _grid(y_centre):
        if hole_d <= 0 or spacing <= 0:
            return []
        cols = int((clear_span - hole_d) // spacing) + 1
        rows = int((step_height - hole_d) // spacing) + 1
        # Centred on the riser, but only as many columns as clear the stringers
        return [[width / 2 + (c - (cols - 1) / 2) * spacing,
                 y_centre + (r - (rows - 1) / 2) * spacing,
                 hole_d]
                for r in range(rows) for c in range(cols)]

    step_list = []
    for i in range(steps):
        riser_z = table_top_z + i * step_height

        # The tread below stops one thickness short of the next riser, leaving a
        # slot under every step above the first. Dropping the riser and the
        # stringer by one thickness closes it, and it also makes consecutive
        # stringer segments meet so the run becomes continuous.
        drop = bt if i > 0 else 0

        step_list.append({
            'riser_z': riser_z,
            'front_y': front_y - i * step_depth,
            'tread_depth': tread_depth,
            # Knobs stay centred on the step face, not on the extended board
            'holes': _grid(drop + step_height / 2),
            'riser_z_bottom': riser_z - drop,
            'riser_height': step_height + drop,
            # The stringer is inset one thickness at the front so the riser
            # lands against it, and one at the top so the tread rests on it
            'closure_depth': total_depth - i * step_depth - bt,
            'closure_z_bottom': riser_z - drop,
            'closure_height': step_height - bt + drop,
        })

    # Terrace bands, running the full width over the stringers
    x_right = -bt
    x_left = -(p.organ_internal_width_g + bt) + width

    return {
        'width': width,
        'gap': gap,
        'front_inset': front_inset,
        'front_y': front_y,
        'step_depth': step_depth,
        'step_height': step_height,
        'tread_depth': tread_depth,
        'hole_diameter': hole_d,
        'back_y': back_y,
        'steps': step_list,
        'x_right': x_right,                       # terrace max-X edge, right side
        'x_left': x_left,                         # terrace max-X edge, left side
        'clear_span': clear_span,
        # A stringer at each end of both staircases, tucked under the terraces.
        # Given as min-X faces.
        'stringer_x': [
            x_right - width,                      # right, keyboard side
            x_right - bt,                         # right, console-wall side
            x_left - bt,                          # left,  keyboard side
            x_left - width,                       # left,  console-wall side
        ],
    }


def generate_knob_stairs(parameters, show_dimensions=False):
    """
    Generate the terraced drawknob jambs either side of the manuals.

    Args:
        parameters: Parameter dictionary
        show_dimensions: Passed through to create_board

    Returns:
        List of Part objects (empty when the jambs are disabled)
    """
    p = DotDict(parameters)

    spec = get_knob_stair_specs(parameters)
    if spec is None:
        return []

    bt = p.general_board_thickness_g
    parts = []

    for x_edge in (spec['x_right'], spec['x_left']):
        for step in spec['steps']:
            # Riser: vertical face carrying the drawknobs, looking at the player
            parts.append(create_board(
                max_width=spec['width'],
                max_height=step['riser_height'],
                board_thickness=bt,
                position=(x_edge, step['front_y'] - bt, step['riser_z_bottom']),
                rotation=(0, 0, 90),
                circular_holes=step['holes'],
                show_dimensions=show_dimensions
            ))

            # Tread: horizontal top of the step, running back from the riser
            if spec['tread_depth'] > 0:
                parts.append(create_board(
                    max_width=spec['width'],
                    max_height=spec['tread_depth'],
                    board_thickness=bt,
                    position=(x_edge,
                              step['front_y'] - bt - spec['tread_depth'],
                              step['riser_z'] + spec['step_height']),
                    rotation=(0, 90, 90),
                    show_dimensions=show_dimensions
                ))

    # Stringers at both ends of each staircase. They sit inside the structure
    # and carry it: every riser lands against the stringer's front edge and
    # every tread sits on its top edge, so the terraces span between the two
    # and the assembly stands on its own.
    for closure_x in spec['stringer_x']:
        for step in spec['steps']:
            if step['closure_depth'] <= 0 or step['closure_height'] <= 0:
                continue
            parts.append(create_board(
                max_width=step['closure_depth'],
                max_height=step['closure_height'],
                board_thickness=bt,
                position=(closure_x, spec['back_y'], step['closure_z_bottom']),
                rotation=(0, 0, 0),
                show_dimensions=show_dimensions
            ))

    return parts


def _knob_prototypes(parameters, hole_diameter):
    """
    Build one drawknob (black gramophone horn + white cap) at the origin,
    flaring toward +Y with the neck at y=0. Returns (trumpet, cap, body_mat,
    cap_mat) so callers can copy the same knob to every hole.
    """
    p = DotDict(parameters)

    knob_d = getattr(p, 'knob_stair_knob_diameter_g', 30)
    protr = getattr(p, 'knob_stair_knob_protrusion_g', 15)
    cap_t = getattr(p, 'knob_stair_knob_cap_thickness_g', 1)
    body_mat = getattr(p, 'knob_stair_knob_body_material_g', 'black')
    cap_mat = getattr(p, 'knob_stair_knob_cap_material_g', 'white')
    base_d = getattr(p, 'knob_stair_knob_base_diameter_g', hole_diameter - 2)
    flare = getattr(p, 'knob_stair_knob_flare_g', 3.0)   # >1 keeps a neck then bells out

    r_front = knob_d / 2
    r_back = max(1.0, base_d / 2)   # trumpet neck, sits inside the hole

    n = 16
    outer = [(r_back + (r_front - r_back) * ((i / n) ** flare), (i / n) * protr)
             for i in range(n + 1)]
    with BuildPart() as horn:
        with BuildSketch(Plane.XY):
            with BuildLine():
                Polyline([(0, 0)] + outer + [(0, protr), (0, 0)])
            make_face()
        revolve(axis=Axis.Y)
    trumpet = horn.part
    cap = Pos(0, protr + cap_t / 2, 0) * (Rot(90, 0, 0) * Cylinder(
        radius=r_front, height=cap_t))
    return trumpet, cap, body_mat, cap_mat


def generate_curved_knob_stairs(parameters):
    """
    Semicircular terraced drawknob controller: the straight staircase revolved
    around a vertical axis into an arc. Treads become moon-shaped annular boards,
    risers become curved bands, and a flat terminator board closes each end - the
    same pieces as the straight staircase, just swept. The straight staircase is
    the limit as the radius goes to infinity (arc angle -> 0).

    The controller starts at the union line where the keyboards meet the upper
    front board and steps up-and-back around the axis. Knobs sit on the outer
    face of each riser, equally spaced along the arc, facing the player.

    Args:
        parameters: Parameter dictionary

    Returns:
        List of Part objects (empty when disabled or the radius is not finite)
    """
    p = DotDict(parameters)

    if not getattr(p, 'knob_stairs_enabled_g', False):
        return []
    if getattr(p, 'knob_stair_radius_g', 0) <= 0:
        return []   # 0 = straight staircase, handled elsewhere

    spec = get_knob_stair_specs(parameters)
    if spec is None:
        return []

    bt = p.general_board_thickness_g
    arc = math.radians(getattr(p, 'knob_stair_arc_angle_g', 55))  # angular span per jamb
    spacing = getattr(p, 'knob_stair_hole_spacing_g', 55)
    hole_d = spec['hole_diameter']
    W = spec['width']
    if arc <= 0 or W <= 0:
        return []

    kbd_w = get_keyboard_dimensions(parameters)['width']
    cheek = get_cheek_thickness(parameters, bt)
    cxm = -bt - p.organ_internal_width_g / 2                  # console centre X
    inner_edge = kbd_w / 2 + cheek + getattr(p, 'knob_stair_gap_g', 20)
    radius = W / arc                                          # developed width = jamb width

    knobs_on = getattr(p, 'knob_stair_knobs_enabled_g', False)
    if knobs_on:
        trumpet0, cap0, body_mat, cap_mat = _knob_prototypes(parameters, hole_d)

    n_cols = max(1, int(W / spacing))

    parts = []
    # sgn = +1 right jamb (extends toward +X), -1 left jamb (mirror).
    for sgn in (+1, -1):
        cheek_x = cxm + sgn * inner_edge                     # inner end anchored at the cheek

        for step in spec['steps']:
            ay = step['front_y']                             # this terrace's front line (steps back)
            oy = ay + radius                                 # arc centre sits toward the player
            zb = step['riser_z_bottom']
            fh = step['riser_height']
            fz = zb + fh / 2
            rows = sorted({hy for _, hy, _ in step['holes']}) or [fh / 2]

            for c in range(n_cols):
                beta = (c + 0.5) * spacing / radius          # arc angle from the cheek anchor
                if beta > arc:
                    break
                fx = cheek_x + sgn * radius * math.sin(beta)
                fy = oy - radius * math.cos(beta)
                deg = sgn * math.degrees(beta)               # facet turns toward the centre

                with BuildPart() as fb:
                    Box(spacing, bt, fh)
                    with Locations(*[(0, 0, hy - fh / 2) for hy in rows]):
                        Cylinder(radius=hole_d / 2, height=bt * 3,
                                 rotation=(90, 0, 0), mode=Mode.SUBTRACT)
                parts.append(Pos(fx, fy, fz) * (Rot(0, 0, deg) * fb.part))

                if knobs_on:
                    nx, ny = -sgn * math.sin(beta), math.cos(beta)   # face concave centre (player)
                    for hy in rows:
                        kz = zb + hy
                        px, py = fx + nx * bt / 2, fy + ny * bt / 2
                        t = Pos(px, py, kz) * (Rot(0, 0, deg) * trumpet0)
                        t.label = f"material:{body_mat}"
                        cc = Pos(px, py, kz) * (Rot(0, 0, deg) * cap0)
                        cc.label = f"material:{cap_mat}"
                        parts.append(t)
                        parts.append(cc)

    return parts


def generate_knob_stair_knobs(parameters):
    """
    Generate the drawknobs sitting in the knob-stair riser holes.

    Each knob is a little black plastic trumpet flaring out of its hole, capped
    with a thin white disc on the front. They are hardware, not wood, and are
    kept out of the timber cut list. All knobs are identical, so the trumpet and
    the cap are each built once and copied to every hole.

    Args:
        parameters: Parameter dictionary

    Returns:
        List of Part objects (empty when disabled)
    """
    p = DotDict(parameters)

    if not getattr(p, 'knob_stair_knobs_enabled_g', False):
        return []

    spec = get_knob_stair_specs(parameters)
    if spec is None:
        return []

    trumpet0, cap0, body_mat, cap_mat = _knob_prototypes(parameters, spec['hole_diameter'])

    parts = []
    for x_edge in (spec['x_right'], spec['x_left']):
        for step in spec['steps']:
            for hx, hy, _ in step['holes']:
                wx = x_edge - spec['width'] + hx    # world X of the hole centre
                wz = step['riser_z_bottom'] + hy
                base = Pos(wx, step['front_y'], wz)
                t = base * trumpet0
                t.label = f"material:{body_mat}"
                c = base * cap0
                c.label = f"material:{cap_mat}"
                parts.append(t)
                parts.append(c)

    return parts


def get_default_parameters():
    """
    Returns the default parameter set for the normal console.

    Returns:
        dict: Nested dictionary with all console parameters organized by category
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
            {"volume_pedals_width_g": 120},
            {"volume_pedals_height_g": 240},
            {"volume_pedals_number_g": 3},
            {"volume_pedals_spacing_g": 10},
            {"volume_pedals_hole_start_height_g": 140}
        ],
        "Top": [
            {"top_depth_g": 650},
            {"top_height_g": 350},
            {"top_notch_start_x_g": 350},
            {"top_notch_start_y_g": 150}
        ],
        "Carve": [
            {"carve_enabled_g": True},   # Recess in the front edge of the horizontal table
            {"carve_width_g": 900},      # Width of the flat bottom of the recess (mm)
            {"carve_depth_g": 30},       # How far the recess eats into the table depth (mm)
            {"carve_slope_g": 40},       # Horizontal run of each diagonal ramp (mm)
            {"carve_offset_g": 0}        # Shift of the recess centre off board centre (mm)
        ],
        "Knob_stairs": [
            {"knob_stairs_enabled_g": True},      # Cavaille-Coll terraced drawknob jambs
            {"knob_stair_steps_g": 4},            # Number of stair steps
            {"knob_stair_step_height_g": 70},     # Height of each step (mm)
            {"knob_stair_hole_diameter_g": 25},   # Drawknob hole diameter (mm)
            {"knob_stair_hole_spacing_g": 55},    # Centre-to-centre knob spacing (mm)
            {"knob_stair_gap_g": 20},             # Clear gap between the cheek and the staircase (mm)
            {"knob_stair_front_inset_g": 20},     # Setback of the bottom riser from the table front edge (mm)
            {"knob_stair_radius_g": 0},           # Concave arc radius (0 = straight staircase)
            {"knob_stair_arc_angle_g": 90},       # Per-jamb bend angle (deg); 0-radius = straight
            {"knob_stair_knobs_enabled_g": True},     # Draw the knobs in the holes
            {"knob_stair_knob_diameter_g": 35},       # Knob bell diameter (mm)
            {"knob_stair_knob_base_diameter_g": 18},  # Knob stem (start) diameter (mm)
            {"knob_stair_knob_flare_g": 3.0},         # Horn flare (>1 = long neck, late bell)
            {"knob_stair_knob_protrusion_g": 50},     # How far the knob flares out of the hole (mm)
            {"knob_stair_knob_cap_thickness_g": 1},   # White cap thickness (mm)
            {"knob_stair_knob_body_material_g": "black"},
            {"knob_stair_knob_cap_material_g": "white"}
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
        "Keyboards": [
            {"keyboard_num_manuals_g": 2},           # Number of keyboards (manuals)
            {"keyboard_total_keys_g": 61},           # Total keys (61 = 5 octaves, standard organ manual)
            {"keyboard_total_width_g": 870},         # Total keyboard width (mm) - key width calculated from this
            {"keyboard_white_key_length_g": 150},    # Visible white key length (mm)
            {"keyboard_white_key_height_g": 15},     # White key height/thickness (mm)
            {"keyboard_white_key_front_cut_depth_g": 20},   # Undercut at the key tip, back from the front (mm)
            {"keyboard_white_key_front_cut_height_g": 8},   # Undercut height, up from the key underside (mm)
            {"keyboard_black_key_width_ratio_g": 0.65},  # Black key width as ratio of white key width
            {"keyboard_black_key_length_g": 95},     # Black key length (mm)
            {"keyboard_black_key_height_g": 10},     # Black key height above white (mm)
            {"keyboard_key_gap_g": 0.5},             # Gap between keys (mm)
            {"keyboard_base_thickness_g": 10},       # Base plate thickness (mm)
            # 73 = board_thickness + manual lift + manual height, which makes every
            # cheek step the same height (the first spans table -> manual 1 black
            # keys, each later one spans a single manual rise)
            {"keyboard_vertical_spacing_g": 73},     # Vertical spacing between manuals (mm)
            {"keyboard_depth_offset_g": 130},        # Each higher manual offset back (mm) = key_length - 20
            {"keyboard_y_offset_g": 0},              # Offset from back of horizontal divider (mm), 0 = keys at front
            {"keyboard_initial_height_gap_g": 20},   # Lift of the manuals above the table (mm), room for a register board
            {"keyboard_cheeks_enabled_g": True},     # Vertical boards flanking the manuals
            {"keyboard_cheek_layers_g": 2},          # Boards laminated side by side per cheek
            {"keyboard_cheek_height_g": 35}          # Cheek clearance above each manual; 35 = manual height, so cheeks finish flush with the black keys
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
            "description": "Front panel of the base with volume pedal hole",
            "rectangular_holes": [[p.organ_internal_width_g/2, p.volume_pedals_hole_start_height_g + (p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g) / 2, p.volume_pedals_number_g * (p.volume_pedals_width_g + p.volume_pedals_spacing_g) + p.volume_pedals_spacing_g, p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g]]
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
        },
        {
            "name": "Volume Pedals",
            "width": p.volume_pedals_width_g,
            "height": p.volume_pedals_height_g,
            "thickness": p.general_board_thickness_g,
            "description": f"The volume pedals (quantity: {p.volume_pedals_number_g})"
        }
    ]

    # Keyboard cheeks - one pair of steps per manual. Sizes depend only on how
    # far the manuals sit above the table, not on absolute position, so measure
    # from a table surface at z=0.
    if getattr(p, 'keyboard_cheeks_enabled_g', False):
        bt = p.general_board_thickness_g
        kbd_z = bt + getattr(p, 'keyboard_initial_height_gap_g', 0)
        for n, step in enumerate(get_keyboard_cheek_steps(parameters, (0, 0, kbd_z), bt, cheek_z=0)):
            for side in ("Left", "Right"):
                # Each cheek is laminated from several boards side by side
                for layer in range(step['layers']):
                    board_list.append({
                        "name": f"{side} Keyboard Cheek Step {n + 1} Board {layer + 1}",
                        "width": step['depth'],
                        "height": step['height'],
                        "thickness": bt,
                        "description": f"{side} cheek step {n + 1} (manual {n + 1}), "
                                       f"lamination {layer + 1} of {step['layers']}, "
                                       f"depth={step['depth']:.0f}mm, height={step['height']:.0f}mm"
                    })


    # Combination piston rails - one per manual, holes drilled through the face
    _first_rail_max = p.general_board_thickness_g + getattr(p, 'keyboard_initial_height_gap_g', 0)
    for n, spec in enumerate(get_piston_rail_specs(parameters, p.general_board_thickness_g, _first_rail_max)):
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


    # Cavaille-Coll drawknob jambs - a riser and tread per step, doubled L/R
    _stairs = get_knob_stair_specs(parameters)
    if _stairs:
        bt = p.general_board_thickness_g
        nholes = len(_stairs['steps'][0]['holes'])
        for side in ("Left", "Right"):
            for n, step in enumerate(_stairs['steps']):
                board_list.append({
                    "name": f"{side} Knob Stair Riser {n + 1}",
                    "width": _stairs['width'],
                    "height": step['riser_height'],
                    "thickness": bt,
                    "description": f"{side} drawknob riser {n + 1}, {nholes} holes of "
                                   f"{_stairs['hole_diameter']:.0f}mm",
                    "circular_holes": step['holes'],
                })
                if _stairs['tread_depth'] > 0:
                    board_list.append({
                        "name": f"{side} Knob Stair Tread {n + 1}",
                        "width": _stairs['width'],
                        "height": _stairs['tread_depth'],
                        "thickness": bt,
                        "description": f"{side} drawknob tread {n + 1}",
                    })
                if step['closure_depth'] > 0 and step['closure_height'] > 0:
                    for end in ("Inner", "Outer"):
                        board_list.append({
                            "name": f"{side} Knob Stair {end} Stringer {n + 1}",
                            "width": step['closure_depth'],
                            "height": step['closure_height'],
                            "thickness": bt,
                            "description": f"{side} staircase {end.lower()} stringer {n + 1}; "
                                           f"riser lands on its front edge, tread on its top",
                        })

    return board_list


def generate_console(parameters):
    """
    Generate the complete normal console assembly.

    Args:
        parameters: Parameter dictionary containing all configuration values

    Returns:
        Compound object representing the complete normal console
    """
    p = DotDict(parameters)

    # Set default for show_dimensions if not present
    show_dims = getattr(p, 'show_dimensions_g', False)

    parts = []

    # Base right table
    parts.append(create_board(
        max_width=p.base_depth_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 0),
        show_dimensions=show_dims
    ))

    # Base left table
    parts.append(create_board(
        max_width=p.base_depth_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.organ_internal_width_g - 2*p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 0),
        show_dimensions=show_dims
    ))

    # Base back
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 90),
        show_dimensions=show_dims
    ))

    # Base front
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.base_depth_g-100, 0),
        rotation=(0, 0, 90),
        rectangular_holes=[[p.organ_internal_width_g/2, p.volume_pedals_hole_start_height_g + (p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g) / 2, p.volume_pedals_number_g * (p.volume_pedals_width_g + p.volume_pedals_spacing_g) + p.volume_pedals_spacing_g, p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g]],
        show_dimensions=show_dims
    ))

    # Base horizontal - the keyboard table. Its front edge can carry a recess so
    # the player can sit closer to the manuals.
    carve_on = getattr(p, 'carve_enabled_g', False)
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_depth_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.general_board_thickness_g, p.base_height_g + p.general_board_thickness_g),
        rotation=(0, 90, 90),
        show_dimensions=show_dims,
        carve_width=getattr(p, 'carve_width_g', 0) if carve_on else 0,
        carve_depth=getattr(p, 'carve_depth_g', 0) if carve_on else 0,
        carve_slope=getattr(p, 'carve_slope_g', 0) if carve_on else 0,
        carve_offset=getattr(p, 'carve_offset_g', 0) if carve_on else 0
    ))

    # Top lateral left
    parts.append(create_board(
        max_width=p.top_depth_g,
        max_height=p.top_height_g,
        min_width=p.top_notch_start_x_g,
        min_height=p.top_notch_start_y_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, p.base_height_g),
        rotation=(0, 0, 0),
        show_dimensions=show_dims
    ))

    # Top lateral right
    parts.append(create_board(
        max_width=p.top_depth_g,
        max_height=p.top_height_g,
        min_width=p.top_notch_start_x_g,
        min_height=p.top_notch_start_y_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.organ_internal_width_g - 2*p.general_board_thickness_g, 0, p.base_height_g),
        rotation=(0, 0, 0),
        show_dimensions=show_dims
    ))

    # Top back
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_height_g - 2 * p.general_board_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, p.base_height_g + p.general_board_thickness_g),
        rotation=(0, 0, 90),
        show_dimensions=show_dims
    ))

    # Top front
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_height_g - 2 * p.general_board_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.base_depth_g - p.general_board_thickness_g, p.base_height_g + p.general_board_thickness_g),
        rotation=(0, 0, 90),
        show_dimensions=show_dims
    ))

    # Top lid
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_depth_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, p.base_height_g + p.top_height_g),
        rotation=(0, 90, 90),
        show_dimensions=show_dims
    ))

    # Volume pedals
    for i in range(p.volume_pedals_number_g):
        parts.append(create_board(
            max_width=p.volume_pedals_width_g,
            max_height=p.volume_pedals_height_g,
            board_thickness=p.general_board_thickness_g,
            position=(-p.general_board_thickness_g - p.organ_internal_width_g / 2 + (p.volume_pedals_number_g * (p.volume_pedals_width_g + p.volume_pedals_spacing_g) + p.volume_pedals_spacing_g) / 2 - i * (p.volume_pedals_spacing_g + p.volume_pedals_width_g) - p.volume_pedals_spacing_g, p.base_depth_g - p.base_front_distance_g + p.general_board_thickness_g, p.volume_pedals_hole_start_height_g + 2 * p.volume_pedals_spacing_g),
            rotation=(0, -30, 90),
            show_dimensions=show_dims
        ))

    # Generate keyboards (manuals) on top of the horizontal divider
    num_manuals = getattr(p, 'keyboard_num_manuals_g', 2)
    if num_manuals > 0:
        # Calculate keyboard dimensions for centering
        kbd_dims = get_keyboard_dimensions(parameters)
        kbd_width = kbd_dims['width']
        kbd_depth = kbd_dims['depth']

        # Position keyboards centered on the console, on top of the horizontal divider
        # The horizontal divider top surface is at Z = base_height_g + general_board_thickness_g
        # Keyboards sit on top at Z = base_height_g + general_board_thickness_g
        #
        # Console X runs from -general_board_thickness to -(organ_internal_width + 2*general_board_thickness)
        # Console center X = -general_board_thickness - organ_internal_width/2
        # Console Y runs from 0 (back) to top_depth_g (front of horizontal divider)
        # Player sits at high Y values, facing toward -Y (back of console)
        # Keys should extend toward the player (in +Y direction)

        keyboard_y_offset = getattr(p, 'keyboard_y_offset_g', 0)

        # Position: centered in X, positioned near the front of the divider, on top of divider
        # Keyboard position is the back edge (low Y), keys extend toward player (+Y direction)
        # keyboard_y_offset is distance from back of divider (0 = at back, higher values move toward front)
        # The horizontal divider extends from Y=general_board_thickness_g to Y=top_depth_g+general_board_thickness_g
        # To place keyboard at front: back edge at (front_of_divider - kbd_depth)
        # Front of divider is at Y = general_board_thickness_g + top_depth_g
        keyboard_front_y = p.general_board_thickness_g + p.top_depth_g
        height_gap = getattr(p, 'keyboard_initial_height_gap_g', 0)

        # Horizontal boards are placed by their top face, so the divider surface
        # is at base_height_g + one thickness. The manuals then sit a further
        # thickness above that, matching the vertical console.
        table_top_z = p.base_height_g + p.general_board_thickness_g
        keyboard_position = (
            -p.general_board_thickness_g - p.organ_internal_width_g / 2 - kbd_width / 2,
            keyboard_front_y - kbd_depth + keyboard_y_offset,
            table_top_z + p.general_board_thickness_g + height_gap
        )

        keyboard_stack = generate_keyboard_stack(parameters, base_position=keyboard_position)
        parts.append(keyboard_stack)

        # Cheeks flanking the manuals, standing on the divider surface
        parts.extend(generate_keyboard_cheeks(
            parameters, keyboard_position, p.general_board_thickness_g,
            cheek_z=table_top_z, show_dimensions=show_dims
        ))

        # Terraced drawknob jambs either side of the manuals. A finite radius
        # bends them onto a concave arc facing the player; otherwise they are
        # the straight staircase with its side stringers and separate knobs.
        if getattr(p, 'knob_stair_radius_g', 0) > 0:
            parts.extend(generate_curved_knob_stairs(parameters))
        else:
            parts.extend(generate_knob_stairs(parameters, show_dimensions=show_dims))
            parts.extend(generate_knob_stair_knobs(parameters))

        # Combination piston rail under each manual
        parts.extend(generate_piston_rails(
            parameters, keyboard_position, p.general_board_thickness_g,
            rail_base_z=table_top_z, show_dimensions=show_dims
        ))

        # Plastic buttons through the rail holes
        parts.extend(generate_piston_buttons(
            parameters, keyboard_position, p.general_board_thickness_g,
            rail_base_z=table_top_z
        ))

        # Rocker (stop) tab bank on the upper front board, centred between the
        # top of the highest manual and the top of that board.
        top_manual_top = (keyboard_position[2]
                          + (num_manuals - 1) * getattr(p, 'keyboard_vertical_spacing_g', 73)
                          + kbd_dims['height'])
        board_top_z = p.base_height_g + p.top_height_g - p.general_board_thickness_g
        parts.extend(generate_rocker_tabs(
            parameters,
            front_y=p.base_depth_g,
            center_x=-p.general_board_thickness_g - p.organ_internal_width_g / 2,
            z_center=(top_manual_top + board_top_z) / 2
        ))

    # Combine all parts into a compound
    result = Compound(children=parts)

    return result


# Main execution for testing
if __name__ == "__main__":
    # Generate the console with default parameters
    params = get_default_parameters()
    console = generate_console(params)

    # Display the result (requires ocp_vscode)
    try:
        from ocp_vscode import show
        show(console)
    except ImportError:
        print("Note: Install ocp_vscode to visualize the model")
