import os
import tempfile
import json
import csv
import platform
from enum import Enum
from functools import cache

import cadquery as cq
import streamlit as st
import pyvista as pv
import numpy as np
from stpyvista import stpyvista as stv
from datetime import datetime


class DotDict:
    def __init__(self, nested_dict):
        for category, items in nested_dict.items():
            # For each dictionary in the list
            for item_dict in items:
                # There should be only one key-value pair in each dictionary
                for key, value in item_dict.items():
                    # Add to flattened dictionary
                    setattr(self, key, value)


class Tessellation(Enum):
    COARSE = 1e-3
    MEDIUM = 1e-4
    FINE = 1e-5


def create_board(max_width, max_height, board_thickness, position, rotation, min_width=0, min_height=0, rectangular_holes=[], circular_holes=[]):
    # Set the min height equal to max height if it's zero (for full rectangle)
    if min_height == 0:
        min_height = max_height

    # Create the points for the board shape
    points = [
        (0, 0),  # Lower left corner
        (max_width, 0),  # Lower right corner
        (max_width, min_height),  # Upper right corner
        (min_width, max_height),  # Transition for slanted edge
        (0, max_height)  # Upper left corner
    ]

    if min_width == 0:
        del points[3]  # Remove slanted edge if min_width is zero

    # Create the board by extruding the slanted rectangle shape
    board = cq.Workplane("YZ").polyline(points).close().extrude(board_thickness)

    # Calculate the offset from the center to the bottom-left corner
    x_offset = -max_width / 2
    y_offset = -max_height / 2

    # Add rectangular holes
    for hole in rectangular_holes:
        x, y, hole_width, hole_height = hole
        # Subtract half the width and height for bottom-left positioning
        hole_wp = board.faces(">X").workplane(centerOption="CenterOfBoundBox") \
            .transformed(offset=cq.Vector(x + x_offset, y + y_offset))
        board = hole_wp.rect(hole_width, hole_height).cutThruAll()

    # Add circular holes
    for hole in circular_holes:
        x, y, diameter = hole
        # Subtract half the width and height for bottom-left positioning
        hole_wp = board.faces(">X").workplane(centerOption="CenterOfBoundBox") \
            .transformed(offset=cq.Vector(x + x_offset, y + y_offset))
        board = hole_wp.circle(diameter / 2).cutThruAll()

    # Apply rotation and translation to position the board
    board = board.rotate((0, 0, 0), (1, 0, 0), rotation[0])
    board = board.rotate((0, 0, 0), (0, 1, 0), rotation[1])
    board = board.rotate((0, 0, 0), (0, 0, 1), rotation[2])

    board = board.translate(position)

    # Return the final CadQuery object
    return board


def create_2d_board(max_width, max_height, min_width=0, min_height=0, rectangular_holes=[], circular_holes=[]):
    """Create a 2D representation of a board with holes for DXF export"""
    # Set the min height equal to max height if it's zero (for full rectangle)
    if min_height == 0:
        min_height = max_height

    # Create the points for the board shape
    points = [
        (0, 0),  # Lower left corner
        (max_width, 0),  # Lower right corner
        (max_width, min_height),  # Upper right corner
        (min_width, max_height),  # Transition for slanted edge
        (0, max_height)  # Upper left corner
    ]

    if min_width == 0:
        del points[3]  # Remove slanted edge if min_width is zero

    # Create the 2D board shape
    board = cq.Workplane("XY").polyline(points).close()

    # Add rectangular holes
    for hole in rectangular_holes:
        x, y, hole_width, hole_height = hole
        # Calculate the bottom-left corner of the rectangle
        x_bl = x - hole_width / 2
        y_bl = y - hole_height / 2
        # Create the rectangular hole
        rect_points = [
            (x_bl, y_bl),
            (x_bl + hole_width, y_bl),
            (x_bl + hole_width, y_bl + hole_height),
            (x_bl, y_bl + hole_height)
        ]
        hole = cq.Workplane("XY").polyline(rect_points).close()
        board = board.cut(hole)

    # Add circular holes
    for hole in circular_holes:
        x, y, diameter = hole
        circle = cq.Workplane("XY").circle(diameter / 2).center(x, y)
        board = board.cut(circle)

    return board


