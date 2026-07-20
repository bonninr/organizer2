"""
Keyboard Generator Module

This module generates organ/piano keyboard assemblies (manuals) with:
- White keys (naturals)
- Black keys (sharps/flats)
- Base plate connecting all keys
- Support for multiple keyboards stacked

Standard measurements based on piano industry standards:
- Octave span: ~164mm (6.46 inches)
- White key width: ~23.5mm at base
- Black key width: ~13.7mm
- 61 keys (5 octaves): ~870mm total width

Usage:
    from keyboard import generate_keyboard, generate_keyboard_stack, get_default_parameters

    params = get_default_parameters()
    keyboard = generate_keyboard(params)
"""

from build123d import *
from utils import DotDict, create_board


def calculate_white_keys(total_keys):
    """
    Calculate the number of white keys for a given total key count.

    Standard keyboard pattern per octave (starting from C):
    - White keys: C, D, E, F, G, A, B (7 per octave)
    - Black keys: C#, D#, F#, G#, A# (5 per octave)

    For a keyboard starting on C:
    - Full octaves have 12 keys (7 white + 5 black)
    - Remaining keys follow the pattern: C(w), C#(b), D(w), D#(b), E(w), F(w), F#(b), G(w), G#(b), A(w), A#(b), B(w)

    Args:
        total_keys: Total number of keys on the keyboard

    Returns:
        Number of white keys
    """
    # Pattern of white keys in an octave starting from C
    # Index 0-11: C=white, C#=black, D=white, D#=black, E=white, F=white, F#=black, G=white, G#=black, A=white, A#=black, B=white
    white_key_pattern = [True, False, True, False, True, True, False, True, False, True, False, True]

    white_count = 0
    for i in range(total_keys):
        if white_key_pattern[i % 12]:
            white_count += 1

    return white_count


def get_default_parameters():
    """
    Return default parameters for keyboard generation.

    Standard piano/organ keyboard measurements.
    Key width is calculated from total_width, num_keys, and gap:
        key_width = (total_width - (num_keys - 1) * gap) / num_keys

    Returns:
        Dictionary with parameter categories
    """
    return {
        "Keyboard": [
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
            {"keyboard_vertical_spacing_g": 80},     # Vertical spacing between manuals (mm)
            {"keyboard_depth_offset_g": 130}         # Each higher manual offset back (mm) = key_length - 20
        ]
    }


