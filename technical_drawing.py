"""
Technical Drawing Generator - A3 Plan with Orthographic Views

This module generates A3 technical drawings with:
- 6 orthographic views (front, back, top, bottom, left, right)
- Perspective/isometric view
- Exploded view
- Dimension annotations using build123d's DimensionLine

Uses build123d's project_to_viewport(), ExportSVG, and DimensionLine for rendering.
"""

import os
import tempfile
from io import BytesIO
from build123d import *

from utils import DotDict, create_board


# Color scheme for technical drawings
COLORS = {
    "visible": (139, 69, 19),      # Saddle brown for visible edges
    "hidden": (153, 153, 153),     # Gray for hidden edges
    "fill": (222, 184, 135),       # Burlywood for solid fill
    "dimension": (0, 0, 0),        # Black for dimensions
    "background": (255, 255, 255), # White background
}


def generate_view_projection(model, view_name, distance=3000):
    """
    Generate a 2D projection of the model from a specific viewpoint.

    Args:
        model: The 3D Compound model
        view_name: One of 'front', 'back', 'top', 'bottom', 'left', 'right', 'perspective'
        distance: Distance from the model center for the viewport

    Returns:
        tuple: (visible_edges, hidden_edges, bbox_2d)
    """
    bbox = model.bounding_box()
    center = (
        (bbox.min.X + bbox.max.X) / 2,
        (bbox.min.Y + bbox.max.Y) / 2,
        (bbox.min.Z + bbox.max.Z) / 2
    )

    view_configs = {
        "front": {
            "origin": (center[0], center[1] + distance, center[2]),
            "up": (0, 0, 1)
        },
        "back": {
            "origin": (center[0], center[1] - distance, center[2]),
            "up": (0, 0, 1)
        },
        "top": {
            "origin": (center[0], center[1], center[2] + distance),
            "up": (0, 1, 0)
        },
        "bottom": {
            "origin": (center[0], center[1], center[2] - distance),
            "up": (0, -1, 0)
        },
        "left": {
            "origin": (center[0] - distance, center[1], center[2]),
            "up": (0, 0, 1)
        },
        "right": {
            "origin": (center[0] + distance, center[1], center[2]),
            "up": (0, 0, 1)
        },
        "perspective": {
            "origin": (center[0] + distance * 0.7, center[1] + distance * 0.7, center[2] + distance * 0.5),
            "up": (0, 0, 1)
        }
    }

    config = view_configs.get(view_name, view_configs["front"])

    visible, hidden = model.project_to_viewport(
        viewport_origin=config["origin"],
        viewport_up=config["up"],
        look_at=center
    )

    # Calculate 2D bounding box of the projection
    all_edges = visible + hidden
    if all_edges:
        compound = Compound(children=all_edges)
        bbox_2d = compound.bounding_box()
    else:
        bbox_2d = None

    return visible, hidden, bbox_2d


def create_dimensions_for_view(bbox_2d, view_name, draft, dim_offset=50):
    """
    Create dimension lines for a projected view.

    Args:
        bbox_2d: 2D bounding box of the projection
        view_name: Name of the view for labeling
        draft: Draft object for styling
        dim_offset: Offset distance for dimension lines

    Returns:
        list: List of DimensionLine objects
    """
    dimensions = []

    if bbox_2d is None:
        return dimensions

    min_x, max_x = bbox_2d.min.X, bbox_2d.max.X
    min_y, max_y = bbox_2d.min.Y, bbox_2d.max.Y
    width = max_x - min_x
    height = max_y - min_y

    try:
        # Width dimension at bottom
        if width > 10:  # Only add dimension if significant
            width_dim = DimensionLine(
                path=[(min_x, min_y - dim_offset), (max_x, min_y - dim_offset)],
                draft=draft
            )
            dimensions.append(width_dim)

        # Height dimension on left
        if height > 10:
            height_dim = DimensionLine(
                path=[(min_x - dim_offset, min_y), (min_x - dim_offset, max_y)],
                draft=draft
            )
            dimensions.append(height_dim)

    except Exception as e:
        pass  # Skip dimensions if creation fails

    return dimensions


