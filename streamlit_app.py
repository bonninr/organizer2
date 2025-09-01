"""
Streamlit Organ Cabinet Designer App

This is the main Streamlit interface that integrates all the modular components:
- organ_generator: CadQuery geometry generation
- file_exporters: File export functionality  
- threejs_viewer: 3D visualization

Usage:
    streamlit run streamlit_app.py

The app provides an interactive interface for designing organ cabinets with:
- Parameter controls for dimensions and configuration
- Real-time 3D preview with wood materials
- Export to multiple formats (GLTF, STEP, CSV, DXF)
- Cutting list generation
"""

import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from functools import cache

# Import our modular components
from organ_generator import generate_general_console, generate_board_list, get_default_parameters
from file_exporters import generate_temp_file, generate_temp_csv, generate_temp_dxf, Tessellation
from threejs_viewer import create_threejs_gltf_viewer, find_wood_texture


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
    """
    Cached function to generate and export the organ cabinet model.
    This prevents regeneration when parameters haven't changed.
    """
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
    return (
        generate_temp_file(organ_model, file_format, tessellation), 
        generate_temp_csv(parameters), 
        generate_temp_dxf(parameters)
    )


def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        layout='wide', 
        page_title='Organ Cabinet Designer',
        page_icon='🎹',
        initial_sidebar_state='expanded'
    )
    
    # Main layout
    col1, col2, col3 = st.columns([2, 2, 4])
    
    # ----------------------- Parameter Controls ----------------------- #
    with col1:
        st.header("🎹 Organ Cabinet Designer")
        st.subheader("General Configuration")
        
        organ_internal_width = st.slider(
            'Cabinet Internal Width (mm)', 
            min_value=800, max_value=2000, value=1300, step=50,
            help="Internal width of the organ cabinet"
        )
        
        general_board_thickness = st.slider(
            'Board Thickness (mm)', 
            min_value=12, max_value=25, value=18, step=1,
            help="Thickness of all wooden boards"
        )
        
        st.divider()
        st.subheader("Base Dimensions")
        
        base_height = st.slider(
            'Base Height (mm)', 
            min_value=500, max_value=1000, value=800, step=50,
            help="Height of the base section"
        )
        
        base_depth = st.slider(
            'Base Depth (mm)', 
            min_value=250, max_value=500, value=350, step=25,
            help="Depth of the base section"
        )
        
        base_front_distance = st.slider(
            'Base Front Distance (mm)', 
            min_value=0, max_value=50, value=10, step=5,
            help="Distance from front edge"
        )

    with col2:
        st.subheader("Volume Pedals Configuration")
        
        volume_pedals_width = st.slider(
            'Volume Pedals Width (mm)', 
            min_value=8, max_value=20, value=12, step=1,
            help="Width of volume pedal holes"
        )
        
        volume_pedals_height = st.slider(
            'Volume Pedals Height (mm)', 
            min_value=16, max_value=32, value=24, step=1,
            help="Height of volume pedal holes"
        )
        
        volume_pedals_number = st.slider(
            'Number of Volume Pedals', 
            min_value=1, max_value=4, value=2, step=1,
            help="Number of volume pedal controls"
        )
        
        volume_pedals_hole_start_height = st.slider(
            'Volume Pedals Hole Start Height (mm)', 
            min_value=100, max_value=200, value=140, step=10,
            help="Starting height for volume pedal holes"
        )
        
        st.divider()
        st.subheader("Top Section Configuration")
        
        top_depth = st.slider(
            'Top Depth (mm)', 
            min_value=400, max_value=800, value=650, step=25,
            help="Depth of the top section"
        )
        
        top_height = st.slider(
            'Top Height (mm)', 
            min_value=200, max_value=500, value=350, step=25,
            help="Height of the top section"
        )
        
        top_notch_start_x = st.slider(
            'Top Notch Start X (mm)', 
            min_value=200, max_value=500, value=350, step=25,
            help="X position where top notch starts"
        )
        
        top_notch_start_y = st.slider(
            'Top Notch Start Y (mm)', 
            min_value=100, max_value=300, value=150, step=25,
            help="Y position where top notch starts"
        )
        
        st.divider()
        st.subheader("Export Settings")
        
        quality_value = st.select_slider(
            'Surface Quality', 
            options=[t.name.lower() for t in Tessellation],
            value='medium',
            help="Quality of exported mesh surfaces (for STL/STEP only)"
        )

    # ----------------------- 3D Visualization ----------------------- #
    with col3:
        st.subheader("🎨 3D Model Preview")
        
        # Initialize variables to avoid UnboundLocalError
        file_path_threejs = None
        file_path_gltf = None 
        file_path_step = None
        file_path_csv = None
        file_path_dxf = None
        
        # Generate files for visualization - USE NATIVE THREE.JS FORMAT FOR BETTER TEXTURING
        try:
            file_path_threejs, file_path_csv, file_path_dxf = generate_and_export_organ_cabinet_cached(
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
                file_format="threejs",  # Use native Three.js format
                tessellation=quality_value
            )
            
            # Generate GLTF file separately for download
            file_path_gltf, _, _ = generate_and_export_organ_cabinet_cached(
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
                tessellation=quality_value
            )
            
            # Generate STEP file separately for download
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
                tessellation=quality_value
            )
            
            # Find wood texture for Three.js viewer
            wood_texture_path = find_wood_texture()
            
            # Create and display Three.js viewer using native geometry
            viewer_html = create_threejs_gltf_viewer(  # Note: still using same function but with different data
                gltf_file_path=file_path_gltf,  # Use GLTF for now, will enhance later
                wood_texture_path=wood_texture_path,
                height=500
            )
            
            # Display the Three.js viewer
            components.html(viewer_html, height=520, scrolling=False)
            
            # Show texture status
            if wood_texture_path:
                st.success(f"✅ Using wood texture: {os.path.basename(wood_texture_path)}")
            else:
                st.info("ℹ️ No wood texture found - using procedural material")
                
        except Exception as e:
            st.error(f"Failed to create 3D viewer: {str(e)}")
            st.info("Please check that all required dependencies are installed.")
        
        # ----------------------- Download Section ----------------------- #
        st.subheader("📥 Download Files")
        
        # Create download buttons in columns
        download_col1, download_col2, download_col3 = st.columns(3)
        
        with download_col1:
            try:
                with open(file_path_gltf, 'rb') as gltf_file:
                    st.download_button(
                        label="📄 Download GLTF",
                        data=gltf_file,
                        file_name="organ_cabinet.gltf",
                        mime="model/gltf+json",
                        help="3D model for web viewers"
                    )
            except:
                st.error("GLTF file not available")
        
        with download_col2:
            try:
                with open(file_path_step, 'rb') as step_file:
                    st.download_button(
                        label="🔧 Download STEP",
                        data=step_file,
                        file_name="organ_cabinet.step",
                        mime="application/step",
                        help="CAD file for engineering software"
                    )
            except:
                st.error("STEP file not available")
        
        with download_col3:
            try:
                with open(file_path_csv, 'rb') as csv_file:
                    st.download_button(
                        label="📊 Download CSV",
                        data=csv_file,
                        file_name="organ_cabinet_cutlist.csv",
                        mime="text/csv",
                        help="Cutting list for manufacturing"
                    )
            except:
                st.error("CSV file not available")
        
        # DXF download (if available)
        if file_path_dxf:
            col_dxf, col_empty = st.columns(2)
            with col_dxf:
                try:
                    with open(file_path_dxf, 'rb') as dxf_file:
                        st.download_button(
                            label="📐 Download DXF",
                            data=dxf_file,
                            file_name="organ_cabinet_profiles.dxf",
                            mime="application/dxf",
                            help="2D profiles for CNC cutting"
                        )
                except:
                    st.error("DXF file not available")
        
        # ----------------------- Cutting List Preview ----------------------- #
        st.subheader("📋 Cutting List Preview")
        
        try:
            # Read and display the CSV file
            cutlist_df = pd.read_csv(file_path_csv)
            st.dataframe(cutlist_df, use_container_width=True)
            
            # Summary statistics
            total_boards = len(cutlist_df)
            total_area = (cutlist_df['Width (mm)'] * cutlist_df['Height (mm)'] / 1000000).sum()
            
            col_stats1, col_stats2 = st.columns(2)
            with col_stats1:
                st.metric("Total Boards", total_boards)
            with col_stats2:
                st.metric("Total Area", f"{total_area:.2f} m²")
                
        except Exception as e:
            st.error(f"Failed to load cutting list: {str(e)}")

    # ----------------------- Sidebar Information ----------------------- #
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        **Organ Cabinet Designer** is a modular application for designing 
        custom organ cabinets with precise dimensions and specifications.
        
        **Features:**
        - Interactive 3D preview with wood materials
        - Real-time parameter adjustment
        - Multiple export formats (GLTF, STEP, DXF, CSV)
        - Automatic cutting list generation
        - Modular codebase for easy development
        
        **Modules:**
        - `organ_generator.py` - CadQuery geometry (VSCode compatible)
        - `file_exporters.py` - Export functionality
        - `threejs_viewer.py` - 3D visualization
        - `streamlit_app.py` - Main interface
        """)
        
        st.divider()
        
        st.subheader("🔧 Development")
        st.markdown("""
        **VSCode CadQuery Integration:**
        Open `organ_generator.py` in VSCode with the CadQuery viewer 
        extension to interactively develop and test geometry.
        
        **Module Testing:**
        Each module can be imported and tested independently:
        ```python
        from organ_generator import generate_general_console
        from file_exporters import generate_temp_file
        from threejs_viewer import create_threejs_gltf_viewer
        ```
        """)


if __name__ == "__main__":
    main()