def generate_keyboard(parameters, position=(0, 0, 0)):
    """
    Generate a single keyboard (manual) assembly.

    The keyboard consists of:
    - A base plate connecting all keys
    - White keys (naturals) arranged in sequence
    - Black keys (sharps) placed between appropriate white keys

    Black key pattern per octave (C to B):
    - C (white), C# (black), D (white), D# (black), E (white)
    - F (white), F# (black), G (white), G# (black), A (white), A# (black), B (white)

    Note indices where black keys follow: 0 (C), 1 (D), 3 (F), 4 (G), 5 (A)

    Args:
        parameters: Parameter dictionary
        position: (x, y, z) position tuple for the keyboard

    Returns:
        Compound object representing the keyboard
    """
    p = DotDict(parameters)

    # Get total keys and calculate white key count
    total_keys = getattr(p, 'keyboard_total_keys_g', 61)
    num_white_keys = calculate_white_keys(total_keys)
    total_width = getattr(p, 'keyboard_total_width_g', 870)
    white_key_length = getattr(p, 'keyboard_white_key_length_g', 150)
    white_key_height = getattr(p, 'keyboard_white_key_height_g', 15)
    black_key_width_ratio = getattr(p, 'keyboard_black_key_width_ratio_g', 0.65)
    black_key_length = getattr(p, 'keyboard_black_key_length_g', 95)
    black_key_height = getattr(p, 'keyboard_black_key_height_g', 10)
    key_gap = getattr(p, 'keyboard_key_gap_g', 0.5)
    base_thickness = getattr(p, 'keyboard_base_thickness_g', 10)
    front_cut_depth = getattr(p, 'keyboard_white_key_front_cut_depth_g', 0)
    front_cut_height = getattr(p, 'keyboard_white_key_front_cut_height_g', 0)

    # Undercut at the key tip must stay inside the key
    front_cut_depth = max(0, min(front_cut_depth, white_key_length))
    front_cut_height = max(0, min(front_cut_height, white_key_height))

    # Calculate key width from total width, number of keys, and gap
    # Formula: total_width = num_keys * key_width + (num_keys - 1) * gap
    # Solving for key_width: key_width = (total_width - (num_keys - 1) * gap) / num_keys
    white_key_width = (total_width - (num_white_keys - 1) * key_gap) / num_white_keys
    black_key_width = white_key_width * black_key_width_ratio

    parts = []
    black_keys = []

    # Keyboard orientation: keys extend in +Y direction (toward player at high Y)
    # Position is the back edge (low Y), keys extend toward player (high Y)
    # Black keys are at the back (low Y), white key fronts toward high Y (player)

    # Create base plate - starts at position, extends in +Y
    with BuildPart() as base_builder:
        with BuildSketch(Plane.XY):
            Rectangle(total_width, white_key_length, align=(Align.MIN, Align.MIN))
        extrude(amount=base_thickness)

    base = base_builder.part
    base = Pos(position[0], position[1], position[2]) * base
    base.label = "material:white"  # White/ivory color for keyboard base
    parts.append(base)

    # Generate white keys and black keys
    # White key pattern in octave: C(0), D(1), E(2), F(3), G(4), A(5), B(6)
    # Black keys go AFTER: C(0)->C#, D(1)->D#, F(3)->F#, G(4)->G#, A(5)->A#
    # NO black key after: E(2), B(6)
    # Pattern: C C# D D# E | F F# G G# A A# B
    #          w b  w b  w   w b  w b  w b  w
    black_key_after = [True, True, False, True, True, True, False]  # After C,D,E,F,G,A,B

    for i in range(num_white_keys):
        # Keys are built right-to-left (from high X to low X) so that
        # when viewed from the player's position, low notes (C) are on the left
        x_pos = position[0] + total_width - (i + 1) * white_key_width - i * key_gap
        note_index = i % 7  # C=0, D=1, E=2, F=3, G=4, A=5, B=6

        # White key - extends from back (position[1]) toward player (+Y).
        # The underside of the tip is cut away so the top of the key hangs over
        # the front, as on a real natural key.
        with BuildPart() as white_key_builder:
            with BuildSketch(Plane.XY):
                Rectangle(white_key_width, white_key_length, align=(Align.MIN, Align.MIN))
            extrude(amount=white_key_height)

            if front_cut_depth > 0 and front_cut_height > 0:
                with BuildSketch(Plane.XY):
                    with Locations((white_key_width / 2,
                                    white_key_length - front_cut_depth / 2)):
                        Rectangle(white_key_width, front_cut_depth)
                extrude(amount=front_cut_height, mode=Mode.SUBTRACT)

        white_key = white_key_builder.part
        white_key = Pos(x_pos, position[1], position[2] + base_thickness) * white_key
        white_key.label = "material:white"  # White/ivory keys
        parts.append(white_key)

        # Black key logic - placed between current and next white key
        # Black keys exist after: C(0), D(1), F(3), G(4), A(5)
        # No black key after: E(2), B(6)
        if i < num_white_keys - 1:
            if black_key_after[note_index]:
                # Center the black key on the gap between white keys
                # Since keys are built right-to-left, black key goes to the LEFT of current white key
                black_x_pos = x_pos - (key_gap / 2) - (black_key_width / 2)

                with BuildPart() as black_key_builder:
                    with BuildSketch(Plane.XY):
                        Rectangle(black_key_width, black_key_length, align=(Align.MIN, Align.MIN))
                    extrude(amount=black_key_height)

                black_key = black_key_builder.part
                # Black key sits at back of keyboard (low Y), on top of white keys
                black_key = Pos(
                    black_x_pos,
                    position[1],  # At back (low Y)
                    position[2] + base_thickness + white_key_height
                ) * black_key
                black_key.label = "material:black"  # Black keys
                black_keys.append(black_key)

    # Combine all parts (white keys first, then black keys for proper layering)
    all_parts = parts + black_keys

    return Compound(children=all_parts)


