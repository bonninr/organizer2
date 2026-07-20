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

from build123d import *
from utils import DotDict, create_board
from keyboard import (generate_keyboard_stack, get_keyboard_dimensions,
                      get_keyboard_stack_dimensions, generate_keyboard_cheeks,
                      get_keyboard_cheek_steps, generate_piston_rails,
                      get_piston_rail_specs)


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
        "Pistons": [
            {"pistons_enabled_g": True},   # Combination piston rail under each manual
            {"piston_count_g": 9},         # Number of pistons per rail
            {"piston_diameter_g": 15},     # Piston hole diameter (mm)
            {"piston_spacing_g": 45},      # Centre-to-centre spacing (mm)
            {"piston_rail_height_g": 38}   # Rail face height (mm); rail 1 is auto-sized to reach the table
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
                board_list.append({
                    "name": f"{side} Keyboard Cheek Step {n + 1}",
                    "width": step['depth'],
                    "height": step['height'],
                    "thickness": bt,
                    "description": f"{side} cheek step {n + 1} (manual {n + 1}), "
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

        # Combination piston rail under each manual
        parts.extend(generate_piston_rails(
            parameters, keyboard_position, p.general_board_thickness_g,
            rail_base_z=table_top_z, show_dimensions=show_dims
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