def generate_board_list(parameters):
    """Generate a list of all boards with their dimensions."""
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
            "description": "Front panel of the base with access hole",
            "rectangular_holes": [[p.organ_internal_width_g/2, 300, 300, 300]]
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
        }
    ]
    
    return board_list


def generate_cutfile_csv(board_list, output_path):
    """Generate a CSV file with the board cutting specifications."""
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['Name', 'Width (mm)', 'Height (mm)', 'Thickness (mm)', 'Description', 'Notes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for board in board_list:
            writer.writerow({
                'Name': board['name'],
                'Width (mm)': board['width'],
                'Height (mm)': board['height'],
                'Thickness (mm)': board['thickness'],
                'Description': board['description'],
                'Notes': board.get('notes', '')
            })


def generate_dxf_with_annotations(board_list, output_path):
    """Generate a DXF file with all board shapes and annotations at 1/10 scale."""
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
        scaled_width = board['width'] * scale
        scaled_height = board['height'] * scale
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
        width = board['width'] * scale
        height = board['height'] * scale
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
            f"{name} ({board['width']:.0f}x{board['height']:.0f}x{thickness:.0f}mm)",
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
            "ORGAN CABINET - CUTTING LIST (1:10 SCALE)",
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


def generate_general_console(parameters):
    p = DotDict(parameters)
    
    # Base right table
    base_right_table = create_board(
        max_width=p.base_depth_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(- p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 0)
    )

    # Base left table
    base_left_table = create_board(
        max_width=p.base_depth_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.organ_internal_width_g - 2* p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 0)
    )

    # Base back
    base_back = create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, 0),
        rotation=(0, 0, 90)
    )

    # Base front
    base_front = create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_height_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.base_depth_g-100, 0),
        rotation=(0, 0, 90),
        rectangular_holes=[[p.organ_internal_width_g/2, 300, 300, 300]]
    )

    # Base horizontal
    base_horizontal = create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_depth_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.general_board_thickness_g, p.base_height_g),
        rotation=(0, 90, 90)
    )

    # Top lateral left
    top_lateral_left = create_board(
        max_width=p.top_depth_g,
        max_height=p.top_height_g,
        min_width=p.top_notch_start_x_g,
        min_height=p.top_notch_start_y_g,
        board_thickness=p.general_board_thickness_g,
        position=(- p.general_board_thickness_g, 0, p.base_height_g),
        rotation=(0, 0, 0)
    )

    # Top lateral right
    top_lateral_right = create_board(
        max_width=p.top_depth_g,
        max_height=p.top_height_g,
        min_width=p.top_notch_start_x_g,
        min_height=p.top_notch_start_y_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.organ_internal_width_g - 2* p.general_board_thickness_g, 0, p.base_height_g),
        rotation=(0, 0, 0)
    )

    # Top back
    top_back = create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_height_g - 2 * p.general_board_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, p.base_height_g + p.general_board_thickness_g),
        rotation=(0, 0, 90)
    )

    # Top front
    top_front = create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.top_height_g - 2 * p.general_board_thickness_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, p.base_depth_g, p.base_height_g + p.general_board_thickness_g),
        rotation=(0, 0, 90)
    )

    # Top lid
    top_lid = create_board(
        max_width=p.organ_internal_width_g,
        max_height=p.base_depth_g,
        board_thickness=p.general_board_thickness_g,
        position=(-p.general_board_thickness_g, 0, p.base_height_g + p.top_height_g - p.general_board_thickness_g),
        rotation=(0, 90, 90)
    )

    # Combine all parts
    result = base_right_table.add(base_left_table).add(base_back).add(base_front).add(base_horizontal)
    result = result.add(top_lateral_left).add(top_lateral_right).add(top_back).add(top_front).add(top_lid)
    
    return result




def encode_local_image(file_path):
    """Load local image file and encode as base64 data URI"""
    try:
        import base64
        
        with open(file_path, 'rb') as f:
            image_data = f.read()
            
        # Encode as base64 data URI
        encoded = base64.b64encode(image_data).decode('utf-8')
        
        # Determine MIME type based on file extension
        if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
            mime_type = "image/jpeg"
        elif file_path.lower().endswith('.png'):
            mime_type = "image/png"
        else:
            mime_type = "image/jpeg"  # Default to JPEG
            
        return f"data:{mime_type};base64,{encoded}"
    except Exception as e:
        st.warning(f"Failed to load local texture: {str(e)}")
        return None