def generate_keyboard_stack(parameters, base_position=(0, 0, 0)):
    """
    Generate a stack of multiple keyboards (manuals).

    Each keyboard is positioned slightly higher and further back than the one below.
    This mimics the typical organ console layout where higher manuals are
    stepped back for ergonomic access.

    Args:
        parameters: Parameter dictionary
        base_position: (x, y, z) position for the bottom keyboard

    Returns:
        Compound object representing all keyboards
    """
    p = DotDict(parameters)

    num_manuals = getattr(p, 'keyboard_num_manuals_g', 2)
    vertical_spacing = getattr(p, 'keyboard_vertical_spacing_g', 80)
    depth_offset = getattr(p, 'keyboard_depth_offset_g', 30)

    keyboards = []

    # Calculate depth offset if using auto value (keyboard depth - 20mm for overlap)
    white_key_length = getattr(p, 'keyboard_white_key_length_g', 150)
    if depth_offset >= white_key_length:  # If offset would cause no overlap, use calculated
        depth_offset = white_key_length - 20  # Total depth minus 20mm overlap

    for i in range(num_manuals):
        # Each manual is higher and further back (toward -Y, away from player)
        # Position is back edge, so stepping back means lower Y values
        kbd_position = (
            base_position[0],
            base_position[1] - i * depth_offset,  # Step back (toward -Y, away from player)
            base_position[2] + i * vertical_spacing  # Step up
        )

        keyboard = generate_keyboard(parameters, position=kbd_position)
        keyboards.append(keyboard)

    return Compound(children=keyboards)


def resolve_depth_offset(parameters):
    """
    Return the depth offset actually used when stacking manuals.

    generate_keyboard_stack clamps the configured offset when it would leave no
    overlap between manuals. Anything positioning itself against the stack must
    apply the same clamp or it will drift out of alignment.

    Args:
        parameters: Parameter dictionary

    Returns:
        float: Effective per-manual depth offset in mm
    """
    p = DotDict(parameters)

    depth_offset = getattr(p, 'keyboard_depth_offset_g', 30)
    white_key_length = getattr(p, 'keyboard_white_key_length_g', 150)
    if depth_offset >= white_key_length:
        depth_offset = white_key_length - 20

    return depth_offset


def get_keyboard_cheek_steps(parameters, base_position, board_thickness,
                             cheek_z=None, back_y=None, cheek_height=None):
    """
    Calculate the geometry of the keyboard cheek staircase.

    Cheeks are vertical boards flanking the manuals, one step per manual level.
    Each step's front edge sits at its own manual's key tips; because higher
    manuals are stepped back, the steps get shorter as they get taller, which is
    what produces the staircase profile.

    Each step's top clears its own manual by cheek_height, and each step starts
    where the previous one ended, so the cheek is one continuous piece. The
    bottom step starts at cheek_z (the table surface) rather than at the keyboard
    base, so the cheeks rest on the table however far above it the manuals sit.
    Deriving the step heights from cheek_height alone would leave them floating
    whenever the manual spacing exceeds it.

    The whole staircase shares one back edge, at the rearmost manual's back edge.

    Args:
        parameters: Parameter dictionary
        base_position: (x, y, z) base position of the keyboard stack, as passed
                       to generate_keyboard_stack. x is the stack's minimum X.
        board_thickness: Thickness of the cheek boards (mm)
        cheek_z: Z of the surface the cheeks stand on (the table top). Defaults
                 to the keyboard base height.
        back_y: Y of the shared back edge. Defaults to the rearmost manual's back
                edge; pass the table's back edge for cheeks that run full depth.
        cheek_height: Clearance above each manual's base. Defaults to
                      keyboard_cheek_height_g. Pass the manual's own height to
                      finish the cheeks flush with the black keys.

    Returns:
        List of dicts, one per step, each with:
            'depth', 'height', 'z', 'x_left', 'x_right', 'y'
        Left/right x are the minimum-X face of each cheek board.
    """
    p = DotDict(parameters)

    num_manuals = int(getattr(p, 'keyboard_num_manuals_g', 2))
    if num_manuals <= 0:
        return []

    vertical_spacing = getattr(p, 'keyboard_vertical_spacing_g', 80)
    if cheek_height is None:
        cheek_height = getattr(p, 'keyboard_cheek_height_g', 60)
    depth_offset = resolve_depth_offset(parameters)

    kbd_dims = get_keyboard_dimensions(parameters)
    kbd_width = kbd_dims['width']
    kbd_depth = kbd_dims['depth']

    # By default all steps share the back edge of the rearmost (highest) manual
    if back_y is None:
        back_y = base_position[1] - (num_manuals - 1) * depth_offset

    steps = []
    z = base_position[2] if cheek_z is None else cheek_z
    for n in range(num_manuals):
        front_y = base_position[1] - n * depth_offset + kbd_depth
        depth = front_y - back_y
        # Top of this step clears its own manual by cheek_height
        top = base_position[2] + n * vertical_spacing + cheek_height
        height = top - z
        if depth <= 0 or height <= 0:
            break

        steps.append({
            'depth': depth,
            'height': height,
            'y': back_y,
            'z': z,
            'x_left': base_position[0] - board_thickness,
            'x_right': base_position[0] + kbd_width,
        })
        z = top

    return steps


