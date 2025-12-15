"""
Streamlit Organ Console Designer App - build123d Version

This is the main Streamlit interface supporting multiple console models:
- Normal Console: Tower style for compact spaces
- Vertical Console: Horizontal style with keyboard, speakers, and pedals
- Bench Console: Simple bench design

Usage:
    streamlit run streamlit_app.py

The app provides an interactive interface for designing organ consoles with:
- Console type selector
- Consolidated parameter controls in left sidebar
- Real-time 3D preview with wood materials
- Export to multiple formats (GLTF, STEP, CSV, DXF)
- Cutting list generation
"""

import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# Import console models
import console_normal
import console_vertical
import console_bench
import console_pedalboard

# Import exporters and viewer
from file_exporters import generate_temp_file, generate_temp_csv, generate_temp_dxf, Tessellation
from threejs_viewer import create_threejs_gltf_viewer, find_wood_texture
from technical_drawing import create_a3_technical_drawing, generate_technical_drawing_cached


@st.cache_data
def generate_and_export_console_cached(
    console_type,
    parameters_dict,
    file_format,
    tessellation
):
    """
    Cached function to generate and export the organ console model.
    This prevents regeneration when parameters haven't changed.

    Args:
        console_type: "normal", "vertical", or "bench"
        parameters_dict: Dictionary with all console parameters
        file_format: Export format
        tessellation: Quality setting

    Returns:
        tuple: (model_file, csv_file, dxf_file)
    """
    # Select the appropriate console module
    if console_type == "normal":
        console_module = console_normal
    elif console_type == "vertical":
        console_module = console_vertical
    elif console_type == "bench":
        console_module = console_bench
    else:  # pedalboard
        console_module = console_pedalboard

    # Generate the organ console model
    console_model = console_module.generate_console(parameters_dict)

    # Generate board list for exports
    board_list = console_module.generate_board_list(parameters_dict)

    # Export to the specified format
    return (
        generate_temp_file(console_model, file_format, tessellation),
        generate_temp_csv(board_list),
        generate_temp_dxf(board_list)
    )


