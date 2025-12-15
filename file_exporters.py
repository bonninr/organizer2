"""
File Exporters Module - build123d Version

This module handles all file generation and export operations for the organ console project.
Supports GLTF, STL, STEP, CSV, and DXF export formats using build123d.

Usage:
    from file_exporters import generate_temp_file, generate_cutfile_csv, generate_dxf_with_annotations

    # Generate model and export
    from console_bench import generate_console, generate_board_list, get_default_parameters

    params = get_default_parameters()
    model = generate_console(params)

    # Export to different formats
    gltf_file = generate_temp_file(model, "gltf", "medium")
    step_file = generate_temp_file(model, "step", "fine")

    # Generate cutting list
    board_list = generate_board_list(params)
    csv_file = generate_cutfile_csv(board_list, "cutting_list.csv")
"""

import os
import tempfile
import csv
import json
import base64
from enum import Enum


class Tessellation(Enum):
    """Tessellation quality levels for mesh export"""
    COARSE = 0.5
    MEDIUM = 0.1
    FINE = 0.01


def _collect_part_labels(model):
    """
    Collect labels from all parts in the model tree using PreOrderIter.

    Args:
        model: build123d Shape (Compound or Part)

    Returns:
        list: List of labels for parts that have meshes (non-Compound or leaf nodes)
    """
    from anytree import PreOrderIter
    from build123d import Compound

    labels = []
    for node in PreOrderIter(model):
        # Skip compound nodes that are just containers (have children)
        if isinstance(node, Compound) and node.children:
            continue
        # Include nodes that will become meshes
        if hasattr(node, 'wrapped') and node.wrapped is not None:
            labels.append(node.label or '')
    return labels


def _postprocess_gltf_with_labels(gltf_path, labels):
    """
    Post-process a GLTF file to add mesh names from part labels.

    The OpenCASCADE GLTF writer doesn't preserve labels as mesh names,
    so we modify the GLTF JSON to add them after export.

    Three.js GLTFLoader uses the node name (not mesh name) for Object3D.name,
    so we update both mesh names and node names for nodes that reference
    labeled meshes.

    Args:
        gltf_path: Path to the GLTF file
        labels: List of labels in the same order as meshes
    """
    with open(gltf_path, 'r') as f:
        gltf = json.load(f)

    # Update mesh names with labels
    meshes = gltf.get('meshes', [])
    for i, mesh in enumerate(meshes):
        if i < len(labels) and labels[i]:
            mesh['name'] = labels[i]

    # Also update node names for nodes that reference labeled meshes
    # This is needed because Three.js GLTFLoader uses node names for Object3D.name
    nodes = gltf.get('nodes', [])
    for node in nodes:
        mesh_idx = node.get('mesh')
        if mesh_idx is not None and mesh_idx < len(labels) and labels[mesh_idx]:
            node['name'] = labels[mesh_idx]

    # Write back the modified GLTF
    with open(gltf_path, 'w') as f:
        json.dump(gltf, f)


def generate_temp_file(model, file_format, quality="medium"):
    """
    Generates a temporary file with the specified format using build123d.

    Args:
        model: build123d Compound or Part object
        file_format: "gltf", "stl", or "step"
        quality: "coarse", "medium", or "fine" (used for meshing quality)

    Returns:
        str: Path to the generated temporary file
    """
    from build123d import export_gltf, export_stl, export_step

    tolerance = getattr(Tessellation, quality.upper()).value

    if file_format.lower() == "gltf":
        file_suffix = ".gltf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmpfile:
            try:
                # Collect labels before export (they're preserved in the model tree)
                labels = _collect_part_labels(model)

                # Export using build123d's export_gltf function
                export_gltf(model, tmpfile.name, linear_deflection=tolerance, angular_deflection=0.1)

                # Post-process to add mesh names from labels
                _postprocess_gltf_with_labels(tmpfile.name, labels)

                return tmpfile.name
            except Exception as e:
                # Fallback to STL if GLTF fails
                try:
                    import streamlit as st
                    st.warning(f"GLTF export failed ({str(e)}), using STL format")
                except ImportError:
                    print(f"GLTF export failed ({str(e)}), using STL format")

                stl_tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".stl")
                export_stl(model, stl_tmpfile.name, tolerance=tolerance, angular_tolerance=0.1)
                return stl_tmpfile.name

    elif file_format.lower() == "stl":
        file_suffix = ".stl"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmpfile:
            export_stl(model, tmpfile.name, tolerance=tolerance, angular_tolerance=0.1)
            return tmpfile.name

    elif file_format.lower() == "step":
        file_suffix = ".step"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmpfile:
            export_step(model, tmpfile.name)
            return tmpfile.name

    else:
        raise ValueError(f"Unsupported file format: {file_format}")


