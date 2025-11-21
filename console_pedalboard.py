from build123d import *
from utils import DotDict, create_board


def get_default_parameters():
    """
    Return default parameters for the organ pedalboard.

    Returns:
        Dictionary with parameter categories
    """
    return {
        "General": [
            {"general_board_thickness_g": 18},
            {"general_board_offset_g": 5}
        ],
        "Pedals": [
            {"number_of_notes_g": 30},      # Total number of notes (pedals)
            {"short_pedal_width_g": 25.4},  # 1 inch in mm - width of each short pedal
            {"tall_pedal_width_g": 25.4},   # 1 inch in mm - width of each tall pedal
            {"short_pedal_length_g": 700},  # Length of short pedals (extending forward) ~70cm
            {"tall_pedal_length_g": 700},   # Length of tall pedals (extending forward) ~70cm
            {"pedal_height_g": 150},        # Height above base
            {"pedal_thickness_g": 25.4},    # 1 inch - thickness/height of short pedal cross-section
            {"pedal_spacing_g": 3}          # Gap between pedals
        ],
        "Base": [
            {"base_height_g": 100},         # Height of the base frame
            {"base_depth_g": 200},          # Depth of the base frame from front
            {"lateral_board_height_g": 250} # Height of lateral side panels
        ]
    }


def generate_ago_pattern(number_of_notes):
    """
    Generate AGO (American Guild of Organists) standard pedalboard pattern.

    The standard pattern per octave is: s,t,s,t,s,b,s,t,s,t,s,t,s,b
    Where: s=short (natural notes), t=tall (sharp/flat notes), b=blank space

    Args:
        number_of_notes: Total number of notes to generate

    Returns:
        Pattern string (e.g., "ststsb stststs b ststsb stststs b")
    """
    # Standard AGO pattern for one octave (14 positions: 12 notes + 2 blanks)
    octave_pattern = "ststsb stststs b"

    # Calculate how many complete octaves and remaining notes
    positions_per_octave = 14  # 12 notes + 2 blanks
    notes_per_octave = 12

    complete_octaves = number_of_notes // notes_per_octave
    remaining_notes = number_of_notes % notes_per_octave

    # Build the pattern
    pattern_parts = []

    # Add complete octaves
    for _ in range(complete_octaves):
        pattern_parts.append(octave_pattern)

    # Add remaining notes if any
    if remaining_notes > 0:
        # Extract the needed portion of the pattern (excluding blanks)
        partial_pattern = ""
        note_count = 0
        for char in octave_pattern:
            if char != ' ':
                partial_pattern += char
                if char in ['s', 't']:
                    note_count += 1
                    if note_count >= remaining_notes:
                        break
            elif partial_pattern:  # Add space if we've started building the pattern
                partial_pattern += char
        pattern_parts.append(partial_pattern.strip())

    return " ".join(pattern_parts)


def generate_board_list(parameters):
    """
    Generate a list of boards needed for the pedalboard.

    Args:
        parameters: Parameter dictionary

    Returns:
        List of board specifications
    """
    p = DotDict(parameters)

    board_list = []

    # Generate the pattern based on number of notes
    pattern = generate_ago_pattern(p.number_of_notes_g).replace(" ", "")
    short_count = pattern.count('s')
    tall_count = pattern.count('t')

    # Calculate total width
    total_width = 0
    for char in pattern:
        if char == 's':
            total_width += p.short_pedal_width_g + p.pedal_spacing_g
        elif char == 't':
            total_width += p.tall_pedal_width_g + p.pedal_spacing_g
        elif char == 'b':
            total_width += p.short_pedal_width_g + p.pedal_spacing_g  # Blank space same width as short

    # Short pedals
    if short_count > 0:
        board_list.append({
            "name": "Short Pedals",
            "width": p.short_pedal_width_g,
            "height": p.short_pedal_length_g,
            "thickness": p.pedal_thickness_g,
            "description": f"Short pedals (natural notes) - quantity: {short_count}"
        })

    # Tall pedals
    if tall_count > 0:
        board_list.append({
            "name": "Tall Pedals",
            "width": p.tall_pedal_width_g,
            "height": p.tall_pedal_length_g,
            "thickness": p.pedal_thickness_g,
            "description": f"Tall pedals (sharp/flat notes) - quantity: {tall_count}"
        })

    return board_list


def generate_console(parameters):
    """
    Generate the complete organ pedalboard assembly.

    Args:
        parameters: Parameter dictionary containing all configuration values

    Returns:
        Compound object representing the complete pedalboard
    """
    p = DotDict(parameters)

    parts = []

    # Generate the pattern based on number of notes and reverse it for horizontal mirroring
    pattern = generate_ago_pattern(p.number_of_notes_g).replace(" ", "")
    pattern = pattern[::-1]  # Reverse the pattern to mirror horizontally

    # Calculate total width
    total_width = 0
    for char in pattern:
        if char == 's':
            total_width += p.short_pedal_width_g + p.pedal_spacing_g
        elif char == 't':
            total_width += p.tall_pedal_width_g + p.pedal_spacing_g
        elif char == 'b':
            total_width += p.short_pedal_width_g + p.pedal_spacing_g

    # Starting position (centered)
    current_x = -total_width / 2

    # Generate pedals according to pattern
    # Pedals are simple boxes extending forward (negative Y direction)
    # Matching FreeCAD example: 22x22mm cross-section, 700mm long
    for char in pattern:
        if char == 's':
            # Short pedal - 1x2 inch cross-section, 700mm long
            # Create box: width (X) × length (Y) × height (Z)
            with BuildPart() as pedal:
                Box(
                    p.short_pedal_width_g,           # Width in X
                    p.short_pedal_length_g,          # Length in Y (extending forward)
                    p.pedal_thickness_g * 2,         # Height in Z (1x2 inch cross-section)
                    align=(Align.CENTER, Align.MAX, Align.MIN)  # Centered in X, extends in -Y, starts at base
                )
            # Position the pedal
            pedal_part = Pos(current_x + p.short_pedal_width_g / 2, -p.base_depth_g, p.base_height_g + p.pedal_height_g) * pedal.part
            parts.append(pedal_part)
            current_x += p.short_pedal_width_g + p.pedal_spacing_g

        elif char == 't':
            # Tall pedal - 1x1 inch cross-section, 700mm long
            with BuildPart() as pedal:
                Box(
                    p.tall_pedal_width_g,            # Width in X
                    p.tall_pedal_length_g,           # Length in Y (extending forward)
                    p.pedal_thickness_g,             # Height in Z (1x1 inch cross-section)
                    align=(Align.CENTER, Align.MAX, Align.MIN)  # Centered in X, extends in -Y, starts at base
                )
            # Position the pedal
            pedal_part = Pos(current_x + p.tall_pedal_width_g / 2, -p.base_depth_g, p.base_height_g + p.pedal_height_g) * pedal.part
            parts.append(pedal_part)
            current_x += p.tall_pedal_width_g + p.pedal_spacing_g

        elif char == 'b':
            # Blank space - just advance position
            current_x += p.short_pedal_width_g + p.pedal_spacing_g

    # Combine all parts into a compound
    result = Compound(children=parts)

    return result


# Main execution for testing
if __name__ == "__main__":
    # Generate the pedalboard with default parameters
    params = get_default_parameters()
    pedalboard = generate_console(params)

    # Display the result (requires ocp_vscode)
    try:
        from ocp_vscode import show
        show(pedalboard)
    except ImportError:
        print("ocp_vscode not available. Run this in VS Code with OCP CAD Viewer extension.")
        print("Pedalboard generated successfully.")