def generate_keyboard_cheeks(parameters, base_position, board_thickness,
                             cheek_z=None, back_y=None, cheek_height=None,
                             show_dimensions=False):
    """
    Generate the keyboard cheek boards flanking a manual stack.

    Args:
        parameters: Parameter dictionary
        base_position: (x, y, z) base position of the keyboard stack
        board_thickness: Thickness of the cheek boards (mm)
        cheek_z: Z of the table surface the cheeks stand on
        show_dimensions: Passed through to create_board

    Returns:
        List of Part objects (empty if cheeks are disabled or there are no manuals)
    """
    p = DotDict(parameters)

    if not getattr(p, 'keyboard_cheeks_enabled_g', False):
        return []

    parts = []
    for step in get_keyboard_cheek_steps(parameters, base_position, board_thickness,
                                         cheek_z, back_y, cheek_height):
        for x in (step['x_left'], step['x_right']):
            parts.append(create_board(
                max_width=step['depth'],
                max_height=step['height'],
                board_thickness=board_thickness,
                position=(x, step['y'], step['z']),
                rotation=(0, 0, 0),
                show_dimensions=show_dimensions
            ))

    return parts


def get_piston_rail_specs(parameters, board_thickness, first_rail_max=None):
    """
    Calculate the combination piston rail for each manual.

    A piston rail is the board carrying the round combination pistons, mounted
    across the full keyboard width immediately under a manual's base plate, with
    its face level with that manual's key tips so the player thumbs it from
    below the keys.

    The rail height is clamped to the space actually available under the manual:
    between two manuals that is the spacing minus the base plate and white key,
    so the rail can never collide with the manual below it.

    Args:
        parameters: Parameter dictionary
        board_thickness: Depth of the rail front-to-back (mm)
        first_rail_max: Space available under the first manual, i.e. the distance
                        from the table surface up to its base plate. The bottom
                        rail is clamped to this so it cannot grow up into the
                        manual; it stands on the table either way.

    Returns:
        List of dicts, one per manual, each with:
            'width', 'height', 'thickness', 'holes'
        'holes' is a list of [x, y, diameter] in the rail's own face coordinates.
    """
    p = DotDict(parameters)

    if not getattr(p, 'pistons_enabled_g', False):
        return []

    num_manuals = int(getattr(p, 'keyboard_num_manuals_g', 2))
    if num_manuals <= 0:
        return []

    count = int(getattr(p, 'piston_count_g', 9))
    diameter = getattr(p, 'piston_diameter_g', 15)
    spacing = getattr(p, 'piston_spacing_g', 45)
    height = getattr(p, 'piston_rail_height_g', 25)
    vertical_spacing = getattr(p, 'keyboard_vertical_spacing_g', 80)
    base_thickness = getattr(p, 'keyboard_base_thickness_g', 10)
    white_key_height = getattr(p, 'keyboard_white_key_height_g', 15)

    kbd_dims = get_keyboard_dimensions(parameters)
    width = kbd_dims['width']

    # Never let a rail reach down into the manual below it
    if num_manuals > 1:
        available = vertical_spacing - base_thickness - white_key_height
        height = min(height, available)
    if height <= 0:
        return []

    # Piston holes must leave material all round: a hole wider than the rail
    # would saw straight through it and break the board into loose fragments.
    hole_margin = 2

    def _holes(rail_height):
        d = min(diameter, rail_height - 2 * hole_margin)
        if count <= 0 or d <= 0:
            return []

        pitch = spacing
        if count > 1 and (count - 1) * pitch + d > width:
            pitch = (width - d) / (count - 1)

        return [[width / 2 + (i - (count - 1) / 2) * pitch, rail_height / 2, d]
                for i in range(count)]

    specs = []
    for n in range(num_manuals):
        # The bottom rail stands on the table; the rest hang from their own
        # manual's base plate. Either way the configured height applies, clamped
        # to whatever space that rail actually has.
        h = height
        if n == 0 and first_rail_max is not None:
            h = min(h, first_rail_max)
        if h <= 0:
            continue
        specs.append({
            'width': width,
            'height': h,
            'thickness': board_thickness,
            'holes': _holes(h),
        })

    return specs


