import math
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
        ],
        "Frame": [
            {"frame_side_height_g": 120},       # Height of the side cheek boards
            {"frame_side_depth_g": 0},          # Depth of side boards (0 = auto-calculate from pedal length)
            {"frame_back_height_g": 100},       # Height of back board above pedals
            {"frame_back_depth_g": 80},         # Depth/thickness of back board area
            {"frame_front_height_g": 40},       # Height of front board (0 = no front board)
            {"sharp_cap_length_end_g": 150},    # Length of caps at the ends (left/right)
            {"sharp_cap_length_middle_g": 100}, # Length of caps in the middle
            {"sharp_cap_arc_g": 1.0},           # Arc curvature (0=linear, 1=parabolic arc)
            {"sharp_cap_height_ratio_g": 2.0},  # Cap height as multiple of pedal thickness
            {"sharp_cap_notch_height_g": 0.75}, # Min height ratio (0.0-1.0, where notch ends)
            {"sharp_cap_notch_width_g": 0.75},  # Min width ratio (0.0-1.0, where notch starts)
            {"sharp_cap_color_g": True}         # Whether to add colored caps to sharp pedals
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

    # Calculate frame side depth (auto-calculate if 0)
    frame_side_depth = p.frame_side_depth_g if p.frame_side_depth_g > 0 else max(p.short_pedal_length_g, p.tall_pedal_length_g) + p.frame_back_depth_g

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

    # Sharp caps (black note end pieces) - angled/notched pieces with variable length
    if tall_count > 0 and getattr(p, 'sharp_cap_color_g', True):
        cap_height = p.pedal_thickness_g * 2  # About 2 inches tall
        cap_length_end = getattr(p, 'sharp_cap_length_end_g', 150)
        cap_length_middle = getattr(p, 'sharp_cap_length_middle_g', 100)
        board_list.append({
            "name": "Sharp Caps",
            "width": p.tall_pedal_width_g,
            "height": cap_length_end,  # Use max length for cutting list
            "thickness": cap_height,
            "description": f"Dark angled caps for sharp pedals - quantity: {tall_count}",
            "notes": f"Variable length: {cap_length_end}mm at ends, {cap_length_middle}mm in middle. 30° notch angle."
        })

    # Frame side boards (cheeks)
    board_list.append({
        "name": "Frame Side Left",
        "width": frame_side_depth,
        "height": p.frame_side_height_g,
        "thickness": p.general_board_thickness_g,
        "description": "Left side cheek board"
    })
    board_list.append({
        "name": "Frame Side Right",
        "width": frame_side_depth,
        "height": p.frame_side_height_g,
        "thickness": p.general_board_thickness_g,
        "description": "Right side cheek board"
    })

    # Frame back board
    if p.frame_back_height_g > 0:
        board_list.append({
            "name": "Frame Back",
            "width": total_width + 2 * p.general_board_thickness_g,
            "height": p.frame_back_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Back board behind pedals"
        })

    # Frame front board (optional)
    if p.frame_front_height_g > 0:
        board_list.append({
            "name": "Frame Front",
            "width": total_width + 2 * p.general_board_thickness_g,
            "height": p.frame_front_height_g,
            "thickness": p.general_board_thickness_g,
            "description": "Front board in front of pedals"
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
    sharp_caps = []  # Separate list for sharp caps (different color)

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

    # Get sharp cap parameters
    sharp_cap_length_end = getattr(p, 'sharp_cap_length_end_g', 150)
    sharp_cap_length_middle = getattr(p, 'sharp_cap_length_middle_g', 100)
    sharp_cap_arc = getattr(p, 'sharp_cap_arc_g', 1.0)
    sharp_cap_height_ratio = getattr(p, 'sharp_cap_height_ratio_g', 2.0)
    sharp_cap_notch_height = getattr(p, 'sharp_cap_notch_height_g', 0.75)
    sharp_cap_notch_width = getattr(p, 'sharp_cap_notch_width_g', 0.75)
    add_sharp_caps = getattr(p, 'sharp_cap_color_g', True)
    cap_height = p.pedal_thickness_g * sharp_cap_height_ratio

    # Count total sharp pedals to calculate arc positions
    total_sharps = pattern.count('t')

    # Base Z for pedals
    # Enclosure sits ~5mm above floor, pedals are ~50mm (2 inches) above floor for pivot clearance
    enclosure_base_z = 5  # 5mm gap from floor for enclosure
    pedal_base_z = 50     # ~2 inches clearance for pedal movement

    # Generate pedals according to pattern using create_board
    # create_board places board from position: X+thickness, Y+width, Z+height
    sharp_index = 0  # Track which sharp pedal we're on for arc calculation

    for char in pattern:
        if char == 's':
            # Short pedal (natural note) - extends in -Y direction
            pedal_part = create_board(
                max_width=p.short_pedal_length_g,      # Y dimension (length)
                max_height=p.pedal_thickness_g * 2,    # Z dimension (height)
                board_thickness=p.short_pedal_width_g, # X dimension (width)
                position=(
                    current_x,
                    -p.base_depth_g - p.short_pedal_length_g,  # Start at far end
                    pedal_base_z
                ),
                rotation=(0, 0, 0)
            )
            parts.append(pedal_part)
            current_x += p.short_pedal_width_g + p.pedal_spacing_g

        elif char == 't':
            # Tall pedal (sharp note) - thinner height
            pedal_part = create_board(
                max_width=p.tall_pedal_length_g,
                max_height=p.pedal_thickness_g,
                board_thickness=p.tall_pedal_width_g,
                position=(
                    current_x,
                    -p.base_depth_g - p.tall_pedal_length_g,
                    pedal_base_z
                ),
                rotation=(0, 0, 0)
            )
            parts.append(pedal_part)

            # Add sharp cap - angled piece ON TOP of the sharp pedal at the far end
            if add_sharp_caps and total_sharps > 0:
                # Calculate cap length based on position using parametric arc
                # t goes from 0 (first sharp) to 1 (last sharp)
                if total_sharps > 1:
                    t = sharp_index / (total_sharps - 1)
                else:
                    t = 0.5

                # Parametric arc: interpolate between end and middle lengths
                # arc=0: linear interpolation, arc=1: parabolic (smooth curve)
                # Formula: length = end - (end - middle) * (1 - (2*t - 1)^2) * arc_factor
                # This gives end length at t=0 and t=1, middle length at t=0.5
                normalized = 2 * t - 1  # Maps t from [0,1] to [-1,1]
                if sharp_cap_arc == 0:
                    # Linear case: V-shape
                    arc_factor = 1 - abs(normalized)
                else:
                    # Parabolic arc: smooth curve
                    arc_factor = 1 - normalized * normalized

                sharp_cap_length = sharp_cap_length_end - (sharp_cap_length_end - sharp_cap_length_middle) * arc_factor

                # Calculate notch using configurable ratios
                # create_board polygon: (0,0), (max_width,0), (max_width,min_height), (min_width,max_height), (0,max_height)
                # The notch diagonal goes from (max_width, min_height) to (min_width, max_height)
                # min_height = height at the back (Y=max_width end)
                # min_width = where the full height (max_height) starts

                # Use the configurable ratios
                min_cap_height = cap_height * sharp_cap_notch_height  # e.g., 75% of full height
                min_cap_width = sharp_cap_length * sharp_cap_notch_width  # e.g., 75% of full length

                # Cap sits on top of pedal, at the far end, with angled notch
                cap_part = create_board(
                    max_width=sharp_cap_length,           # Y dimension (full length)
                    max_height=cap_height,                # Z dimension (full height at front)
                    min_width=min_cap_width,              # Where the full height starts
                    min_height=min_cap_height,            # Height at the back (lower)
                    board_thickness=p.tall_pedal_width_g, # X dimension (width)
                    position=(
                        current_x,
                        -p.base_depth_g - p.tall_pedal_length_g,  # At far end of pedal
                        pedal_base_z + p.pedal_thickness_g        # On top of pedal
                    ),
                    rotation=(0, 0, 0),
                    material="black"  # Black material for sharp pedal caps
                )
                sharp_caps.append(cap_part)
                sharp_index += 1

            current_x += p.tall_pedal_width_g + p.pedal_spacing_g

        elif char == 'b':
            # Blank space - just advance position
            current_x += p.short_pedal_width_g + p.pedal_spacing_g

    # Calculate frame dimensions
    frame_back_depth = getattr(p, 'frame_back_depth_g', 80)
    frame_side_depth = getattr(p, 'frame_side_depth_g', 0)
    if frame_side_depth == 0:
        frame_side_depth = max(p.short_pedal_length_g, p.tall_pedal_length_g) + frame_back_depth

    frame_side_height = getattr(p, 'frame_side_height_g', 120)
    frame_back_height = getattr(p, 'frame_back_height_g', 100)
    frame_front_height = getattr(p, 'frame_front_height_g', 40)

    # Frame/enclosure base Z position (sits on floor with small gap)
    frame_base_z = enclosure_base_z

    # Add frame side boards (cheeks) - vertical boards on sides
    # Left side board - extends along Y (depth), height in Z
    left_side_part = create_board(
        max_width=frame_side_depth,      # Y dimension (depth)
        max_height=frame_side_height,    # Z dimension (height)
        board_thickness=p.general_board_thickness_g,  # X dimension (thickness)
        position=(
            -total_width / 2 - p.general_board_thickness_g,
            -p.base_depth_g - frame_side_depth,  # Start at back
            frame_base_z
        ),
        rotation=(0, 0, 0)
    )
    parts.append(left_side_part)

    # Right side board
    right_side_part = create_board(
        max_width=frame_side_depth,
        max_height=frame_side_height,
        board_thickness=p.general_board_thickness_g,
        position=(
            total_width / 2,
            -p.base_depth_g - frame_side_depth,
            frame_base_z
        ),
        rotation=(0, 0, 0)
    )
    parts.append(right_side_part)

    # Add frame back board - rotated to XZ plane (facing forward)
    # With (0,0,90) rotation: max_width goes in -X, thickness goes in +Y
    if frame_back_height > 0:
        back_part = create_board(
            max_width=total_width + 2 * p.general_board_thickness_g,
            max_height=frame_back_height,
            board_thickness=p.general_board_thickness_g,
            position=(
                total_width / 2 + p.general_board_thickness_g,  # Right edge, extends left
                -p.base_depth_g - frame_side_depth,
                frame_base_z
            ),
            rotation=(0, 0, 90)
        )
        parts.append(back_part)

    # Add frame front board
    if frame_front_height > 0:
        front_part = create_board(
            max_width=total_width + 2 * p.general_board_thickness_g,
            max_height=frame_front_height,
            board_thickness=p.general_board_thickness_g,
            position=(
                total_width / 2 + p.general_board_thickness_g,
                -p.base_depth_g,
                frame_base_z
            ),
            rotation=(0, 0, 90)
        )
        parts.append(front_part)

    # Combine all parts into a compound
    # Note: sharp_caps are added last, so they will be the last meshes in the GLTF export
    # The Three.js viewer identifies them by their position (after normal parts count)
    all_parts = parts + sharp_caps

    # Store metadata about mesh counts for the viewer
    # This will be used to identify which meshes are sharp caps
    result = Compound(children=all_parts)

    # Store counts as a custom attribute (will be available to streamlit app)
    result._wood_mesh_count = len(parts)
    result._cap_mesh_count = len(sharp_caps)

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