def generate_exploded_view(model, console_type, parameters, explosion_offset=150):
    """
    Generate an exploded view of any console type.
    Uses the model's bounding box to create explosion offsets.

    Args:
        model: The original 3D model
        console_type: Type of console ('normal', 'vertical', 'bench', 'pedalboard')
        parameters: Console parameters dictionary
        explosion_offset: Base offset for explosion (mm)

    Returns:
        Compound: Exploded view model
    """
    if console_type == "normal":
        return generate_exploded_console_normal(parameters, explosion_offset)
    elif console_type == "vertical":
        return generate_exploded_console_vertical(parameters, explosion_offset)
    elif console_type == "bench":
        return generate_exploded_console_bench(parameters, explosion_offset)
    elif console_type == "pedalboard":
        return generate_exploded_console_pedalboard(parameters, explosion_offset)
    else:
        return model  # Fallback


def generate_exploded_console_normal(parameters, explosion_offset=150):
    """
    Generate an exploded view of the normal console.
    Lateral parts explode horizontally, horizontal parts explode vertically.
    """
    p = DotDict(parameters)
    parts = []

    # Horizontal explosion offset for lateral parts
    h_offset = explosion_offset * 0.8

    # Base right table - explode RIGHT
    parts.append(create_board(
        max_width=p.base_depth_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g + h_offset, 0, 0),
        rotation=(0, 0, 0)
    ))

    # Base left table - explode LEFT
    parts.append(create_board(
        max_width=p.base_depth_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.organ_internal_width_g - 2*p.general_board_thickness_g - h_offset, 0, 0),
        rotation=(0, 0, 0)
    ))

    # Base back - stays in place
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 90)
    ))

    # Base front - explode FORWARD
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.base_depth_g - 100 + explosion_offset, 0),
        rotation=(0, 0, 90),
        rectangular_holes=[[
            p.organ_internal_width_g/2,
            p.volume_pedals_hole_start_height_g + (p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g) / 2,
            p.volume_pedals_number_g * (p.volume_pedals_width_g + p.volume_pedals_spacing_g) + p.volume_pedals_spacing_g,
            p.volume_pedals_height_g + 2 * p.volume_pedals_spacing_g
        ]]
    ))

    # Base horizontal - offset upward
    offset1 = explosion_offset
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_depth_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.general_board_thickness_g, p.base_height_g + offset1),
        rotation=(0, 90, 90)
    ))

    # Top section - offset more
    offset2 = explosion_offset * 2

    # Top lateral left - explode LEFT and UP
    parts.append(create_board(
        max_width=p.top_depth_g,
        max_height=p.top_height_g,
        min_width=p.top_notch_start_x_g,
        min_height=p.top_notch_start_y_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g + h_offset, 0, p.base_height_g + offset2),
        rotation=(0, 0, 0)
    ))

    # Top lateral right - explode RIGHT and UP
    parts.append(create_board(
        max_width=p.top_depth_g,
        max_height=p.top_height_g,
        min_width=p.top_notch_start_x_g,
        min_height=p.top_notch_start_y_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.organ_internal_width_g - 2*p.general_board_thickness_g - h_offset, 0, p.base_height_g + offset2),
        rotation=(0, 0, 0)
    ))

    # Top back - explode UP
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_height_g - 2 * p.general_board_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, p.base_height_g + p.general_board_thickness_g + offset2),
        rotation=(0, 0, 90)
    ))

    # Top front - explode UP and FORWARD
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_height_g - 2 * p.general_board_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.base_depth_g + explosion_offset * 0.5, p.base_height_g + p.general_board_thickness_g + offset2),
        rotation=(0, 0, 90)
    ))

    # Top lid - offset even more
    offset3 = explosion_offset * 3
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_depth_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, p.base_height_g + p.top_height_g - p.general_board_thickness_g + offset3),
        rotation=(0, 90, 90)
    ))

    # Volume pedals - offset forward
    pedal_y_offset = explosion_offset * 1.5
    for i in range(p.volume_pedals_number_g):
        pedal_x = (-p.general_board_thickness_g
                   - p.organ_internal_width_g / 2
                   + (p.volume_pedals_number_g * (p.volume_pedals_width_g + p.volume_pedals_spacing_g) + p.volume_pedals_spacing_g) / 2
                   - i * (p.volume_pedals_spacing_g + p.volume_pedals_width_g)
                   - p.volume_pedals_spacing_g)
        pedal_y = p.base_depth_g - p.base_front_distance_g + p.general_board_thickness_g + pedal_y_offset
        pedal_z = p.volume_pedals_hole_start_height_g + 2 * p.volume_pedals_spacing_g

        parts.append(create_board(
            max_width=p.volume_pedals_width_g,
            max_height=p.volume_pedals_height_g,
            board_thickness=p.general_board_thickness_g,
            position=(pedal_x, pedal_y, pedal_z),
            rotation=(0, -30, 90)
        ))

    return Compound(children=parts)