def find_wood_texture():
    """Find wood texture file in current directory"""
    import glob
    
    # Look for common wood texture file names
    patterns = [
        "wood*.jpg", "wood*.jpeg", "wood*.png",
        "texture*.jpg", "texture*.jpeg", "texture*.png",
        "*.jpg", "*.jpeg", "*.png"
    ]
    
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            return files[0]  # Return first match
    
    return None

def add_lacquered_wood_material_to_gltf(gltf_path):
    """Add lacquered wood PBR material with local texture to GLTF file"""
    try:
        with open(gltf_path, 'r') as f:
            gltf_data = json.load(f)
        
        # Find local wood texture
        wood_texture_file = find_wood_texture()
        
        if not wood_texture_file:
            st.warning("No wood texture file found, using procedural material")
            return add_procedural_wood_material(gltf_data, gltf_path)
        
        st.info(f"Using wood texture: {wood_texture_file}")
        diffuse_data_uri = encode_local_image(wood_texture_file)
        
        # Fallback to procedural material if encoding fails
        if not diffuse_data_uri:
            st.warning("Failed to load local texture, using procedural material")
            return add_procedural_wood_material(gltf_data, gltf_path)
        
        # Add textures array for wood texture images
        if "textures" not in gltf_data:
            gltf_data["textures"] = []
        if "images" not in gltf_data:
            gltf_data["images"] = []
        if "samplers" not in gltf_data:
            gltf_data["samplers"] = []
        
        # Add wood texture image
        wood_diffuse_image = {
            "uri": diffuse_data_uri,
            "name": "WoodDiffuse"
        }
        
        gltf_data["images"].append(wood_diffuse_image)
        
        # Add texture sampler for repeating wood pattern
        wood_sampler = {
            "magFilter": 9729,  # LINEAR
            "minFilter": 9987,  # LINEAR_MIPMAP_LINEAR
            "wrapS": 10497,     # REPEAT
            "wrapT": 10497      # REPEAT
        }
        gltf_data["samplers"].append(wood_sampler)
        sampler_index = len(gltf_data["samplers"]) - 1
        
        # Add texture
        diffuse_texture = {
            "sampler": sampler_index,
            "source": len(gltf_data["images"]) - 1  # Wood diffuse image
        }
        
        gltf_data["textures"].append(diffuse_texture)
        diffuse_texture_index = len(gltf_data["textures"]) - 1
        
        # Define high-gloss lacquered wood PBR material (PyVista compatible)
        wood_material = {
            "name": "HighGlossLacqueredWood",
            "pbrMetallicRoughness": {
                "baseColorTexture": {
                    "index": diffuse_texture_index,
                    "texCoord": 0
                },
                "baseColorFactor": [0.9, 0.7, 0.5, 1.0],  # Brighter wood tint for better visibility
                "metallicFactor": 0.1,   # Slightly higher metallic for more reflection
                "roughnessFactor": 0.02  # Very low roughness for mirror-like lacquer finish
            },
            "emissiveFactor": [0.12, 0.08, 0.04]  # Stronger warm glow for lacquer effect
        }
        
        # Add materials array if it doesn't exist
        if "materials" not in gltf_data:
            gltf_data["materials"] = []
        
        gltf_data["materials"].append(wood_material)
        material_index = len(gltf_data["materials"]) - 1
        
        # Apply material to all meshes
        if "meshes" in gltf_data:
            for mesh in gltf_data["meshes"]:
                if "primitives" in mesh:
                    for primitive in mesh["primitives"]:
                        primitive["material"] = material_index
        
        # Enhanced cathedral lighting
        if "extensions" not in gltf_data:
            gltf_data["extensions"] = {}
        
        gltf_data["extensions"]["KHR_lights_punctual"] = {
            "lights": [
                {
                    "name": "MainCathedralLight",
                    "type": "directional",
                    "color": [1.0, 0.95, 0.8],  # Warm golden light
                    "intensity": 4.0
                },
                {
                    "name": "StainedGlassLight1", 
                    "type": "spot",
                    "color": [0.9, 0.7, 1.0],  # Purple stained glass
                    "intensity": 3.0,
                    "range": 800,
                    "spot": {
                        "innerConeAngle": 0.5,
                        "outerConeAngle": 1.0
                    }
                },
                {
                    "name": "StainedGlassLight2",
                    "type": "spot", 
                    "color": [1.0, 0.8, 0.6],  # Amber stained glass
                    "intensity": 2.5,
                    "range": 600,
                    "spot": {
                        "innerConeAngle": 0.3,
                        "outerConeAngle": 0.8
                    }
                }
            ]
        }
        
        # Add required extensions to the root
        if "extensionsUsed" not in gltf_data:
            gltf_data["extensionsUsed"] = []
        
        # Only use extensions that PyVista supports
        extensions_needed = ["KHR_lights_punctual"]
        for ext in extensions_needed:
            if ext not in gltf_data["extensionsUsed"]:
                gltf_data["extensionsUsed"].append(ext)
        
        # Save modified GLTF
        with open(gltf_path, 'w') as f:
            json.dump(gltf_data, f, indent=2)
            
        return True
        
    except Exception as e:
        st.warning(f"Failed to add materials to GLTF: {str(e)}")
        return False

