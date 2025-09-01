"""
File Exporters Module

This module handles all file generation and export operations for the organ cabinet project.
Supports GLTF, STL, STEP, CSV, and DXF export formats.

Usage:
    from file_exporters import generate_temp_file, generate_cutfile_csv, generate_dxf_with_annotations
    from organ_generator import generate_general_console, generate_board_list, get_default_parameters
    
    # Generate model and export
    params = get_default_parameters()
    model = generate_general_console(params)
    
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
import cadquery as cq


class Tessellation(Enum):
    """Tessellation quality levels for mesh export"""
    COARSE = 1e-3
    MEDIUM = 1e-4
    FINE = 1e-5


def add_wood_texture_to_gltf(gltf_file_path):
    """
    Add wood texture and material to an existing GLTF file.
    
    Args:
        gltf_file_path: Path to the existing GLTF file
    
    Returns:
        str: Path to the enhanced GLTF file
    """
    try:
        # Read the existing GLTF file
        with open(gltf_file_path, 'r') as f:
            gltf_data = json.load(f)
        
        # Find a wood texture file
        wood_texture_path = None
        for pattern in ["wood*.jpg", "wood*.jpeg", "wood*.png"]:
            import glob
            files = glob.glob(pattern)
            if files:
                wood_texture_path = files[0]
                break
        
        if wood_texture_path and os.path.exists(wood_texture_path):
            # Encode wood texture as base64
            with open(wood_texture_path, 'rb') as f:
                texture_data = f.read()
            texture_base64 = base64.b64encode(texture_data).decode('utf-8')
            
            # Determine MIME type
            if wood_texture_path.lower().endswith('.jpg') or wood_texture_path.lower().endswith('.jpeg'):
                mime_type = "image/jpeg"
            else:
                mime_type = "image/png"
            
            texture_uri = f"data:{mime_type};base64,{texture_base64}"
        else:
            # Use online wood texture as fallback
            texture_uri = "https://threejs.org/examples/textures/hardwood2_diffuse.jpg"
        
        # Add texture to GLTF
        if "images" not in gltf_data:
            gltf_data["images"] = []
        
        gltf_data["images"].append({
            "uri": texture_uri,
            "name": "wood_texture"
        })
        
        # Add texture sampler
        if "textures" not in gltf_data:
            gltf_data["textures"] = []
        
        gltf_data["textures"].append({
            "source": len(gltf_data["images"]) - 1,
            "name": "wood_texture_sampler"
        })
        
        # Create wood material
        if "materials" not in gltf_data:
            gltf_data["materials"] = []
        
        wood_material = {
            "name": "LacqueredWood",
            "pbrMetallicRoughness": {
                "baseColorTexture": {
                    "index": len(gltf_data["textures"]) - 1,
                    "texCoord": 0
                },
                "baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.2
            },
            "extensions": {
                "KHR_materials_clearcoat": {
                    "clearcoatFactor": 0.8,
                    "clearcoatRoughnessFactor": 0.1
                }
            }
        }
        
        gltf_data["materials"].append(wood_material)
        
        # Apply material to all meshes
        if "meshes" in gltf_data:
            material_index = len(gltf_data["materials"]) - 1
            for mesh in gltf_data["meshes"]:
                if "primitives" in mesh:
                    for primitive in mesh["primitives"]:
                        primitive["material"] = material_index
        
        # Add required extensions
        if "extensionsUsed" not in gltf_data:
            gltf_data["extensionsUsed"] = []
        
        if "KHR_materials_clearcoat" not in gltf_data["extensionsUsed"]:
            gltf_data["extensionsUsed"].append("KHR_materials_clearcoat")
        
        # Write enhanced GLTF file
        enhanced_path = gltf_file_path.replace('.gltf', '_textured.gltf')
        with open(enhanced_path, 'w') as f:
            json.dump(gltf_data, f, indent=2)
        
        try:
            import streamlit as st
            st.success("✅ Wood texture embedded into GLTF!")
        except ImportError:
            print("✅ Wood texture embedded into GLTF!")
        
        return enhanced_path
        
    except Exception as e:
        try:
            import streamlit as st
            st.warning(f"Failed to add texture to GLTF: {str(e)}")
        except ImportError:
            print(f"Failed to add texture to GLTF: {str(e)}")
        
        # Return original file if enhancement fails
        return gltf_file_path


def generate_temp_file(model, file_format, quality="medium"):
    """
    Generates a temporary file with the specified format.
    
    Args:
        model: CadQuery model object
        file_format: "threejs", "gltf", "stl", or "step"
        quality: "coarse", "medium", or "fine" (used for STL/STEP only)
    
    Returns:
        str: Path to the generated temporary file
    """
    if file_format.lower() == "threejs":
        # Use CadQuery's built-in Three.js export (TJS format)
        file_suffix = ".json"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmpfile:
            try:
                # Use the official CadQuery Three.js export via exporters module
                tolerance = getattr(Tessellation, quality.upper()).value
                cq.exporters.export(
                    model,
                    tmpfile.name,
                    exportType=cq.exporters.ExportTypes.TJS,
                    tolerance=tolerance,
                    angularTolerance=0.1
                )
                
                try:
                    import streamlit as st
                    st.success("✅ Three.js geometry export successful!")
                except ImportError:
                    print("✅ Three.js geometry export successful!")
                
                return tmpfile.name
                
            except Exception as e:
                # If Three.js export fails, fall back to GLTF
                try:
                    import streamlit as st
                    st.warning(f"Three.js export failed: {str(e)}, using GLTF instead")
                except ImportError:
                    print(f"Three.js export failed: {str(e)}, using GLTF instead")
                
                # Fall back to GLTF
                gltf_tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".gltf")
                try:
                    assembly = cq.Assembly()
                    assembly.add(model, name="organ_cabinet")
                    assembly.save(gltf_tmpfile.name)
                    return gltf_tmpfile.name
                except Exception as gltf_error:
                    # Final fallback to STL
                    stl_tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".stl")
                    cq.exporters.export(model, stl_tmpfile.name, exportType=cq.exporters.ExportTypes.STL)
                    return stl_tmpfile.name
                
    elif file_format.lower() == "gltf":
        file_suffix = ".gltf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmpfile:
            try:
                # For GLTF, create an Assembly and use save() method
                assembly = cq.Assembly()
                assembly.add(model, name="organ_cabinet")
                assembly.save(tmpfile.name)
                
                # Enhance the GLTF file with embedded wood texture and material
                enhanced_gltf_path = add_wood_texture_to_gltf(tmpfile.name)
                return enhanced_gltf_path
                
            except Exception as e:
                # Fall back to STL if GLTF fails
                import streamlit as st
                st.warning(f"GLTF export failed ({str(e)}), using STL format")
                stl_tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".stl")
                tolerance = getattr(Tessellation, quality.upper()).value
                cq.exporters.export(model, stl_tmpfile.name, exportType=cq.exporters.ExportTypes.STL, 
                                   tolerance=tolerance)
                return stl_tmpfile.name
    elif file_format.lower() == "stl":
        file_suffix = ".stl"
        export_type = cq.exporters.ExportTypes.STL
    elif file_format.lower() == "step":
        file_suffix = ".step"
        export_type = cq.exporters.ExportTypes.STEP
    else:
        raise ValueError(f"Unsupported file format: {file_format}")

    # For STL and STEP, use the quality parameter
    tolerance = getattr(Tessellation, quality.upper()).value
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmpfile:
        cq.exporters.export(model, tmpfile.name, exportType=export_type, 
                           tolerance=tolerance)
        return tmpfile.name


def generate_cutfile_csv(board_list, output_path):
    """
    Generate a CSV file with the board cutting specifications.
    
    Args:
        board_list: List of board dictionaries from generate_board_list()
        output_path: Path where to save the CSV file
    
    Returns:
        str: Path to the generated CSV file
    """
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
    return output_path


def generate_temp_csv(parameters):
    """
    Generates a temporary CSV file with the cutting specifications.
    
    Args:
        parameters: Parameter dictionary for generating board list
    
    Returns:
        str: Path to the generated temporary CSV file
    """
    from organ_generator import generate_board_list
    
    board_list = generate_board_list(parameters)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmpfile:
        generate_cutfile_csv(board_list, tmpfile.name)
        return tmpfile.name


def generate_temp_dxf(parameters):
    """
    Generates a temporary DXF file with 2D profiles.
    
    Args:
        parameters: Parameter dictionary for generating board list
    
    Returns:
        str: Path to the generated temporary DXF file, or None if failed
    """
    from organ_generator import generate_board_list
    
    board_list = generate_board_list(parameters)
    
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