def generate_exploded_console_vertical(parameters, explosion_offset=150):
    """
    Generate an exploded view of the vertical console.
    """
    p = DotDict(parameters)
    parts = []

    h_offset = explosion_offset * 0.8  # Horizontal explosion
    v_offset = explosion_offset  # Vertical explosion

    # Cabinet Top - explode UP
    parts.append(create_board(
        max_width=p.base_depth_g + 2 * p.general_board_thickness_g + p.general_board_offset_g,
        max_height=p.organ_internal_width_g,
        board_thickness=p.general_board_thickness_g,
        position=(p.organ_internal_width_g / 2, 0, p.base_height_g + p.keyboard_height_g + p.note_stand_height_g + p.general_board_thickness_g + p.front_speaker_height_g + v_offset),
        rotation=(0, -90, 0)
    ))

    # Cabinet Upper Back Panel
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.keyboard_height_g + p.note_stand_height_g + p.general_board_thickness_g + p.front_speaker_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(p.organ_internal_width_g / 2, -explosion_offset * 0.5, p.base_height_g),
        rotation=(0, 0, 90)
    ))

    # Cabinet Lower Back Panel
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_height_g - p.general_board_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(p.organ_internal_width_g / 2, -explosion_offset * 0.5, 0),
        rotation=(0, 0, 90)
    ))

    # Cabinet Bottom Shelf - explode UP slightly
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_depth_g - p.base_front_distance_g + p.general_board_offset_g,
        board_thickness=p.general_board_thickness_g,
        position=(p.organ_internal_width_g / 2, p.general_board_thickness_g, p.volume_pedals_hole_start_height_g + v_offset * 0.3),
        rotation=(0, 90, 90)
    ))

    # Cabinet Speaker Shelf - explode UP
    parts.append(create_board(
        max_width=p.base_depth_g + p.general_board_thickness_g + p.general_board_offset_g,
        max_height=p.organ_internal_width_g,
        board_thickness=p.general_board_thickness_g,
        position=(p.organ_internal_width_g / 2, p.general_board_thickness_g, p.base_height_g + p.keyboard_height_g + p.note_stand_height_g + v_offset * 0.5),
        rotation=(0, -90, 0)
    ))

    # Left lateral - explode LEFT
    lateral_height = p.base_height_g + p.keyboard_height_g + p.note_stand_height_g + 2 * p.general_board_thickness_g + p.front_speaker_height_g - p.general_feet_thickness_g
    speaker_holes = [[p.side_speaker_width_g / 2 + p.general_board_offset_g, lateral_height / 2 + p.general_feet_thickness_g / 2, p.side_speaker_width_g, p.side_speaker_height_g]] if p.enable_lateral_speaker_holes_g else []

    parts.append(create_board(
        max_width=p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g,
        max_height=lateral_height,
        board_thickness=p.general_board_thickness_g,
        position=(p.organ_internal_width_g / 2 + p.general_board_thickness_g + h_offset, 0, p.general_feet_thickness_g),
        rotation=(0, 0, 0),
        rectangular_holes=speaker_holes
    ))

    # Right lateral - explode RIGHT
    parts.append(create_board(
        max_width=p.base_depth_g + 2 * p.general_board_thickness_g + 2 * p.general_board_offset_g,
        max_height=lateral_height,
        board_thickness=p.general_board_thickness_g,
        position=(-p.organ_internal_width_g / 2 - 2 * p.general_board_thickness_g - h_offset, 0, p.general_feet_thickness_g),
        rotation=(0, 0, 0),
        rectangular_holes=speaker_holes
    ))

    # Left knobs panel - explode LEFT and FORWARD
    left_panel_width = (p.organ_internal_width_g - p.keyboard_width_g - 2 * p.general_board_thickness_g) / 2
    parts.append(create_board(
        max_width=left_panel_width,
        max_height=p.keyboard_height_g + p.note_stand_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(p.organ_internal_width_g / 2 + h_offset * 0.5, p.base_depth_g + p.general_board_thickness_g + explosion_offset * 0.3, p.base_height_g),
        rotation=(0, 0, 90)
    ))

    # Right knobs panel - explode RIGHT and FORWARD
    parts.append(create_board(
        max_width=left_panel_width,
        max_height=p.keyboard_height_g + p.note_stand_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.organ_internal_width_g / 2 - h_offset * 0.5, p.base_depth_g + 2 * p.general_board_thickness_g + explosion_offset * 0.3, p.base_height_g),
        rotation=(0, 0, -90)
    ))

    # Main keyboard shelf - explode UP
    parts.append(create_board(
        max_width=p.keyboard_width_g,
        max_height=p.base_depth_g + p.base_front_distance_g,
        board_thickness=p.general_board_thickness_g,
        position=(p.keyboard_width_g / 2, 0, p.base_height_g + v_offset * 0.4),
        rotation=(0, 90, 90)
    ))

    return Compound(children=parts)