def main():
    """Main Streamlit application"""

    # Page configuration
    st.set_page_config(
        layout='wide',
        page_title='Organ Console Designer',
        initial_sidebar_state='expanded'
    )

    # SIDEBAR - CONSOLE TYPE SELECTION
    with st.sidebar:
        st.title("Organ Console Designer")

        console_type = st.radio(
            "Console Type",
            options=["normal", "vertical", "bench", "pedalboard"],
            format_func=lambda x: {"normal": "Normal Console", "vertical": "Vertical Console", "bench": "Bench Console", "pedalboard": "Pedalboard"}[x],
            help="Select the type of organ console to design"
        )

        st.divider()

        # PARAMETERS SECTION
        st.header("Parameters")

        # Initialize parameters based on console type
        if console_type == "normal":
            default_params = console_normal.get_default_parameters()
        elif console_type == "vertical":
            default_params = console_vertical.get_default_parameters()
        elif console_type == "bench":
            default_params = console_bench.get_default_parameters()
        else:  # pedalboard
            default_params = console_pedalboard.get_default_parameters()

        # GENERAL SECTION (Pedalboard only)
        if console_type == "pedalboard":
            with st.expander("General", expanded=True):
                general_board_thickness = st.slider(
                    'Board Thickness (mm)',
                    min_value=12, max_value=25,
                    value=default_params["General"][0]["general_board_thickness_g"],
                    step=1,
                    help="Thickness of all wooden boards"
                )

                general_board_offset = st.slider(
                    'Board Offset (mm)',
                    min_value=3, max_value=10,
                    value=default_params["General"][1]["general_board_offset_g"],
                    step=1,
                    help="Offset for board spacing"
                )

        # GENERAL AND BASE SECTION (Console types only)
        if console_type != "pedalboard":
            with st.expander("General & Base", expanded=True):
                organ_internal_width = st.slider(
                    'Internal Width (mm)',
                    min_value=800, max_value=2000,
                    value=default_params["General_and_base"][0]["organ_internal_width_g"],
                    step=50,
                    help="Internal width of the console"
                )

                general_board_thickness = st.slider(
                    'Board Thickness (mm)',
                    min_value=12, max_value=25,
                    value=default_params["General_and_base"][1]["general_board_thickness_g"],
                    step=1,
                    help="Thickness of all wooden boards"
                )

                base_height = st.slider(
                    'Base Height (mm)',
                    min_value=500, max_value=1200,
                    value=default_params["General_and_base"][2]["base_height_g"],
                    step=50,
                    help="Height of the base section"
                )

                base_depth = st.slider(
                    'Base Depth (mm)',
                    min_value=250, max_value=500,
                    value=default_params["General_and_base"][3]["base_depth_g"],
                    step=25,
                    help="Depth of the base section"
                )

                base_front_distance = st.slider(
                    'Base Front Distance (mm)',
                    min_value=0, max_value=200,
                    value=default_params["General_and_base"][4]["base_front_distance_g"],
                    step=10,
                    help="Front edge distance"
                )

            # Additional vertical-specific parameters
            if console_type == "vertical":
                general_board_offset = st.slider(
                    'Board Offset (mm)',
                    min_value=5, max_value=20,
                    value=default_params["General_and_base"][5]["general_board_offset_g"],
                    step=1,
                    help="Offset for board spacing"
                )

                general_feet_thickness = st.slider(
                    'Feet Thickness (mm)',
                    min_value=30, max_value=80,
                    value=default_params["General_and_base"][6]["general_feet_thickness_g"],
                    step=5,
                    help="Thickness of console feet"
                )

                note_stand_height = st.slider(
                    'Note Stand Height (mm)',
                    min_value=300, max_value=700,
                    value=default_params["General_and_base"][7]["note_stand_height_g"],
                    step=50,
                    help="Height of the music note stand"
                )

                note_stand_angle = st.slider(
                    'Note Stand Angle (degrees)',
                    min_value=0, max_value=30,
                    value=default_params["General_and_base"][8]["note_stand_angle_g"],
                    step=1,
                    help="Angle of the note stand"
                )

                note_shelf_height = st.slider(
                    'Note Shelf Height (mm)',
                    min_value=50, max_value=150,
                    value=default_params["General_and_base"][9]["note_shelf_height_g"],
                    step=10,
                    help="Height of the note shelf"
                )

            # Additional bench-specific parameters
            if console_type == "bench":
                general_board_offset = st.slider(
                    'Board Offset (mm)',
                    min_value=5, max_value=20,
                    value=default_params["General_and_base"][5]["general_board_offset_g"],
                    step=1,
                    help="Offset for board spacing"
                )

                general_feet_thickness = st.slider(
                    'Feet Thickness (mm)',
                    min_value=30, max_value=80,
                    value=default_params["General_and_base"][6]["general_feet_thickness_g"],
                    step=5,
                    help="Thickness of console feet"
                )

        # KEYBOARD SECTION (Vertical only)
        if console_type == "vertical":
            with st.expander("Keyboard", expanded=False):
                keyboard_width = st.slider(
                    'Keyboard Width (mm)',
                    min_value=600, max_value=1200,
                    value=default_params["Keyboard"][0]["keyboard_width_g"],
                    step=20,
                    help="Width of keyboard compartment"
                )

                keyboard_depth = st.slider(
                    'Keyboard Depth (mm)',
                    min_value=300, max_value=500,
                    value=default_params["Keyboard"][1]["keyboard_depth_g"],
                    step=25,
                    help="Depth of keyboard compartment"
                )

                keyboard_height = st.slider(
                    'Keyboard Height (mm)',
                    min_value=150, max_value=300,
                    value=default_params["Keyboard"][2]["keyboard_height_g"],
                    step=10,
                    help="Height of keyboard compartment"
                )

                keyboard_offset = st.slider(
                    'Keyboard Offset (mm)',
                    min_value=100, max_value=300,
                    value=default_params["Keyboard"][3]["keyboard_offset_g"],
                    step=10,
                    help="Keyboard positioning offset"
                )

        # SPEAKERS SECTION (Vertical only)
        if console_type == "vertical":
            with st.expander("Speakers", expanded=False):
                front_speaker_width = st.slider(
                    'Front Speaker Width (mm)',
                    min_value=200, max_value=600,
                    value=default_params["Speakers"][0]["front_speaker_width_g"],
                    step=25,
                    help="Width of front speakers"
                )

                front_speaker_height = st.slider(
                    'Front Speaker Height (mm)',
                    min_value=100, max_value=300,
                    value=default_params["Speakers"][1]["front_speaker_height_g"],
                    step=25,
                    help="Height of front speakers"
                )

                side_speaker_width = st.slider(
                    'Side Speaker Width (mm)',
                    min_value=50, max_value=200,
                    value=default_params["Speakers"][2]["side_speaker_width_g"],
                    step=10,
                    help="Width of side speakers"
                )

                side_speaker_height = st.slider(
                    'Side Speaker Height (mm)',
                    min_value=1000, max_value=2000,
                    value=default_params["Speakers"][3]["side_speaker_height_g"],
                    step=50,
                    help="Height of side speakers"
                )

                enable_lateral_speaker_holes = st.checkbox(
                    'Enable Lateral Speaker Holes',
                    value=default_params["Speakers"][4]["enable_lateral_speaker_holes_g"],
                    help="Enable or disable holes for lateral speakers in side panels"
                )

        # VOLUME PEDALS SECTION (Vertical only)
        if console_type == "vertical":
            with st.expander("Volume Pedals", expanded=False):
                volume_pedals_width = st.slider(
                    'Pedal Width (mm)',
                    min_value=80, max_value=200,
                    value=default_params["Volume_pedals"][0]["volume_pedals_width_g"],
                    step=10,
                    help="Width of each volume pedal"
                )

                volume_pedals_height = st.slider(
                    'Pedal Height (mm)',
                    min_value=150, max_value=300,
                    value=default_params["Volume_pedals"][1]["volume_pedals_height_g"],
                    step=10,
                    help="Height of each volume pedal"
                )

                volume_pedals_number = st.slider(
                    'Number of Pedals',
                    min_value=1, max_value=5,
                    value=default_params["Volume_pedals"][2]["volume_pedals_number_g"],
                    step=1,
                    help="Number of volume pedal controls"
                )

                volume_pedals_spacing = st.slider(
                    'Pedal Spacing (mm)',
                    min_value=5, max_value=20,
                    value=default_params["Volume_pedals"][3]["volume_pedals_spacing_g"],
                    step=1,
                    help="Spacing between pedals"
                )

                volume_pedals_hole_start_height = st.slider(
                    'Pedal Hole Start Height (mm)',
                    min_value=100, max_value=200,
                    value=default_params["Volume_pedals"][4]["volume_pedals_hole_start_height_g"],
                    step=10,
                    help="Starting height for pedal holes"
                )

            with st.expander("Register Knobs", expanded=False):
                enable_knob_holes = st.checkbox(
                    'Enable Knob Holes',
                    value=default_params["Knobs"][0]["enable_knob_holes_g"],
                    help="Add staggered knob holes to register panels"
                )

                knob_columns = st.slider(
                    'Number of Columns',
                    min_value=4, max_value=12,
                    value=default_params["Knobs"][1]["knob_columns_g"],
                    step=1,
                    help="Number of vertical columns of knobs"
                )

                knob_rows = st.slider(
                    'Rows per Column',
                    min_value=5, max_value=15,
                    value=default_params["Knobs"][2]["knob_rows_g"],
                    step=1,
                    help="Number of knob holes per column"
                )

                knob_diameter = st.slider(
                    'Knob Hole Diameter (mm)',
                    min_value=15, max_value=40,
                    value=default_params["Knobs"][3]["knob_diameter_g"],
                    step=1,
                    help="Diameter of each knob hole"
                )

                knob_vertical_spacing = st.slider(
                    'Vertical Spacing (mm)',
                    min_value=30, max_value=80,
                    value=default_params["Knobs"][4]["knob_vertical_spacing_g"],
                    step=5,
                    help="Vertical spacing between holes in same column"
                )

                knob_horizontal_spacing = st.slider(
                    'Horizontal Spacing (mm)',
                    min_value=40, max_value=100,
                    value=default_params["Knobs"][5]["knob_horizontal_spacing_g"],
                    step=5,
                    help="Horizontal spacing between columns"
                )

                knob_stagger_offset = st.slider(
                    'Stagger Offset (mm)',
                    min_value=0, max_value=50,
                    value=default_params["Knobs"][6]["knob_stagger_offset_g"],
                    step=5,
                    help="Vertical offset for alternating columns (stagger pattern)"
                )

                knob_margin_top = st.slider(
                    'Top Margin (mm)',
                    min_value=20, max_value=100,
                    value=default_params["Knobs"][7]["knob_margin_top_g"],
                    step=5,
                    help="Top margin from panel edge"
                )

                knob_margin_side = st.slider(
                    'Side Margin (mm)',
                    min_value=10, max_value=80,
                    value=default_params["Knobs"][8]["knob_margin_side_g"],
                    step=5,
                    help="Side margin from panel edge"
                )

        # VOLUME PEDALS SECTION (Normal only)
        if console_type == "normal":
            with st.expander("Volume Pedals", expanded=False):
                volume_pedals_width = st.slider(
                    'Pedal Width (mm)',
                    min_value=80, max_value=200,
                    value=default_params["Volume_pedals"][0]["volume_pedals_width_g"],
                    step=10,
                    help="Width of each volume pedal"
                )

                volume_pedals_height = st.slider(
                    'Pedal Height (mm)',
                    min_value=150, max_value=300,
                    value=default_params["Volume_pedals"][1]["volume_pedals_height_g"],
                    step=10,
                    help="Height of each volume pedal"
                )

                volume_pedals_number = st.slider(
                    'Number of Pedals',
                    min_value=1, max_value=5,
                    value=default_params["Volume_pedals"][2]["volume_pedals_number_g"],
                    step=1,
                    help="Number of volume pedal controls"
                )

                volume_pedals_spacing = st.slider(
                    'Pedal Spacing (mm)',
                    min_value=5, max_value=20,
                    value=default_params["Volume_pedals"][3]["volume_pedals_spacing_g"],
                    step=1,
                    help="Spacing between pedals"
                )

                volume_pedals_hole_start_height = st.slider(
                    'Pedal Hole Start Height (mm)',
                    min_value=100, max_value=200,
                    value=default_params["Volume_pedals"][4]["volume_pedals_hole_start_height_g"],
                    step=10,
                    help="Starting height for pedal holes"
                )

        # TOP SECTION (Normal only)
        if console_type == "normal":
            with st.expander("Top Section", expanded=False):
                top_depth = st.slider(
                    'Top Depth (mm)',
                    min_value=400, max_value=800,
                    value=default_params["Top"][0]["top_depth_g"],
                    step=25,
                    help="Depth of the top section"
                )

                top_height = st.slider(
                    'Top Height (mm)',
                    min_value=200, max_value=500,
                    value=default_params["Top"][1]["top_height_g"],
                    step=25,
                    help="Height of the top section"
                )

                top_notch_start_x = st.slider(
                    'Top Notch Start X (mm)',
                    min_value=200, max_value=500,
                    value=default_params["Top"][2]["top_notch_start_x_g"],
                    step=25,
                    help="X position where top notch starts"
                )

                top_notch_start_y = st.slider(
                    'Top Notch Start Y (mm)',
                    min_value=100, max_value=300,
                    value=default_params["Top"][3]["top_notch_start_y_g"],
                    step=25,
                    help="Y position where top notch starts"
                )

        # BENCH SECTION (Bench only)
        if console_type == "bench":
            with st.expander("Bench Dimensions", expanded=False):
                bench_depth = st.slider(
                    'Bench Depth (mm)',
                    min_value=250, max_value=500,
                    value=default_params["Bench"][0]["bench_depth_g"],
                    step=25,
                    help="Depth of the bench"
                )

                bench_height = st.slider(
                    'Bench Height (mm)',
                    min_value=400, max_value=800,
                    value=default_params["Bench"][1]["bench_height_g"],
                    step=50,
                    help="Height of the bench"
                )

                bench_length = st.slider(
                    'Bench Length (mm)',
                    min_value=600, max_value=1200,
                    value=default_params["Bench"][2]["bench_length_g"],
                    step=50,
                    help="Length of the bench"
                )

                bench_shelf_height = st.slider(
                    'Bench Shelf Height (mm)',
                    min_value=50, max_value=200,
                    value=default_params["Bench"][3]["bench_shelf_height_g"],
                    step=10,
                    help="Height of the internal shelf"
                )

        # PEDALBOARD SECTION (Pedalboard only)
        if console_type == "pedalboard":
            with st.expander("Pedals", expanded=True):
                number_of_notes = st.slider(
                    'Number of Notes',
                    min_value=12, max_value=36,
                    value=int(default_params["Pedals"][0]["number_of_notes_g"]),
                    step=1,
                    help="Total number of notes (AGO standard pattern will be auto-generated)"
                )

                short_pedal_width = st.slider(
                    'Short Pedal Width (mm)',
                    min_value=20.0, max_value=40.0,
                    value=float(default_params["Pedals"][1]["short_pedal_width_g"]),
                    step=0.5,
                    help="Width of short (natural) pedals - 1 inch cross-section"
                )

                tall_pedal_width = st.slider(
                    'Tall Pedal Width (mm)',
                    min_value=20.0, max_value=40.0,
                    value=float(default_params["Pedals"][2]["tall_pedal_width_g"]),
                    step=0.5,
                    help="Width of tall (sharp/flat) pedals - 1 inch cross-section"
                )

                short_pedal_length = st.slider(
                    'Short Pedal Length (mm)',
                    min_value=600, max_value=800,
                    value=int(default_params["Pedals"][3]["short_pedal_length_g"]),
                    step=10,
                    help="Length of short pedals (extending forward)"
                )

                tall_pedal_length = st.slider(
                    'Tall Pedal Length (mm)',
                    min_value=600, max_value=800,
                    value=int(default_params["Pedals"][4]["tall_pedal_length_g"]),
                    step=10,
                    help="Length of tall pedals (extending forward)"
                )

                pedal_height = st.slider(
                    'Pedal Height (mm)',
                    min_value=100, max_value=250,
                    value=int(default_params["Pedals"][5]["pedal_height_g"]),
                    step=10,
                    help="Height of pedals above base"
                )

                pedal_thickness = st.slider(
                    'Pedal Thickness (mm)',
                    min_value=20.0, max_value=40.0,
                    value=float(default_params["Pedals"][6]["pedal_thickness_g"]),
                    step=0.5,
                    help="Thickness of each pedal cross-section (1 inch for short, 2 inch for tall)"
                )

                pedal_spacing = st.slider(
                    'Pedal Spacing (mm)',
                    min_value=1, max_value=10,
                    value=int(default_params["Pedals"][7]["pedal_spacing_g"]),
                    step=1,
                    help="Gap between pedals"
                )

            with st.expander("Base & Frame", expanded=False):
                base_height = st.slider(
                    'Base Height (mm)',
                    min_value=50, max_value=200,
                    value=int(default_params["Base"][0]["base_height_g"]),
                    step=10,
                    help="Height of the base frame"
                )

                base_depth = st.slider(
                    'Base Depth (mm)',
                    min_value=100, max_value=300,
                    value=int(default_params["Base"][1]["base_depth_g"]),
                    step=10,
                    help="Depth of the base frame from front"
                )

                lateral_board_height = st.slider(
                    'Lateral Board Height (mm)',
                    min_value=150, max_value=400,
                    value=int(default_params["Base"][2]["lateral_board_height_g"]),
                    step=10,
                    help="Height of lateral side panels"
                )

            with st.expander("Enclosure Frame", expanded=True):
                frame_side_height = st.slider(
                    'Side Board Height (mm)',
                    min_value=50, max_value=200,
                    value=int(default_params["Frame"][0]["frame_side_height_g"]),
                    step=10,
                    help="Height of the side cheek boards"
                )

                frame_side_depth = st.slider(
                    'Side Board Depth (mm)',
                    min_value=0, max_value=900,
                    value=int(default_params["Frame"][1]["frame_side_depth_g"]),
                    step=10,
                    help="Depth of side boards (0 = auto-calculate from pedal length)"
                )

                frame_back_height = st.slider(
                    'Back Board Height (mm)',
                    min_value=0, max_value=200,
                    value=int(default_params["Frame"][2]["frame_back_height_g"]),
                    step=10,
                    help="Height of back board (0 = no back board)"
                )

                frame_back_depth = st.slider(
                    'Back Board Depth (mm)',
                    min_value=20, max_value=150,
                    value=int(default_params["Frame"][3]["frame_back_depth_g"]),
                    step=10,
                    help="Depth/thickness of back board area"
                )

                frame_front_height = st.slider(
                    'Front Board Height (mm)',
                    min_value=0, max_value=100,
                    value=int(default_params["Frame"][4]["frame_front_height_g"]),
                    step=5,
                    help="Height of front board (0 = no front board)"
                )

            with st.expander("Sharp Pedal Caps", expanded=True):
                sharp_cap_length_end = st.slider(
                    'Cap Length at Ends (mm)',
                    min_value=50, max_value=200,
                    value=int(default_params["Frame"][5]["sharp_cap_length_end_g"]),
                    step=10,
                    help="Length of caps at the left/right ends of the pedalboard"
                )

                sharp_cap_length_middle = st.slider(
                    'Cap Length at Middle (mm)',
                    min_value=50, max_value=200,
                    value=int(default_params["Frame"][6]["sharp_cap_length_middle_g"]),
                    step=10,
                    help="Length of caps in the middle of the pedalboard"
                )

                sharp_cap_arc = st.slider(
                    'Arc Curvature',
                    min_value=0.0, max_value=1.0,
                    value=float(default_params["Frame"][7]["sharp_cap_arc_g"]),
                    step=0.1,
                    help="0 = linear V-shape, 1 = smooth parabolic arc"
                )

                sharp_cap_height_ratio = st.slider(
                    'Cap Height (x pedal thickness)',
                    min_value=1.0, max_value=4.0,
                    value=float(default_params["Frame"][8]["sharp_cap_height_ratio_g"]),
                    step=0.25,
                    help="Cap height as a multiple of pedal thickness"
                )

                sharp_cap_notch_height = st.slider(
                    'Notch Min Height Ratio',
                    min_value=0.0, max_value=1.0,
                    value=float(default_params["Frame"][9]["sharp_cap_notch_height_g"]),
                    step=0.05,
                    help="Height at back of cap as ratio of full height (0.75 = 75%)"
                )

                sharp_cap_notch_width = st.slider(
                    'Notch Start Position Ratio',
                    min_value=0.0, max_value=1.0,
                    value=float(default_params["Frame"][10]["sharp_cap_notch_width_g"]),
                    step=0.05,
                    help="Where notch starts as ratio of cap length (0.75 = starts at 75%)"
                )

                sharp_cap_color = st.checkbox(
                    'Add Dark Caps to Sharp Pedals',
                    value=default_params["Frame"][11]["sharp_cap_color_g"],
                    help="Add colored end caps to sharp/flat pedals"
                )

        # DISPLAY OPTIONS (exclude pedalboard)
        if console_type != "pedalboard":
            with st.expander("Display Options", expanded=False):
                show_dimensions = st.checkbox(
                    'Show Dimensions on Boards',
                    value=False,
                    help="Extrude dimension text (WxHxT) on all board surfaces"
                )

        # EXPORT SETTINGS
        st.divider()
        with st.expander("Export Settings", expanded=False):
            quality_value = st.select_slider(
                'Surface Quality',
                options=[t.name.lower() for t in Tessellation],
                value='medium',
                help="Quality of exported mesh surfaces"
            )

    # MAIN CONTENT AREA

    # Build parameters dictionary based on console type
    if console_type == "vertical":
        parameters = {
            "General_and_base": [
                {"organ_internal_width_g": organ_internal_width},
                {"general_board_thickness_g": general_board_thickness},
                {"base_height_g": base_height},
                {"base_depth_g": base_depth},
                {"base_front_distance_g": base_front_distance},
                {"general_board_offset_g": general_board_offset},
                {"general_feet_thickness_g": general_feet_thickness},
                {"note_stand_height_g": note_stand_height},
                {"note_stand_angle_g": note_stand_angle},
                {"note_shelf_height_g": note_shelf_height}
            ],
            "Keyboard": [
                {"keyboard_width_g": keyboard_width},
                {"keyboard_depth_g": keyboard_depth},
                {"keyboard_height_g": keyboard_height},
                {"keyboard_offset_g": keyboard_offset}
            ],
            "Speakers": [
                {"front_speaker_width_g": front_speaker_width},
                {"front_speaker_height_g": front_speaker_height},
                {"side_speaker_width_g": side_speaker_width},
                {"side_speaker_height_g": side_speaker_height},
                {"enable_lateral_speaker_holes_g": enable_lateral_speaker_holes}
            ],
            "Volume_pedals": [
                {"volume_pedals_width_g": volume_pedals_width},
                {"volume_pedals_height_g": volume_pedals_height},
                {"volume_pedals_number_g": volume_pedals_number},
                {"volume_pedals_spacing_g": volume_pedals_spacing},
                {"volume_pedals_hole_start_height_g": volume_pedals_hole_start_height}
            ],
            "Knobs": [
                {"enable_knob_holes_g": enable_knob_holes},
                {"knob_columns_g": knob_columns},
                {"knob_rows_g": knob_rows},
                {"knob_diameter_g": knob_diameter},
                {"knob_vertical_spacing_g": knob_vertical_spacing},
                {"knob_horizontal_spacing_g": knob_horizontal_spacing},
                {"knob_stagger_offset_g": knob_stagger_offset},
                {"knob_margin_top_g": knob_margin_top},
                {"knob_margin_side_g": knob_margin_side}
            ],
            "Display": [
                {"show_dimensions_g": show_dimensions}
            ]
        }
    elif console_type == "normal":
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
                {"volume_pedals_spacing_g": volume_pedals_spacing},
                {"volume_pedals_hole_start_height_g": volume_pedals_hole_start_height}
            ],
            "Top": [
                {"top_depth_g": top_depth},
                {"top_height_g": top_height},
                {"top_notch_start_x_g": top_notch_start_x},
                {"top_notch_start_y_g": top_notch_start_y}
            ],
            "Display": [
                {"show_dimensions_g": show_dimensions}
            ]
        }
    elif console_type == "bench":
        parameters = {
            "General_and_base": [
                {"organ_internal_width_g": organ_internal_width},
                {"general_board_thickness_g": general_board_thickness},
                {"base_height_g": base_height},
                {"base_depth_g": base_depth},
                {"base_front_distance_g": base_front_distance},
                {"general_board_offset_g": general_board_offset},
                {"general_feet_thickness_g": general_feet_thickness}
            ],
            "Bench": [
                {"bench_depth_g": bench_depth},
                {"bench_height_g": bench_height},
                {"bench_length_g": bench_length},
                {"bench_shelf_height_g": bench_shelf_height}
            ],
            "Display": [
                {"show_dimensions_g": show_dimensions}
            ]
        }
    else:  # pedalboard
        parameters = {
            "General": [
                {"general_board_thickness_g": general_board_thickness},
                {"general_board_offset_g": general_board_offset}
            ],
            "Pedals": [
                {"number_of_notes_g": number_of_notes},
                {"short_pedal_width_g": short_pedal_width},
                {"tall_pedal_width_g": tall_pedal_width},
                {"short_pedal_length_g": short_pedal_length},
                {"tall_pedal_length_g": tall_pedal_length},
                {"pedal_height_g": pedal_height},
                {"pedal_thickness_g": pedal_thickness},
                {"pedal_spacing_g": pedal_spacing}
            ],
            "Base": [
                {"base_height_g": base_height},
                {"base_depth_g": base_depth},
                {"lateral_board_height_g": lateral_board_height}
            ],
            "Frame": [
                {"frame_side_height_g": frame_side_height},
                {"frame_side_depth_g": frame_side_depth},
                {"frame_back_height_g": frame_back_height},
                {"frame_back_depth_g": frame_back_depth},
                {"frame_front_height_g": frame_front_height},
                {"sharp_cap_length_end_g": sharp_cap_length_end},
                {"sharp_cap_length_middle_g": sharp_cap_length_middle},
                {"sharp_cap_arc_g": sharp_cap_arc},
                {"sharp_cap_height_ratio_g": sharp_cap_height_ratio},
                {"sharp_cap_notch_height_g": sharp_cap_notch_height},
                {"sharp_cap_notch_width_g": sharp_cap_notch_width},
                {"sharp_cap_color_g": sharp_cap_color}
            ]
        }

    # VISUALIZATION SECTION
    console_names = {"normal": "Normal", "vertical": "Vertical", "bench": "Bench", "pedalboard": "Pedalboard"}
    st.header(f"{console_names[console_type]} Console Preview")

    # Initialize variables
    file_path_gltf = None
    file_path_step = None
    file_path_csv = None
    file_path_dxf = None

    # Generate files for visualization
    try:
        file_path_gltf, file_path_csv, file_path_dxf = generate_and_export_console_cached(
            console_type=console_type,
            parameters_dict=parameters,
            file_format="gltf",
            tessellation=quality_value
        )

        # Generate STEP file separately for download
        file_path_step, _, _ = generate_and_export_console_cached(
            console_type=console_type,
            parameters_dict=parameters,
            file_format="step",
            tessellation=quality_value
        )

        # Generate the 3D model for technical drawing
        if console_type == "normal":
            console_module = console_normal
        elif console_type == "vertical":
            console_module = console_vertical
        elif console_type == "bench":
            console_module = console_bench
        else:
            console_module = console_pedalboard

        console_model = console_module.generate_console(parameters)

    except Exception as e:
        st.error(f"Failed to generate model: {str(e)}")
        console_model = None

    # Create tabs for 3D View and Technical Drawing
    tab_3d, tab_drawing = st.tabs(["3D View", "Technical Drawing"])

    # 3D VIEW TAB
    with tab_3d:
        try:
            # Find wood texture for Three.js viewer
            wood_texture_path = find_wood_texture()

            # Create and display Three.js viewer
            viewer_html = create_threejs_gltf_viewer(
                gltf_file_path=file_path_gltf,
                wood_texture_path=wood_texture_path,
                height=600
            )

            # Display the Three.js viewer
            components.html(viewer_html, height=620, scrolling=False)

            # Show texture status
            if wood_texture_path:
                st.success(f"Using wood texture: {os.path.basename(wood_texture_path)}")
            else:
                st.info("No wood texture found - using procedural material")

        except Exception as e:
            st.error(f"Failed to create 3D viewer: {str(e)}")
            st.info("Please check that all required dependencies are installed.")

    # TECHNICAL DRAWING TAB
    with tab_drawing:
        st.subheader("A3 Technical Drawing")
        st.caption("Orthographic views with front, back, top, bottom, left, right, perspective, and exploded views")

        if console_model is not None:
            try:
                # Generate the technical drawing SVG
                svg_content = create_a3_technical_drawing(
                    model=console_model,
                    parameters=parameters,
                    console_type=console_type,
                    title="Organ Console"
                )

                # Display SVG using components.html for better compatibility
                # Wrap SVG in HTML with proper styling
                html_content = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            margin: 0;
                            padding: 10px;
                            background-color: #f0f0f0;
                            display: flex;
                            justify-content: center;
                        }}
                        .svg-container {{
                            background-color: white;
                            border: 1px solid #ddd;
                            border-radius: 5px;
                            padding: 10px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            overflow: auto;
                        }}
                        svg {{
                            max-width: 100%;
                            height: auto;
                        }}
                    </style>
                </head>
                <body>
                    <div class="svg-container">
                        {svg_content}
                    </div>
                </body>
                </html>
                '''
                components.html(html_content, height=500, scrolling=True)

                # Download button for SVG
                st.download_button(
                    label="Download Technical Drawing (SVG)",
                    data=svg_content,
                    file_name=f"organ_console_{console_type}_technical_drawing.svg",
                    mime="image/svg+xml",
                    help="Download the A3 technical drawing as SVG"
                )

            except Exception as e:
                st.error(f"Failed to generate technical drawing: {str(e)}")
                st.info("Technical drawing generation requires all model parts to be valid.")
        else:
            st.warning("Model not available for technical drawing generation.")

    # DOWNLOAD SECTION
    st.subheader("Download Files")

    # Create download buttons in columns
    download_col1, download_col2, download_col3 = st.columns(3)

    with download_col1:
        try:
            with open(file_path_gltf, 'rb') as gltf_file:
                st.download_button(
                    label="Download GLTF",
                    data=gltf_file,
                    file_name=f"organ_console_{console_type}.gltf",
                    mime="model/gltf+json",
                    help="3D model for web viewers"
                )
        except:
            st.error("GLTF file not available")

    with download_col2:
        try:
            with open(file_path_step, 'rb') as step_file:
                st.download_button(
                    label="Download STEP",
                    data=step_file,
                    file_name=f"organ_console_{console_type}.step",
                    mime="application/step",
                    help="CAD file for engineering software"
                )
        except:
            st.error("STEP file not available")

    with download_col3:
        try:
            with open(file_path_csv, 'rb') as csv_file:
                st.download_button(
                    label="Download CSV",
                    data=csv_file,
                    file_name=f"organ_console_{console_type}_cutlist.csv",
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
                        label="Download DXF",
                        data=dxf_file,
                        file_name=f"organ_console_{console_type}_profiles.dxf",
                        mime="application/dxf",
                        help="2D profiles for CNC cutting"
                    )
            except:
                st.error("DXF file not available")

    # CUTTING LIST PREVIEW
    st.subheader("Cutting List Preview")

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


if __name__ == "__main__":
    main()