def add_procedural_wood_material(gltf_data, gltf_path):
    """Add procedural wood material without external textures"""
    try:
        # Define high-gloss lacquered wood PBR material (no textures, PyVista compatible)
        wood_material = {
            "name": "ProceduralLacqueredWood",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.65, 0.45, 0.3, 1.0],  # Brighter rich wood brown
                "metallicFactor": 0.15,  # Higher metallic for more reflection
                "roughnessFactor": 0.03  # Very low roughness for high-gloss lacquer
            },
            "emissiveFactor": [0.15, 0.1, 0.05]  # Stronger warm glow from lacquer
        }
        
        # Add materials array if it doesn't exist
        if "materials" not in gltf_data:
            gltf_data["materials"] = []
        
        gltf_data["materials"].append(wood_material)
        material_index = len(gltf_data["materials"]) - 1
        
        # Apply material to all meshes
        if "meshes" in gltf_data:
            for mesh in gltf_data["meshes"]:
                if "primitives" in mesh:
                    for primitive in mesh["primitives"]:
                        primitive["material"] = material_index
        
        # Add cathedral lighting
        if "extensions" not in gltf_data:
            gltf_data["extensions"] = {}
        
        gltf_data["extensions"]["KHR_lights_punctual"] = {
            "lights": [
                {
                    "name": "MainCathedralLight",
                    "type": "directional",
                    "color": [1.0, 0.95, 0.8],
                    "intensity": 4.0
                },
                {
                    "name": "AmbientLight", 
                    "type": "point",
                    "color": [0.9, 0.8, 1.0],
                    "intensity": 2.0,
                    "range": 1000
                }
            ]
        }
        
        # Add required extensions (only PyVista supported ones)
        if "extensionsUsed" not in gltf_data:
            gltf_data["extensionsUsed"] = []
        
        extensions_needed = ["KHR_lights_punctual"]
        for ext in extensions_needed:
            if ext not in gltf_data["extensionsUsed"]:
                gltf_data["extensionsUsed"].append(ext)
        
        # Save modified GLTF
        with open(gltf_path, 'w') as f:
            json.dump(gltf_data, f, indent=2)
            
        return True
        
    except Exception as e:
        st.warning(f"Failed to add procedural material: {str(e)}")
        return False