def generate_exploded_console_bench(parameters, explosion_offset=150):
    """
    Generate an exploded view of the bench console.
    """
    p = DotDict(parameters)
    parts = []

    h_offset = explosion_offset * 0.8
    v_offset = explosion_offset

    # Bench top - explode UP
    parts.append(create_board(
        max_width=p.bench_depth_g,
        max_height=p.bench_length_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.bench_length_g / 2, 0, p.bench_height_g + v_offset),
        rotation=(0, 90, 0)
    ))

    # Bench left panel - explode LEFT
    parts.append(create_board(
        max_width=p.bench_depth_g - 2 * p.general_board_offset_g,
        max_height=p.bench_height_g - p.general_board_thickness_g - p.general_feet_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.bench_length_g / 2 + p.general_board_offset_g - h_offset, p.general_board_offset_g, p.general_feet_thickness_g),
        rotation=(0, 0, 0)
    ))

    # Bench right panel - explode RIGHT
    parts.append(create_board(
        max_width=p.bench_depth_g - 2 * p.general_board_offset_g,
        max_height=p.bench_height_g - p.general_board_thickness_g - p.general_feet_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(p.bench_length_g / 2 - p.general_board_offset_g - p.general_board_thickness_g + h_offset, p.general_board_offset_g, p.general_feet_thickness_g),
        rotation=(0, 0, 0)
    ))

    # Bench left foot - explode LEFT and DOWN
    parts.append(create_board(
        max_width=p.bench_depth_g,
        max_height=p.general_feet_thickness_g,
        board_thickness=p.general_feet_thickness_g,
        position=(-p.general_feet_thickness_g / 2 - p.bench_length_g / 2 + p.general_board_offset_g + p.general_board_thickness_g / 2 - h_offset, p.general_board_offset_g, -v_offset * 0.3),
        rotation=(0, 0, 0)
    ))

    # Bench right foot - explode RIGHT and DOWN
    parts.append(create_board(
        max_width=p.bench_depth_g,
        max_height=p.general_feet_thickness_g,
        board_thickness=p.general_feet_thickness_g,
        position=(-p.general_feet_thickness_g / 2 + p.bench_length_g / 2 - p.general_board_offset_g - p.general_board_thickness_g / 2 + h_offset, p.general_board_offset_g, -v_offset * 0.3),
        rotation=(0, 0, 0)
    ))

    # Bench shelf back panel - stays mostly in place
    parts.append(create_board(
        max_width=p.bench_shelf_height_g,
        max_height=p.bench_length_g - 2 * p.general_board_thickness_g - 2 * p.general_board_offset_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.bench_length_g / 2 + p.general_board_offset_g + p.general_board_thickness_g, 2 * p.general_board_offset_g - explosion_offset * 0.3, p.bench_height_g - p.bench_shelf_height_g - p.general_board_thickness_g),
        rotation=(90, 0, 90)
    ))

    # Bench shelf - explode UP slightly
    parts.append(create_board(
        max_width=p.bench_depth_g - 2 * p.general_board_offset_g,
        max_height=p.bench_length_g - 2 * p.general_board_thickness_g - 2 * p.general_board_offset_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.bench_length_g / 2 + p.general_board_offset_g + p.general_board_thickness_g, p.general_board_offset_g, p.bench_height_g - p.bench_shelf_height_g - p.general_board_thickness_g + v_offset * 0.3),
        rotation=(0, 90, 0)
    ))

    # Bench holder - explode FORWARD
    parts.append(create_board(
        max_width=p.bench_length_g - 2 * p.general_board_thickness_g - 2 * p.general_board_offset_g,
        max_height=p.bench_shelf_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(p.bench_length_g / 2 - p.general_board_offset_g - p.general_board_thickness_g, -p.general_board_thickness_g / 2 + p.bench_depth_g / 2 + explosion_offset * 0.5, p.bench_height_g / 2 - p.bench_shelf_height_g / 2),
        rotation=(0, 0, 90)
    ))

    return Compound(children=parts)


