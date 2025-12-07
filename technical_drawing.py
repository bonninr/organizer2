"""
Technical Drawing Generator - A3 Plan with Orthographic Views

This module generates A3 technical drawings with:
- 6 orthographic views (front, back, top, bottom, left, right)
- Perspective/isometric view
- Exploded view
- Dimension annotations

Uses build123d's project_to_viewport() and ExportSVG for rendering.
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
        tuple: (visible_edges, hidden_edges)
    """
    # Calculate model center for look_at
    bbox = model.bounding_box()
    center = (
        (bbox.min.X + bbox.max.X) / 2,
        (bbox.min.Y + bbox.max.Y) / 2,
        (bbox.min.Z + bbox.max.Z) / 2
    )

    # Define viewport origins and up vectors for each view
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

    return visible, hidden


def create_single_view_svg(model, view_name, width=200, height=150):
    """
    Create an SVG for a single view of the model.

    Args:
        model: The 3D Compound model
        view_name: View name for projection
        width: Target width in mm
        height: Target height in mm

    Returns:
        str: SVG content as string
    """
    visible, hidden = generate_view_projection(model, view_name)

    # Combine all edges to calculate bounding box and scale
    all_edges = visible + hidden
    if not all_edges:
        return f'<svg width="{width}" height="{height}"><text x="10" y="20">No edges</text></svg>'

    compound = Compound(children=all_edges)
    bbox = compound.bounding_box()

    # Calculate scale to fit within the target dimensions with margin
    margin_factor = 0.85
    scale_x = (width * margin_factor) / max(bbox.size.X, 1)
    scale_y = (height * margin_factor) / max(bbox.size.Y, 1)
    scale = min(scale_x, scale_y)

    # Create SVG exporter
    exporter = ExportSVG(scale=scale, margin=10)

    # Add layers for visible and hidden edges
    exporter.add_layer("Visible", line_color=COLORS["visible"], line_weight=0.5)
    exporter.add_layer("Hidden", line_color=COLORS["hidden"], line_weight=0.25, line_type=LineType.ISO_DASH)

    # Add shapes to layers
    if visible:
        exporter.add_shape(visible, layer="Visible")
    if hidden:
        exporter.add_shape(hidden, layer="Hidden")

    # Write to BytesIO and return as string
    svg_buffer = BytesIO()
    exporter.write(svg_buffer)
    svg_buffer.seek(0)
    return svg_buffer.read().decode('utf-8')


def generate_exploded_console_normal(parameters, explosion_offset=150):
    """
    Generate an exploded view of the normal console.
    Parts are separated vertically to show assembly.

    Args:
        parameters: Console parameters dictionary
        explosion_offset: Distance to separate parts (mm)

    Returns:
        Compound: Exploded view model
    """
    p = DotDict(parameters)
    parts = []

    # Base section - stays in original position
    # Base right table
    parts.append(create_board(
        max_width=p.base_depth_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 0)
    ))

    # Base left table
    parts.append(create_board(
        max_width=p.base_depth_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.organ_internal_width_g - 2*p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 0)
    ))

    # Base back
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 90)
    ))

    # Base front
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.base_depth_g-100, 0),
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

    # Top lateral left
    parts.append(create_board(
        max_width=p.top_depth_g,
        max_height=p.top_height_g,
        min_width=p.top_notch_start_x_g,
        min_height=p.top_notch_start_y_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, p.base_height_g + offset2),
        rotation=(0, 0, 0)
    ))

    # Top lateral right
    parts.append(create_board(
        max_width=p.top_depth_g,
        max_height=p.top_height_g,
        min_width=p.top_notch_start_x_g,
        min_height=p.top_notch_start_y_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.organ_internal_width_g - 2*p.general_board_thickness_g, 0, p.base_height_g + offset2),
        rotation=(0, 0, 0)
    ))

    # Top back
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_height_g - 2 * p.general_board_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, p.base_height_g + p.general_board_thickness_g + offset2),
        rotation=(0, 0, 90)
    ))

    # Top front
    parts.append(create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_height_g - 2 * p.general_board_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.base_depth_g, p.base_height_g + p.general_board_thickness_g + offset2),
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
    pedal_y_offset = explosion_offset
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