def generate_piston_rails(parameters, base_position, board_thickness,
                          rail_base_z=None, show_dimensions=False):
    """
    Generate the combination piston rail under each manual.

    Args:
        parameters: Parameter dictionary
        base_position: (x, y, z) base position of the manual stack
        board_thickness: Depth of the rail front-to-back (mm)
        rail_base_z: Z of the table surface. When given, the bottom rail is
                     sized to stand on it rather than hang in mid air.
        show_dimensions: Passed through to create_board

    Returns:
        List of Part objects (empty if pistons are disabled)
    """
    p = DotDict(parameters)

    first_rail_max = (None if rail_base_z is None
                      else base_position[2] - rail_base_z)
    specs = get_piston_rail_specs(parameters, board_thickness, first_rail_max)
    if not specs:
        return []

    vertical_spacing = getattr(p, 'keyboard_vertical_spacing_g', 80)
    depth_offset = resolve_depth_offset(parameters)
    kbd_depth = get_keyboard_dimensions(parameters)['depth']

    parts = []
    for n, spec in enumerate(specs):
        # Face flush with this manual's key tips, hung under its base plate
        front_y = base_position[1] - n * depth_offset + kbd_depth

        # Bottom rail sits on the table; upper rails hang from their base plate
        if n == 0 and rail_base_z is not None:
            z = rail_base_z
        else:
            z = base_position[2] + n * vertical_spacing - spec['height']

        parts.append(create_board(
            max_width=spec['width'],
            max_height=spec['height'],
            board_thickness=spec['thickness'],
            position=(base_position[0] + spec['width'],
                      front_y - spec['thickness'],
                      z),
            rotation=(0, 0, 90),
            circular_holes=spec['holes'],
            show_dimensions=show_dimensions
        ))

    return parts


def get_keyboard_dimensions(parameters):
    """
    Calculate the overall dimensions of a keyboard.

    Useful for positioning keyboards within the console.

    Args:
        parameters: Parameter dictionary

    Returns:
        dict with 'width', 'depth', 'height', 'num_white_keys' in mm
    """
    p = DotDict(parameters)

    total_keys = getattr(p, 'keyboard_total_keys_g', 61)
    num_white_keys = calculate_white_keys(total_keys)
    total_width = getattr(p, 'keyboard_total_width_g', 870)
    white_key_length = getattr(p, 'keyboard_white_key_length_g', 150)
    white_key_height = getattr(p, 'keyboard_white_key_height_g', 15)
    black_key_height = getattr(p, 'keyboard_black_key_height_g', 10)
    base_thickness = getattr(p, 'keyboard_base_thickness_g', 10)

    total_depth = white_key_length
    total_height = base_thickness + white_key_height + black_key_height

    return {
        'width': total_width,
        'depth': total_depth,
        'height': total_height,
        'num_white_keys': num_white_keys
    }


def get_keyboard_stack_dimensions(parameters):
    """
    Calculate the overall dimensions of a keyboard stack.

    Args:
        parameters: Parameter dictionary

    Returns:
        dict with 'width', 'depth', 'height' in mm
    """
    p = DotDict(parameters)

    num_manuals = getattr(p, 'keyboard_num_manuals_g', 2)
    vertical_spacing = getattr(p, 'keyboard_vertical_spacing_g', 80)
    depth_offset = getattr(p, 'keyboard_depth_offset_g', 30)

    single_dims = get_keyboard_dimensions(parameters)

    # Stack dimensions account for offset of each manual
    total_width = single_dims['width']
    total_depth = single_dims['depth'] + (num_manuals - 1) * depth_offset
    total_height = single_dims['height'] + (num_manuals - 1) * vertical_spacing

    return {
        'width': total_width,
        'depth': total_depth,
        'height': total_height
    }


# Main execution for testing
if __name__ == "__main__":
    # Generate a keyboard stack with default parameters
    params = get_default_parameters()

    # Print dimensions
    dims = get_keyboard_dimensions(params)
    print(f"Single keyboard dimensions: {dims['width']:.1f}mm x {dims['depth']:.1f}mm x {dims['height']:.1f}mm")

    stack_dims = get_keyboard_stack_dimensions(params)
    print(f"Keyboard stack dimensions: {stack_dims['width']:.1f}mm x {stack_dims['depth']:.1f}mm x {stack_dims['height']:.1f}mm")

    # Generate the keyboard stack
    keyboard_stack = generate_keyboard_stack(params)

    # Display the result (requires ocp_vscode)
    try:
        from ocp_vscode import show
        show(keyboard_stack)
    except ImportError:
        print("ocp_vscode not available. Run this in VS Code with OCP CAD Viewer extension.")
        print("Keyboard stack generated successfully.")