def generate_cutfile_csv(board_list, output_path):
    """
    Generate a CSV file with the board cutting specifications.

    Args:
        board_list: List of board dictionaries from generate_board_list()
        output_path: Path where to save the CSV file

    Returns:
        str: Path to the generated CSV file
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Width (mm)', 'Height (mm)', 'Thickness (mm)', 'Description', 'Notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for board in board_list:
            writer.writerow({
                'Name': board['name'],
                'Width (mm)': board.get('width', board.get('height', 0)),  # Handle both width/height naming
                'Height (mm)': board.get('height', board.get('width', 0)),
                'Thickness (mm)': board['thickness'],
                'Description': board['description'],
                'Notes': board.get('notes', '')
            })

    return output_path


def generate_dxf_with_annotations(board_list, output_path):
    """
    Generate a DXF file with all board shapes and annotations at 1/10 scale.

    Args:
        board_list: List of board dictionaries from generate_board_list()
        output_path: Path where to save the DXF file

    Returns:
        str: Path to the generated DXF file
    """
    # Create a new drawing
    import ezdxf

    doc = ezdxf.new('R2010')  # AutoCAD 2010 format

    # Create a new modelspace
    msp = doc.modelspace()

    # Define layers for different components
    doc.layers.new(name='BOARDS', dxfattribs={'color': 1})  # Blue
    doc.layers.new(name='TEXT', dxfattribs={'color': 3})    # Green
    doc.layers.new(name='DIMENSIONS', dxfattribs={'color': 2})  # Yellow

    # Scale factor for 1/10 size
    scale = 0.1

    # Calculate total page dimensions needed
    total_height = 0
    max_board_width = 0

    # First pass: calculate total dimensions
    for board in board_list:
        width = board.get('width', board.get('height', 0))
        height = board.get('height', board.get('width', 0))
        scaled_width = width * scale
        scaled_height = height * scale
        max_board_width = max(max_board_width, scaled_width)
        total_height += scaled_height + 10  # Add spacing between boards

    # Add margins and text space
    text_space = 50  # Space for annotations
    margin = 20      # Page margins
    page_width = max_board_width + text_space + (2 * margin)
    page_height = total_height + (2 * margin)

    # Set up paper space and viewport for proper page layout
    try:
        # Create a layout (paper space)
        layout = doc.layouts.new('Layout1')

        # Set paper size (in mm) - use calculated dimensions or standard sizes
        if page_width <= 210 and page_height <= 297:  # A4 size
            layout.page_setup(size=(210, 297), margins=(10, 10, 10, 10))
        elif page_width <= 297 and page_height <= 420:  # A3 size
            layout.page_setup(size=(297, 420), margins=(15, 15, 15, 15))
        else:  # Custom size
            layout.page_setup(size=(page_width + 20, page_height + 20), margins=(10, 10, 10, 10))

        # Create viewport in paper space
        layout.add_viewport(
            center=(page_width/2, page_height/2),
            size=(page_width - 20, page_height - 20),
            view_center_point=(page_width/2, page_height/2),
            view_height=page_height - 20
        )
    except:
        # If paper space setup fails, continue with model space only
        pass

    current_y_offset = margin
    max_width = 0

    # Add each board to the DXF
    for idx, board in enumerate(board_list):
        # Extract board info and apply scale
        name = board['name']
        width = board.get('width', board.get('height', 0)) * scale
        height = board.get('height', board.get('width', 0)) * scale
        thickness = board['thickness']  # Keep original thickness for annotations

        # Track max width for layout purposes
        max_width = max(max_width, width)

        # Create 2D board shape
        min_width = board.get('min_width', 0) * scale
        min_height = board.get('min_height', 0) * scale
        rectangular_holes = board.get('rectangular_holes', [])
        circular_holes = board.get('circular_holes', [])

        # Create the basic outline (offset by margin)
        if min_width == 0:
            # Simple rectangle
            msp.add_lwpolyline([(margin, current_y_offset),
                              (margin + width, current_y_offset),
                              (margin + width, current_y_offset + height),
                              (margin, current_y_offset + height),
                              (margin, current_y_offset)],
                              dxfattribs={'layer': 'BOARDS'})
        else:
            # Slanted shape
            msp.add_lwpolyline([(margin, current_y_offset),
                              (margin + width, current_y_offset),
                              (margin + width, current_y_offset + min_height),
                              (margin + min_width, current_y_offset + height),
                              (margin, current_y_offset + height),
                              (margin, current_y_offset)],
                              dxfattribs={'layer': 'BOARDS'})

        # Add holes if any (scaled and offset by margin)
        for hole in rectangular_holes:
            x, y, hole_width, hole_height = hole
            x_scaled = x * scale
            y_scaled = y * scale
            hole_width_scaled = hole_width * scale
            hole_height_scaled = hole_height * scale

            x_bl = margin + x_scaled - hole_width_scaled/2
            y_bl = y_scaled - hole_height_scaled/2 + current_y_offset
            msp.add_lwpolyline([(x_bl, y_bl),
                              (x_bl + hole_width_scaled, y_bl),
                              (x_bl + hole_width_scaled, y_bl + hole_height_scaled),
                              (x_bl, y_bl + hole_height_scaled),
                              (x_bl, y_bl)],
                              dxfattribs={'layer': 'BOARDS'})

        for hole in circular_holes:
            x, y, diameter = hole
            x_scaled = x * scale
            y_scaled = y * scale
            diameter_scaled = diameter * scale
            msp.add_circle((margin + x_scaled, y_scaled + current_y_offset), diameter_scaled/2, dxfattribs={'layer': 'BOARDS'})

        # Add annotations with proper text positioning (ezdxf compatible)
        text_entity = msp.add_text(
            f"{name} ({width/scale:.0f}x{height/scale:.0f}x{thickness:.0f}mm)",
            dxfattribs={
                'layer': 'TEXT',
                'height': 2.0  # Scaled text height
            }
        )
        # Set text position using dxf attributes (offset by margin)
        text_entity.dxf.insert = (margin + width + 2, current_y_offset + height/2)
        text_entity.dxf.halign = 0  # Left alignment
        text_entity.dxf.valign = 1  # Middle alignment

        # Add dimensions (scaled and offset by margin)
        try:
            msp.add_linear_dim(
                base=(margin, current_y_offset),
                p1=(margin, current_y_offset),
                p2=(margin + width, current_y_offset),
                distance=5,  # Scaled dimension distance
                dxfattribs={'layer': 'DIMENSIONS'}
            )

            msp.add_linear_dim(
                base=(margin + width + 10, current_y_offset),
                p1=(margin + width, current_y_offset),
                p2=(margin + width, current_y_offset + height),
                distance=5,  # Scaled dimension distance
                dxfattribs={'layer': 'DIMENSIONS'}
            )
        except:
            # Skip dimensions if they fail
            pass

        # Update y offset for next board with some spacing (scaled)
        current_y_offset += height + 10  # Scaled spacing

    # Add page border and title block
    try:
        # Add page border
        border_margin = 5
        msp.add_lwpolyline([
            (border_margin, border_margin),
            (page_width - border_margin, border_margin),
            (page_width - border_margin, page_height - border_margin),
            (border_margin, page_height - border_margin),
            (border_margin, border_margin)
        ], dxfattribs={'layer': 'DIMENSIONS'})

        # Add title block
        title_text = msp.add_text(
            "ORGAN CONSOLE - CUTTING LIST (1:10 SCALE)",
            dxfattribs={
                'layer': 'TEXT',
                'height': 3.0
            }
        )
        title_text.dxf.insert = (border_margin + 5, page_height - border_margin - 8)
        title_text.dxf.halign = 0
        title_text.dxf.valign = 1

        # Add scale note
        scale_text = msp.add_text(
            f"Total boards: {len(board_list)} | Scale: 1:10 | Dimensions in mm (full size)",
            dxfattribs={
                'layer': 'TEXT',
                'height': 1.5
            }
        )
        scale_text.dxf.insert = (border_margin + 5, page_height - border_margin - 12)
        scale_text.dxf.halign = 0
        scale_text.dxf.valign = 1

    except:
        # Skip title block if it fails
        pass

    # Save the DXF file
    doc.saveas(output_path)
    return output_path


def generate_temp_csv(board_list):
    """
    Generates a temporary CSV file with the cutting specifications.

    Args:
        board_list: Board list from generate_board_list()

    Returns:
        str: Path to the generated temporary CSV file
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', newline='', encoding='utf-8') as tmpfile:
        generate_cutfile_csv(board_list, tmpfile.name)
        return tmpfile.name


def generate_temp_dxf(board_list):
    """
    Generates a temporary DXF file with 2D profiles.

    Args:
        board_list: Board list from generate_board_list()

    Returns:
        str: Path to the generated temporary DXF file, or None if failed
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmpfile:
        try:
            generate_dxf_with_annotations(board_list, tmpfile.name)
            return tmpfile.name
        except Exception as e:
            # Import streamlit here to avoid circular imports
            try:
                import streamlit as st
                st.error(f"Failed to generate DXF: {str(e)}")
            except ImportError:
                print(f"Failed to generate DXF: {str(e)}")
            return None