def create_a3_technical_drawing(model, parameters, console_type="normal", title="Organ Console"):
    """
    Create a complete A3 technical drawing with multiple views.

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
    title_height = 25

    # Calculate view cell dimensions
    content_width = a3_width - 2 * margin
    content_height = a3_height - 2 * margin - title_height

    cell_width = content_width / 3
    cell_height = content_height / 3

    # Generate exploded model for exploded view
    try:
        if console_type == "normal":
            exploded_model = generate_exploded_console_normal(parameters)
        else:
            exploded_model = model  # Fallback to regular model for other console types
    except Exception:
        exploded_model = model  # Fallback on any error

    # Define views and their positions in the grid
    views = [
        # Row 1
        {"name": "front", "label": "FRONT VIEW", "col": 0, "row": 0, "model": model},
        {"name": "top", "label": "TOP VIEW", "col": 1, "row": 0, "model": model},
        {"name": "right", "label": "RIGHT VIEW", "col": 2, "row": 0, "model": model},
        # Row 2
        {"name": "back", "label": "BACK VIEW", "col": 0, "row": 1, "model": model},
        {"name": "bottom", "label": "BOTTOM VIEW", "col": 1, "row": 1, "model": model},
        {"name": "left", "label": "LEFT VIEW", "col": 2, "row": 1, "model": model},
        # Row 3
        {"name": "perspective", "label": "PERSPECTIVE VIEW", "col": 0, "row": 2, "colspan": 2, "model": model},
        {"name": "perspective", "label": "EXPLODED VIEW", "col": 2, "row": 2, "model": exploded_model},
    ]

    # Start building the SVG
    svg_parts = []
    svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg"
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
    <text x="{a3_width/2}" y="{a3_height - margin - title_height/2 + 5}"
          font-family="Arial" font-size="12" text-anchor="middle" font-weight="bold">
        {title} - {console_type.upper()} CONSOLE
    </text>

    <!-- Grid lines -->
    ''')

    # Add grid lines
    for i in range(1, 3):
        # Vertical lines
        x = margin + i * cell_width
        svg_parts.append(f'<line x1="{x}" y1="{margin}" x2="{x}" y2="{margin + content_height}" stroke="#cccccc" stroke-width="0.25"/>')
    for i in range(1, 3):
        # Horizontal lines
        y = margin + i * cell_height
        svg_parts.append(f'<line x1="{margin}" y1="{y}" x2="{margin + content_width}" y2="{y}" stroke="#cccccc" stroke-width="0.25"/>')

    # Generate each view
    for view in views:
        col = view["col"]
        row = view["row"]
        colspan = view.get("colspan", 1)

        # Calculate position
        x = margin + col * cell_width
        y = margin + row * cell_height
        w = cell_width * colspan
        h = cell_height

        # Add view label
        svg_parts.append(f'''
    <text x="{x + w/2}" y="{y + 12}"
          font-family="Arial" font-size="8" text-anchor="middle" fill="#666666">
        {view["label"]}
    </text>''')

        # Generate the view SVG
        try:
            view_model = view["model"]
            visible, hidden = generate_view_projection(view_model, view["name"])

            if visible or hidden:
                all_edges = visible + hidden
                compound = Compound(children=all_edges)
                bbox = compound.bounding_box()

                # Calculate scale to fit in cell (with padding for label)
                view_height = h - 20  # Leave space for label
                view_width = w - 10

                scale_x = view_width / max(bbox.size.X, 1)
                scale_y = view_height / max(bbox.size.Y, 1)
                scale = min(scale_x, scale_y) * 0.75

                # Calculate center offset
                cx = x + w / 2
                cy = y + h / 2 + 5  # Offset down for label

                # Add a group for this view with translation
                svg_parts.append(f'<g transform="translate({cx}, {cy}) scale({scale}, -{scale})">')

                # Calculate offset to center the geometry
                offset_x = -(bbox.min.X + bbox.max.X) / 2
                offset_y = -(bbox.min.Y + bbox.max.Y) / 2

                # Draw hidden edges first (behind)
                for edge in hidden:
                    try:
                        path_data = edge_to_svg_path(edge, offset_x, offset_y)
                        if path_data:
                            svg_parts.append(f'<path d="{path_data}" fill="none" stroke="#999999" stroke-width="{0.25/scale}" stroke-dasharray="{2/scale},{1/scale}"/>')
                    except:
                        pass

                # Draw visible edges
                for edge in visible:
                    try:
                        path_data = edge_to_svg_path(edge, offset_x, offset_y)
                        if path_data:
                            svg_parts.append(f'<path d="{path_data}" fill="none" stroke="#8B4513" stroke-width="{0.5/scale}"/>')
                    except:
                        pass

                svg_parts.append('</g>')

        except Exception as e:
            # Add error text if view generation fails
            svg_parts.append(f'''
    <text x="{x + w/2}" y="{y + h/2}"
          font-family="Arial" font-size="6" text-anchor="middle" fill="red">
        Error: {str(e)[:30]}
    </text>''')

    # Add dimensions info using the model's bounding box (works for all console types)
    bbox = model.bounding_box()
    width_mm = abs(bbox.max.X - bbox.min.X)
    depth_mm = abs(bbox.max.Y - bbox.min.Y)
    height_mm = abs(bbox.max.Z - bbox.min.Z)
    dim_text = f"Overall: {width_mm:.0f}mm W x {depth_mm:.0f}mm D x {height_mm:.0f}mm H"
    svg_parts.append(f'''
    <text x="{margin + 5}" y="{a3_height - margin - 5}"
          font-family="Arial" font-size="6" fill="#333333">
        {dim_text}
    </text>''')

    # Close SVG
    svg_parts.append('</svg>')

    return '\n'.join(svg_parts)


def edge_to_svg_path(edge, offset_x=0, offset_y=0):
    """
    Convert a build123d Edge to an SVG path string.

    Args:
        edge: A build123d Edge object
        offset_x: X offset to apply
        offset_y: Y offset to apply

    Returns:
        str: SVG path data string
    """
    try:
        # Sample points along the edge for all edge types
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

        # Build path from points
        path_parts = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
        for pt in points[1:]:
            path_parts.append(f"L {pt[0]:.2f} {pt[1]:.2f}")

        return " ".join(path_parts)

    except Exception as e:
        return None


def save_technical_drawing(svg_content, filepath):
    """
    Save the SVG content to a file.

    Args:
        svg_content: SVG string content
        filepath: Output file path
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)


def generate_technical_drawing_cached(model, parameters, console_type="normal"):
    """
    Generate technical drawing and save to temp file.
    Returns the file path.

    Args:
        model: The 3D model
        parameters: Console parameters
        console_type: Type of console

    Returns:
        str: Path to the generated SVG file
    """
    svg_content = create_a3_technical_drawing(model, parameters, console_type)

    # Save to temp file
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

    # Save test output
    with open("test_technical_drawing.svg", "w") as f:
        f.write(svg_content)

    print("Technical drawing saved to test_technical_drawing.svg")