def generate_temp_file(model, file_format, tessellation):
    """Generates a temporary file with the specified STL, STEP, or GLTF format."""
    if file_format.lower() == "gltf":
        file_suffix = ".gltf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmpfile:
            try:
                # For GLTF, create an Assembly and use save() method
                assembly = cq.Assembly()
                assembly.add(model, name="organ_cabinet")
                assembly.save(tmpfile.name)
                
                # Add lacquered wood material and cathedral lighting
                add_lacquered_wood_material_to_gltf(tmpfile.name)
                
                return tmpfile.name
            except Exception as e:
                # Fall back to STL if GLTF fails
                st.warning(f"GLTF export failed ({str(e)}), using STL format")
                stl_tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".stl")
                cq.exporters.export(model, stl_tmpfile.name, exportType=cq.exporters.ExportTypes.STL, 
                                   tolerance=getattr(Tessellation, tessellation.upper()).value)
                return stl_tmpfile.name
    elif file_format.lower() == "stl":
        file_suffix = ".stl"
        export_type = cq.exporters.ExportTypes.STL
    elif file_format.lower() == "step":
        file_suffix = ".step"
        export_type = cq.exporters.ExportTypes.STEP
    else:
        raise ValueError(f"Unsupported file format: {file_format}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmpfile:
        cq.exporters.export(model, tmpfile.name, exportType=export_type, 
                           tolerance=getattr(Tessellation, tessellation.upper()).value)
        return tmpfile.name


def generate_temp_csv(parameters):
    """Generates a temporary CSV file with the cutting specifications."""
    board_list = generate_board_list(parameters)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmpfile:
        generate_cutfile_csv(board_list, tmpfile.name)
        return tmpfile.name


def generate_temp_dxf(parameters):
    """Generates a temporary DXF file with 2D profiles."""
    board_list = generate_board_list(parameters)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmpfile:
        try:
            generate_dxf_with_annotations(board_list, tmpfile.name)
            return tmpfile.name
        except Exception as e:
            st.error(f"Failed to generate DXF: {str(e)}")
            return None


@st.cache_data
def generate_and_export_organ_cabinet_cached(
    organ_internal_width,
    general_board_thickness,
    base_height,
    base_depth,
    base_front_distance,
    volume_pedals_width,
    volume_pedals_height,
    volume_pedals_number,
    volume_pedals_hole_start_height,
    top_depth,
    top_height,
    top_notch_start_x,
    top_notch_start_y,
    file_format,
    tessellation
):
    # Organize parameters in the expected structure
    parameters = {
        "General_and_base": [
            {"organ_internal_width_g": organ_internal_width},
            {"general_board_thickness_g": general_board_thickness},
            {"base_height_g": base_height},
            {"base_depth_g": base_depth},
            {"base_front_distance_g": base_front_distance}
        ],
        "Volume_pedals": [
            {"volume_pedals_width_g": volume_pedals_width},
            {"volume_pedals_height_g": volume_pedals_height},
            {"volume_pedals_number_g": volume_pedals_number},
            {"volume_pedals_hole_start_height_g": volume_pedals_hole_start_height}
        ],
        "Top": [
            {"top_depth_g": top_depth},
            {"top_height_g": top_height},
            {"top_notch_start_x_g": top_notch_start_x},
            {"top_notch_start_y_g": top_notch_start_y}
        ]
    }
    
    # Generate the organ cabinet model
    organ_model = generate_general_console(parameters)
    
    # Export to the specified format
    return generate_temp_file(organ_model, file_format, tessellation), generate_temp_csv(parameters), generate_temp_dxf(parameters)


# ----------------------- Streamlit UI ----------------------- #

# Streamlit UI for parameter inputs
st.set_page_config(layout='wide', page_title='Organ Cabinet Designer')
col1, col2, col3 = st.columns([2, 2, 4])

with col1:
    st.header("Organ Cabinet Model Generator")
    st.subheader("General Configuration")
    organ_internal_width = st.slider('Cabinet Internal Width (mm)', min_value=800, max_value=2000, value=1300, step=50)
    general_board_thickness = st.slider('Board Thickness (mm)', min_value=12, max_value=25, value=18, step=1)
    
    st.divider()
    st.subheader("Base Dimensions")
    base_height = st.slider('Base Height (mm)', min_value=500, max_value=1000, value=800, step=50)
    base_depth = st.slider('Base Depth (mm)', min_value=250, max_value=500, value=350, step=25)
    base_front_distance = st.slider('Base Front Distance (mm)', min_value=0, max_value=50, value=10, step=5)

with col2:
    st.subheader("Volume Pedals Configuration")
    volume_pedals_width = st.slider('Volume Pedals Width (mm)', min_value=8, max_value=20, value=12, step=1)
    volume_pedals_height = st.slider('Volume Pedals Height (mm)', min_value=16, max_value=32, value=24, step=1)
    volume_pedals_number = st.slider('Number of Volume Pedals', min_value=1, max_value=4, value=2, step=1)
    volume_pedals_hole_start_height = st.slider('Volume Pedals Hole Start Height (mm)', min_value=100, max_value=200, value=140, step=10)
    
    st.divider()
    st.subheader("Top Section Configuration")
    top_depth = st.slider('Top Depth (mm)', min_value=400, max_value=800, value=650, step=25)
    top_height = st.slider('Top Height (mm)', min_value=200, max_value=500, value=350, step=25)
    top_notch_start_x = st.slider('Top Notch Start X (mm)', min_value=200, max_value=500, value=350, step=25)
    top_notch_start_y = st.slider('Top Notch Start Y (mm)', min_value=100, max_value=300, value=150, step=25)
    
    st.divider()
    st.subheader("Export Settings")
    tessellation_value = st.select_slider('Surface quality', options=[t.name.lower() for t in Tessellation])


# ----------------------- Visualization ----------------------- #
file_path_gltf, file_path_csv, file_path_dxf = generate_and_export_organ_cabinet_cached(
    organ_internal_width=organ_internal_width,
    general_board_thickness=general_board_thickness,
    base_height=base_height,
    base_depth=base_depth,
    base_front_distance=base_front_distance,
    volume_pedals_width=volume_pedals_width,
    volume_pedals_height=volume_pedals_height,
    volume_pedals_number=volume_pedals_number,
    volume_pedals_hole_start_height=volume_pedals_hole_start_height,
    top_depth=top_depth,
    top_height=top_height,
    top_notch_start_x=top_notch_start_x,
    top_notch_start_y=top_notch_start_y,
    file_format="gltf",
    tessellation=tessellation_value
)

# Generate STEP file separately (not using the CSV here)
file_path_step, _, _ = generate_and_export_organ_cabinet_cached(
    organ_internal_width=organ_internal_width,
    general_board_thickness=general_board_thickness,
    base_height=base_height,
    base_depth=base_depth,
    base_front_distance=base_front_distance,
    volume_pedals_width=volume_pedals_width,
    volume_pedals_height=volume_pedals_height,
    volume_pedals_number=volume_pedals_number,
    volume_pedals_hole_start_height=volume_pedals_hole_start_height,
    top_depth=top_depth,
    top_height=top_height,
    top_notch_start_x=top_notch_start_x,
    top_notch_start_y=top_notch_start_y,
    file_format="step",
    tessellation=tessellation_value
)

# Configure PyVista visualization
if platform.system() == 'Linux':
    pv.start_xvfb()

plotter = pv.Plotter(window_size=[500, 500])
plotter.import_gltf(file_path_gltf)

# Set exact camera parameters for perfect organ console view
plotter.camera.elevation = -90.0
plotter.camera.azimuth = -30.0
plotter.camera.position = (65.48, 1823.65, -2466.51)
plotter.camera.focal_point = (-668.00, 575.00, -334.00)
plotter.camera.up = (-1000.000, 0.000, 1.000)
plotter.camera.roll = 0
plotter.camera.view_angle = 30.0

plotter.set_background("#0e1117")

with col3:
    stv(plotter, key=f"organ_cabinet_{datetime.now()}")
    
    # Create a columns for downloads
    st.subheader("Download Files")
    download_col1, download_col2, download_col3 = st.columns(3)
    
    with download_col1:
        with open(file_path_gltf, 'rb') as gltf_file:
            st.download_button(
                label="Download GLTF File",
                data=gltf_file,
                file_name="organ_cabinet.gltf",
                mime="model/gltf+json",
            )
    
    with download_col2:
        with open(file_path_step, 'rb') as step_file:
            st.download_button(
                label="Download STEP File",
                data=step_file,
                file_name="organ_cabinet.step",
                mime="application/step",
            )
    
    with download_col3:
        with open(file_path_csv, 'rb') as csv_file:
            st.download_button(
                label="Download Cutting List (CSV)",
                data=csv_file,
                file_name="organ_cabinet_cutlist.csv",
                mime="text/csv",
            )
    
    if file_path_dxf:
        col_dxf, col_empty = st.columns(2)
        with col_dxf:
            with open(file_path_dxf, 'rb') as dxf_file:
                st.download_button(
                    label="Download DXF Profiles",
                    data=dxf_file,
                    file_name="organ_cabinet_profiles.dxf",
                    mime="application/dxf",
                )
    
    # Display the cutting list in the app
    st.subheader("Cutting List Preview")
    
    # Read and display the CSV file
    import pandas as pd
    cutlist_df = pd.read_csv(file_path_csv)
    st.dataframe(cutlist_df, use_container_width=True)