def generate_exploded_console_pedalboard(parameters, explosion_offset=100):
    """
    Generate an exploded view of the pedalboard.
    Pedals are spread out vertically.
    """
    p = DotDict(parameters)
    parts = []

    # Generate the pattern
    pattern = generate_ago_pattern_for_exploded(p.number_of_notes_g).replace(" ", "")

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
    start_x = total_width / 2

    current_x = start_x
    pedal_index = 0

    for char in pattern:
        if char == 's':
            # Short pedal - alternate vertical offset for explosion effect
            v_offset = (pedal_index % 3) * explosion_offset * 0.3
            parts.append(create_board(
                max_width=p.short_pedal_width_g,
                max_height=p.short_pedal_length_g,
                board_thickness=p.pedal_thickness_g,
                position=(current_x - p.short_pedal_width_g / 2, 0, p.pedal_height_g + v_offset),
                rotation=(90, 0, 0)
            ))
            current_x -= p.short_pedal_width_g + p.pedal_spacing_g
            pedal_index += 1
        elif char == 't':
            # Tall pedal - different vertical offset
            v_offset = ((pedal_index % 3) + 1) * explosion_offset * 0.25
            parts.append(create_board(
                max_width=p.tall_pedal_width_g,
                max_height=p.tall_pedal_length_g,
                board_thickness=p.pedal_thickness_g,
                position=(current_x - p.tall_pedal_width_g / 2, 0, p.pedal_height_g + p.pedal_thickness_g + v_offset),
                rotation=(90, 0, 0)
            ))
            current_x -= p.tall_pedal_width_g + p.pedal_spacing_g
            pedal_index += 1
        elif char == 'b':
            current_x -= p.short_pedal_width_g + p.pedal_spacing_g

    return Compound(children=parts)


def generate_ago_pattern_for_exploded(number_of_notes):
    """Generate AGO pattern for exploded view."""
    octave_pattern = "ststsb stststs b"
    notes_per_octave = 12
    complete_octaves = number_of_notes // notes_per_octave
    remaining_notes = number_of_notes % notes_per_octave

    pattern_parts = []
    for _ in range(complete_octaves):
        pattern_parts.append(octave_pattern)

    if remaining_notes > 0:
        partial_pattern = ""
        note_count = 0
        for char in octave_pattern:
            if char != ' ':
                partial_pattern += char
                if char in ['s', 't']:
                    note_count += 1
                    if note_count >= remaining_notes:
                        break
            elif partial_pattern:
                partial_pattern += char
        pattern_parts.append(partial_pattern.strip())

    return " ".join(pattern_parts)


def create_single_view_with_dimensions(model, view_name, draft):
    """
    Create edges and dimensions for a single view.

    Returns:
        tuple: (visible_edges, hidden_edges, dimension_objects, bbox_2d)
    """
    visible, hidden, bbox_2d = generate_view_projection(model, view_name)
    dimensions = create_dimensions_for_view(bbox_2d, view_name, draft)
    return visible, hidden, dimensions, bbox_2d


