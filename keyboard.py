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
from utils import DotDict


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

        # White key - extends from back (position[1]) toward player (+Y)
        with BuildPart() as white_key_builder:
            with BuildSketch(Plane.XY):
                Rectangle(white_key_width, white_key_length, align=(Align.MIN, Align.MIN))
            extrude(amount=white_key_height)

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