def create_a3_technical_drawing(model, parameters, console_type="normal", title="Organ Console"):
    """
    Create a complete A3 technical drawing with multiple views using build123d ExportSVG.

    Layout (3x3 grid):
    +------------------+------------------+------------------+
    |    FRONT VIEW    |    TOP VIEW      |   RIGHT VIEW     |
    +------------------+------------------+------------------+
    |    BACK VIEW     |   BOTTOM VIEW    |   LEFT VIEW      |
    +------------------+------------------+------------------+
    |       PERSPECTIVE VIEW              |  EXPLODED VIEW   |
    +-------------------------------------+------------------+

    Args:
        model: The 3D Compound model
        parameters: Console parameters dictionary
        console_type: Type of console for title
        title: Drawing title

    Returns:
        str: Complete SVG content
    """
    # A3 dimensions in mm
    a3_width = 420
    a3_height = 297
    margin = 15
    title_height = 30

    # Calculate view cell dimensions
    content_width = a3_width - 2 * margin
    content_height = a3_height - 2 * margin - title_height

    cell_width = content_width / 3
    cell_height = content_height / 3

    # Generate exploded model for exploded view
    try:
        exploded_model = generate_exploded_view(model, console_type, parameters, explosion_offset=300)
    except Exception:
        exploded_model = model  # Fallback to regular model on error

    # Define views and their grid positions
    views = [
        {"name": "front", "label": "FRONT VIEW", "col": 0, "row": 0, "model": model},
        {"name": "top", "label": "TOP VIEW", "col": 1, "row": 0, "model": model},
        {"name": "right", "label": "RIGHT VIEW", "col": 2, "row": 0, "model": model},
        {"name": "back", "label": "BACK VIEW", "col": 0, "row": 1, "model": model},
        {"name": "bottom", "label": "BOTTOM VIEW", "col": 1, "row": 1, "model": model},
        {"name": "left", "label": "LEFT VIEW", "col": 2, "row": 1, "model": model},
        {"name": "perspective", "label": "PERSPECTIVE", "col": 0, "row": 2, "colspan": 2, "model": model},
        {"name": "perspective", "label": "EXPLODED", "col": 2, "row": 2, "model": exploded_model},
    ]

    # Get model bounding box for overall dimensions
    bbox = model.bounding_box()
    model_width = abs(bbox.max.X - bbox.min.X)
    model_depth = abs(bbox.max.Y - bbox.min.Y)
    model_height = abs(bbox.max.Z - bbox.min.Z)

    # Calculate scale to fit largest view in cell
    max_model_dim = max(model_width, model_depth, model_height)
    base_scale = (min(cell_width, cell_height) * 0.6) / max_model_dim

    # Draft settings scaled appropriately
    draft = Draft(
        font_size=max(8, 40 / base_scale),
        decimal_precision=0,
        display_units=False,
        arrow_length=max(5, 20 / base_scale),
        line_width=max(0.3, 1.5 / base_scale)
    )

    # Start building the SVG manually with proper A3 layout
    svg_parts = []
    svg_parts.append(f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{a3_width}mm" height="{a3_height}mm"
     viewBox="0 0 {a3_width} {a3_height}">

<!-- Background -->
<rect width="100%" height="100%" fill="white"/>

<!-- Border -->
<rect x="{margin}" y="{margin}"
      width="{content_width}" height="{a3_height - 2*margin}"
      fill="none" stroke="black" stroke-width="0.5"/>

<!-- Title block -->
<rect x="{margin}" y="{a3_height - margin - title_height}"
      width="{content_width}" height="{title_height}"
      fill="none" stroke="black" stroke-width="0.5"/>
<text x="{a3_width/2}" y="{a3_height - margin - title_height + 12}"
      font-family="Arial" font-size="10" text-anchor="middle" font-weight="bold">
    {title} - {console_type.upper()} CONSOLE
</text>
<text x="{a3_width/2}" y="{a3_height - margin - title_height + 24}"
      font-family="Arial" font-size="7" text-anchor="middle" fill="#333">
    Overall: {model_width:.0f}mm W x {model_depth:.0f}mm D x {model_height:.0f}mm H
</text>

<!-- Grid lines -->
''')

    # Add grid lines
    for i in range(1, 3):
        x = margin + i * cell_width
        svg_parts.append(f'<line x1="{x}" y1="{margin}" x2="{x}" y2="{margin + content_height}" stroke="#cccccc" stroke-width="0.25"/>\n')
    for i in range(1, 3):
        y = margin + i * cell_height
        svg_parts.append(f'<line x1="{margin}" y1="{y}" x2="{margin + content_width}" y2="{y}" stroke="#cccccc" stroke-width="0.25"/>\n')

    # Generate each view
    for view in views:
        col = view["col"]
        row = view["row"]
        colspan = view.get("colspan", 1)

        # Calculate cell position and size
        cell_x = margin + col * cell_width
        cell_y = margin + row * cell_height
        cell_w = cell_width * colspan
        cell_h = cell_height

        # Add view label
        svg_parts.append(f'''
<text x="{cell_x + cell_w/2}" y="{cell_y + 10}"
      font-family="Arial" font-size="6" text-anchor="middle" fill="#666666" font-weight="bold">
    {view["label"]}
</text>
''')

        try:
            view_model = view["model"]
            visible, hidden, bbox_2d = generate_view_projection(view_model, view["name"])

            if (visible or hidden) and bbox_2d:
                # Calculate scale for this view
                view_width = bbox_2d.size.X
                view_height = bbox_2d.size.Y

                # Leave space for label and dimensions
                available_w = cell_w - 30
                available_h = cell_h - 35

                scale_x = available_w / max(view_width, 1)
                scale_y = available_h / max(view_height, 1)
                scale = min(scale_x, scale_y) * 0.75

                # Center of view area
                cx = cell_x + cell_w / 2
                cy = cell_y + cell_h / 2 + 5

                # Offset to center the geometry
                offset_x = -(bbox_2d.min.X + bbox_2d.max.X) / 2
                offset_y = -(bbox_2d.min.Y + bbox_2d.max.Y) / 2

                # Create group with transform
                svg_parts.append(f'<g transform="translate({cx}, {cy}) scale({scale}, {-scale})">\n')

                # Draw hidden edges first (dashed)
                for edge in hidden:
                    path_data = edge_to_svg_path(edge, offset_x, offset_y)
                    if path_data:
                        svg_parts.append(f'<path d="{path_data}" fill="none" stroke="#999999" stroke-width="{0.3/scale}" stroke-dasharray="{3/scale},{1.5/scale}"/>\n')

                # Draw visible edges (solid brown)
                for edge in visible:
                    path_data = edge_to_svg_path(edge, offset_x, offset_y)
                    if path_data:
                        svg_parts.append(f'<path d="{path_data}" fill="none" stroke="#8B4513" stroke-width="{0.5/scale}"/>\n')

                # Add dimension lines for main views (not perspective/exploded)
                if view["name"] in ["front", "top", "right", "left", "back", "bottom"]:
                    dim_offset = 15 / scale  # Reduced offset to keep dimensions closer

                    # Width dimension - now at TOP of drawing
                    w_start_x = bbox_2d.min.X + offset_x
                    w_end_x = bbox_2d.max.X + offset_x
                    w_y = bbox_2d.max.Y + offset_y + dim_offset  # Changed to max.Y (top)

                    # Height dimension on left
                    h_x = bbox_2d.min.X + offset_x - dim_offset
                    h_start_y = bbox_2d.min.Y + offset_y
                    h_end_y = bbox_2d.max.Y + offset_y

                    width_val = bbox_2d.size.X
                    height_val = bbox_2d.size.Y

                    # Text positioning - always above/outside the dimension line
                    w_text_y_offset = 4/scale   # Above the line (in flipped coords this appears above)
                    h_text_x_offset = -4/scale  # Left of the line

                    # Draw width dimension line (at top)
                    svg_parts.append(f'''
  <!-- Width dimension -->
  <line x1="{w_start_x}" y1="{bbox_2d.max.Y + offset_y}" x2="{w_start_x}" y2="{w_y + 2/scale}" stroke="#000" stroke-width="{0.15/scale}"/>
  <line x1="{w_end_x}" y1="{bbox_2d.max.Y + offset_y}" x2="{w_end_x}" y2="{w_y + 2/scale}" stroke="#000" stroke-width="{0.15/scale}"/>
  <line x1="{w_start_x}" y1="{w_y}" x2="{w_end_x}" y2="{w_y}" stroke="#000" stroke-width="{0.15/scale}"/>
  <polygon points="{w_start_x},{w_y} {w_start_x + 2/scale},{w_y + 0.75/scale} {w_start_x + 2/scale},{w_y - 0.75/scale}" fill="#000"/>
  <polygon points="{w_end_x},{w_y} {w_end_x - 2/scale},{w_y + 0.75/scale} {w_end_x - 2/scale},{w_y - 0.75/scale}" fill="#000"/>
  <text x="{(w_start_x + w_end_x)/2}" y="{w_y + w_text_y_offset}" font-family="Arial" font-size="{3/scale}" text-anchor="middle" transform="scale(1,-1) translate(0,{-2*w_y})">{width_val:.0f}mm</text>
''')

                    # Draw height dimension line
                    svg_parts.append(f'''
  <!-- Height dimension -->
  <line x1="{bbox_2d.min.X + offset_x}" y1="{h_start_y}" x2="{h_x - 2/scale}" y2="{h_start_y}" stroke="#000" stroke-width="{0.15/scale}"/>
  <line x1="{bbox_2d.min.X + offset_x}" y1="{h_end_y}" x2="{h_x - 2/scale}" y2="{h_end_y}" stroke="#000" stroke-width="{0.15/scale}"/>
  <line x1="{h_x}" y1="{h_start_y}" x2="{h_x}" y2="{h_end_y}" stroke="#000" stroke-width="{0.15/scale}"/>
  <polygon points="{h_x},{h_start_y} {h_x + 0.75/scale},{h_start_y + 2/scale} {h_x - 0.75/scale},{h_start_y + 2/scale}" fill="#000"/>
  <polygon points="{h_x},{h_end_y} {h_x + 0.75/scale},{h_end_y - 2/scale} {h_x - 0.75/scale},{h_end_y - 2/scale}" fill="#000"/>
  <text x="{h_x + h_text_x_offset}" y="{(h_start_y + h_end_y)/2}" font-family="Arial" font-size="{3/scale}" text-anchor="middle" transform="rotate(-90, {h_x + h_text_x_offset}, {(h_start_y + h_end_y)/2}) scale(1,-1) translate(0,{-2*(h_start_y + h_end_y)/2})">{height_val:.0f}mm</text>
''')

                svg_parts.append('</g>\n')

        except Exception as e:
            svg_parts.append(f'''
<text x="{cell_x + cell_w/2}" y="{cell_y + cell_h/2}"
      font-family="Arial" font-size="5" text-anchor="middle" fill="red">
    Error: {str(e)[:40]}
</text>
''')

    # Close SVG
    svg_parts.append('</svg>')

    return ''.join(svg_parts)


def edge_to_svg_path(edge, offset_x=0, offset_y=0):
    """
    Convert a build123d Edge to an SVG path string.
    """
    try:
        points = []
        num_samples = 21 if str(edge.geom_type) != "GeomType.LINE" else 2

        for i in range(num_samples):
            t = i / (num_samples - 1) if num_samples > 1 else 0
            try:
                pt = edge.position_at(t)
                points.append((pt.X + offset_x, pt.Y + offset_y))
            except:
                pass

        if len(points) < 2:
            return None

        path_parts = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
        for pt in points[1:]:
            path_parts.append(f"L {pt[0]:.2f} {pt[1]:.2f}")

        return " ".join(path_parts)

    except Exception:
        return None


def save_technical_drawing(svg_content, filepath):
    """Save the SVG content to a file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)


def generate_technical_drawing_cached(model, parameters, console_type="normal"):
    """
    Generate technical drawing and save to temp file.
    """
    svg_content = create_a3_technical_drawing(model, parameters, console_type)
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, f"organ_technical_drawing_{console_type}.svg")
    save_technical_drawing(svg_content, filepath)
    return filepath, svg_content


# Test execution
if __name__ == "__main__":
    from console_normal import generate_console, get_default_parameters

    params = get_default_parameters()
    model = generate_console(params)

    svg_content = create_a3_technical_drawing(model, params, "normal", "Test Drawing")

    with open("test_technical_drawing.svg", "w") as f:
        f.write(svg_content)

    print("Technical drawing saved to test_technical_drawing.svg")
