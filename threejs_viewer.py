"""
Three.js Viewer Module

This module handles HTML/Three.js rendering and visualization for the organ cabinet project.
Creates interactive 3D viewers with wood materials and lighting.

Usage:
    from threejs_viewer import create_threejs_gltf_viewer, find_wood_texture
    
    # Create a viewer for a GLTF file
    wood_texture = find_wood_texture()
    viewer_html = create_threejs_gltf_viewer(
        gltf_file_path="model.gltf",
        wood_texture_path=wood_texture,
        height=500
    )
    
    # Display in Streamlit
    import streamlit.components.v1 as components
    components.html(viewer_html, height=520, scrolling=False)
"""

import os
import json
import base64
import glob


def encode_local_image(file_path):
    """
    Load local image file and encode as base64 data URI.
    
    Args:
        file_path: Path to the image file
    
    Returns:
        str: Base64 data URI string, or None if failed
    """
    try:
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
        try:
            import streamlit as st
            st.warning(f"Failed to load local texture: {str(e)}")
        except ImportError:
            print(f"Failed to load local texture: {str(e)}")
        return None


def find_wood_texture():
    """
    Find wood texture file in current directory.
    
    Returns:
        str: Path to wood texture file, or None if not found
    """
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


def get_wood_texture_base64(wood_texture_path):
    """
    Get wood texture as base64 data URI.
    
    Args:
        wood_texture_path: Path to the wood texture file
    
    Returns:
        str: Base64 data URI string, or None if failed
    """
    if not wood_texture_path or not os.path.exists(wood_texture_path):
        return None
    
    try:
        with open(wood_texture_path, 'rb') as f:
            texture_data = f.read()
        
        # Encode as base64
        texture_base64 = base64.b64encode(texture_data).decode('utf-8')
        
        # Determine MIME type
        if wood_texture_path.lower().endswith('.jpg') or wood_texture_path.lower().endswith('.jpeg'):
            mime_type = "image/jpeg"
        elif wood_texture_path.lower().endswith('.png'):
            mime_type = "image/png"
        else:
            mime_type = "image/jpeg"
        
        return f"data:{mime_type};base64,{texture_base64}"
    except Exception as e:
        print(f"Error loading texture: {e}")
        return None


def create_threejs_gltf_viewer(gltf_file_path, wood_texture_path=None, height=500, extra_models=None):
    """
    Create a Three.js GLTF viewer with lacquered wood material and wood type selector.
    
    Args:
        gltf_file_path: Path to the GLTF file
        wood_texture_path: Path to wood texture image (optional)
        height: Height of the viewer in pixels
    
    Returns:
        str: HTML string containing the complete Three.js viewer
    """
    
    # Read GLTF file content and handle binary data
    with open(gltf_file_path, 'r') as f:
        gltf_json = json.load(f)
    
    # Check if there's a separate .bin file and embed it
    gltf_dir = os.path.dirname(gltf_file_path)
    bin_data_uri = None
    
    if 'buffers' in gltf_json:
        for buffer in gltf_json['buffers']:
            if 'uri' in buffer and buffer['uri'].endswith('.bin'):
                bin_file_path = os.path.join(gltf_dir, buffer['uri'])
                if os.path.exists(bin_file_path):
                    with open(bin_file_path, 'rb') as bin_file:
                        bin_data = bin_file.read()
                    bin_base64 = base64.b64encode(bin_data).decode('utf-8')
                    bin_data_uri = f"data:application/octet-stream;base64,{bin_base64}"
                    # Update the buffer to use the data URI
                    buffer['uri'] = bin_data_uri
    
    # Convert the modified GLTF JSON to base64
    gltf_json_str = json.dumps(gltf_json)
    gltf_base64 = base64.b64encode(gltf_json_str.encode('utf-8')).decode('utf-8')

    # Process extra models for combined view
    extra_model_calls = ""
    if extra_models:
        for em in extra_models:
            em_path = em['gltf_path']
            with open(em_path, 'r') as f:
                em_json = json.load(f)
            em_dir = os.path.dirname(em_path)
            if 'buffers' in em_json:
                for buf in em_json['buffers']:
                    if 'uri' in buf and buf['uri'].endswith('.bin'):
                        bin_path = os.path.join(em_dir, buf['uri'])
                        if os.path.exists(bin_path):
                            with open(bin_path, 'rb') as bf:
                                bd = bf.read()
                            buf['uri'] = f"data:application/octet-stream;base64,{base64.b64encode(bd).decode()}"
            em_b64 = base64.b64encode(json.dumps(em_json).encode()).decode()
            em_offset = em.get('offset_z', 0)
            em_rotate_y = em.get('rotate_y', 0)
            extra_model_calls += f'\n                loadExtraModel("{em_b64}", {em_offset}, {em_rotate_y});'

    # Handle local wood texture - get as base64
    wood_texture_uri = get_wood_texture_base64(wood_texture_path)
    
    # Create the HTML template with improved Three.js viewer
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lacquered Wood GLTF Viewer with Wood Types</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: #0e1117;
                font-family: Arial, sans-serif;
                overflow: hidden;
            }}
            #container {{
                width: 100%;
                height: {height}px;
                position: relative;
            }}
            #loading {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: #ffffff;
                font-size: 1.1em;
                z-index: 100;
                text-align: center;
            }}
            #menu {{
                position: absolute;
                top: 10px;
                left: 10px;
                background: rgba(0, 0, 0, 0.8);
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
                z-index: 200;
                color: white;
                font-size: 0.9em;
                min-width: 200px;
            }}
            .control {{
                margin-bottom: 10px;
            }}
            .control label {{
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }}
            .slider, select {{
                width: 100%;
                padding: 5px;
                border-radius: 4px;
                border: 1px solid #555;
                background: #333;
                color: white;
            }}
            .controls {{
                position: absolute;
                bottom: 10px;
                left: 10px;
                background: rgba(0,0,0,0.7);
                padding: 10px;
                border-radius: 8px;
                font-size: 0.8em;
                color: #ffffff;
                z-index: 200;
            }}
            .error {{
                color: #ff6b6b;
                background: rgba(255, 0, 0, 0.1);
                padding: 15px;
                border-radius: 8px;
                margin: 20px;
            }}
        #lacquer-capsule {{
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 200;
            font-family: Arial, sans-serif;
            font-size: 11px;
        }}
        #lacquer-toggle-btn {{
            background: rgba(20,12,4,0.85);
            border: 1px solid #c8922a;
            color: #c8922a;
            padding: 5px 12px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 11px;
            font-weight: bold;
            display: block;
            text-align: right;
            white-space: nowrap;
        }}
        #lacquer-toggle-btn:hover {{ background: rgba(40,24,8,0.9); }}
        #lacquer-panel {{
            display: none;
            background: rgba(10,6,2,0.88);
            border: 1px solid #5a3c10;
            border-radius: 8px;
            padding: 10px 13px;
            margin-top: 5px;
            min-width: 200px;
            color: #ddd;
            line-height: 1.8;
            max-height: calc(100vh - 80px);
            overflow-y: auto;
        }}
        #lacquer-panel label {{ display:block; font-size:10px; color:#aaa; margin-top:6px; }}
        #lacquer-panel input[type=range] {{ width:100%; accent-color:#c8922a; margin:1px 0; }}
        #lacquer-panel select {{ width:100%; background:#1e1e1e; color:#ddd; border:1px solid #555; padding:2px 4px; border-radius:4px; font-size:10px; }}
        .cap-section {{ color:#c8922a; font-size:10px; font-weight:bold; margin-top:8px; border-top:1px solid #333; padding-top:5px; }}
        .cap-check {{ display:flex; align-items:center; gap:6px; cursor:pointer; color:#ddd; font-size:11px; margin-bottom:4px; }}
        .cap-check input {{ accent-color:#c8922a; }}
        .tex-dots {{ font-size:9px; color:#888; display:flex; gap:5px; margin:1px 0 3px; }}
        .dot {{ width:6px; height:6px; border-radius:50%; background:#444; display:inline-block; }}
        .dot.ok {{ background:#5a5; }} .dot.err {{ background:#a44; }} .dot.loading {{ background:#c8922a; }}
        </style>
    </head>
    <body>
        <div id="container">
            <div id="loading">
                <div>Loading Lacquered Wood Model...</div>
                <div style="font-size: 0.9em; margin-top: 10px;">Applying materials...</div>
            </div>
            
            <div id="lacquer-capsule">
              <button id="lacquer-toggle-btn">&#9654; Render</button>
              <div id="lacquer-panel">
                <div class="cap-check">
                  <input type="checkbox" id="lacquer" checked>
                  <span>Lacquer finish</span>
                </div>
                <div class="cap-section">INSTRUMENT</div>
                <label>Texture</label>
                <select id="woodTexture">
                  <option value="oak_veneer_ph" selected>Oak Veneer</option>
                  <option value="fine_grained_wood">Fine Grain Wood</option>
                  <option value="wood_table">Wood Table</option>
                  <option value="wood_table_worn">Wood Table Worn</option>
                  <option value="rosewood_veneer1">Rosewood Veneer</option>
                  <option value="kitchen_wood">Kitchen Wood</option>
                  <option value="stained_pine">Stained Pine</option>
                  <option value="dark_wood">Dark Wood</option>
                  <option value="plywood">Plywood</option>
                  <option value="brown_planks_05">Brown Planks</option>
                  <option value="hardwood2_diffuse">Classic Hardwood</option>
                  <option value="local" {"selected" if wood_texture_uri else ""}>Local Wood</option>
                </select>
                <div class="tex-dots"><span class="dot" id="i-d"></span>diff <span class="dot" id="i-n"></span>nor <span class="dot" id="i-r"></span>rough</div>
                <label>Grain scale <span id="gsv">2.0</span></label>
                <input type="range" id="gs" min="0.3" max="10" step="0.1" value="2.0">
                <div class="cap-section">FLOOR</div>
                <label>Texture</label>
                <select id="floorTexture">
                  <option value="herringbone_parquet" selected>Herringbone Parquet</option>
                  <option value="rectangular_parquet">Rectangular Parquet</option>
                  <option value="diagonal_parquet">Diagonal Parquet</option>
                  <option value="wood_floor">Wood Floor</option>
                  <option value="wood_floor_deck">Wood Floor Deck</option>
                  <option value="plank_flooring">Plank Flooring</option>
                  <option value="plank_flooring_02">Plank Flooring 2</option>
                  <option value="old_wood_floor">Old Wood Floor</option>
                  <option value="laminate_floor">Laminate Floor</option>
                  <option value="hardwood2_tjs">Classic Hardwood</option>
                </select>
                <div class="tex-dots"><span class="dot" id="f-d"></span>diff <span class="dot" id="f-n"></span>nor <span class="dot" id="f-r"></span>rough</div>
                <label>Floor scale <span id="fgsv">4.0</span></label>
                <input type="range" id="fgs" min="0.5" max="20" step="0.5" value="4.0">
                <div class="cap-section">FINISH</div>
                <label>Roughness <span id="rv">0.30</span></label>
                <input type="range" id="rough" min="0" max="1" step="0.01" value="0.30">
                <label>Clearcoat <span id="ccv">0.90</span></label>
                <input type="range" id="cc" min="0" max="1" step="0.01" value="0.90">
                <label>CC Roughness <span id="ccrv">0.08</span></label>
                <input type="range" id="ccr" min="0" max="1" step="0.01" value="0.08">
                <label>Normal strength <span id="nsv">0.70</span></label>
                <input type="range" id="ns" min="0" max="4" step="0.05" value="0.70">
                <label>Env intensity <span id="emiv">1.20</span></label>
                <input type="range" id="emi" min="0" max="4" step="0.05" value="1.20">
                <div class="cap-section">FLOOR FINISH</div>
                <label>Roughness <span id="frv">0.25</span></label>
                <input type="range" id="fr" min="0" max="1" step="0.01" value="0.25">
                <label>Clearcoat <span id="fccv">0.95</span></label>
                <input type="range" id="fcc" min="0" max="1" step="0.01" value="0.95">
                <label>CC Roughness <span id="fccrv">0.05</span></label>
                <input type="range" id="fccr" min="0" max="1" step="0.01" value="0.05">
                <div class="cap-section">LIGHTING</div>
                <label>Exposure <span id="expv">1.00</span></label>
                <input type="range" id="expo" min="0.4" max="3" step="0.05" value="1.00">
                <label>Key light <span id="klv">0.118</span></label>
                <input type="range" id="kl" min="0" max="1" step="0.01" value="0.118">
                <label>Fill lights <span id="flv">0.314</span></label>
                <input type="range" id="fl" min="0" max="1" step="0.01" value="0.314">
                <div class="cap-section" style="margin-top:10px;"></div>
                <button id="export-settings-btn" style="width:100%;margin-top:6px;padding:5px;background:#1e1208;border:1px solid #c8922a;border-radius:5px;color:#c8922a;cursor:pointer;font-size:11px;font-weight:bold;">&#11015; Export settings</button>
              </div>
            </div>
            <button id="fullscreen-btn" title="Fullscreen" style="position:absolute;bottom:10px;right:10px;z-index:200;background:rgba(10,6,2,0.80);border:1px solid #5a3c10;color:#c8922a;border-radius:6px;padding:5px 9px;cursor:pointer;font-size:14px;line-height:1;">&#x26F6;</button>
            
            <div class="controls">
                <strong>Controls:</strong><br>
                Mouse: Rotate • Right-click: Pan • Wheel: Zoom<br>
                A: Auto-rotate • R: Reset view
            </div>
        </div>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <script>
            const loading = document.getElementById('loading');
            const container = document.getElementById('container');

            // Scene setup
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x1a1a1a);
            const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            
            // Enhanced renderer settings for better lacquer look
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.0;
            renderer.outputEncoding = THREE.sRGBEncoding;
            
            renderer.setSize(container.clientWidth, container.clientHeight);
            container.appendChild(renderer.domElement);

            // Camera position - positioned to show front-left of instrument (rotated 90° clockwise)
            camera.position.set(-5, 5, -5);

            // Camera controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.enableZoom = true;
            controls.enablePan = true;
            controls.autoRotate = true;
            controls.autoRotateSpeed = 1.0;

            // Hemisphere light with warm tones for church-like ambience - reduced by 65% total (30% + 30% + 30%)
            const hemiLight = new THREE.HemisphereLight(0xffd4a3, 0x0f0e0d, 0.137);
            scene.add(hemiLight);
            
            // Add directional light from above with warmer tone - reduced by 51% total (30% + 30%)
            const dirLight = new THREE.DirectionalLight(0xffcc99, 0.118); // Reduced by additional 30% from 0.168
            dirLight.position.set(0, 10, 0);
            dirLight.castShadow = true;
            dirLight.shadow.camera.top = 10;
            dirLight.shadow.camera.bottom = -10;
            dirLight.shadow.camera.left = -10;
            dirLight.shadow.camera.right = 10;
            scene.add(dirLight);

            // 4 Corner lights setup - positioned at 3 meters high over floor corners
            const bulbGeometry = new THREE.SphereGeometry(0.02, 16, 8);
            const bulbMat = new THREE.MeshStandardMaterial({{
                emissive: 0xffffee,
                emissiveIntensity: 1,
                color: 0x000000
            }});
            
            // Create 4 lights for the corners (floor is 20x20, so corners are at ±10, ±10)
            const bulbLights = [];
            const lightPositions = [
                {{ x: -8, y: 3.0, z: -8 }}, // Front-left corner
                {{ x: 8, y: 3.0, z: -8 }},  // Front-right corner
                {{ x: -8, y: 3.0, z: 8 }},  // Back-left corner
                {{ x: 8, y: 3.0, z: 8 }}    // Back-right corner
            ];
            
            lightPositions.forEach((pos, index) => {{
                const light = new THREE.PointLight(0xffbb66, 0.314, 100, 2); // Reduced by 51% total (30% + 30%) from 0.64, warmer color
                light.add(new THREE.Mesh(bulbGeometry, bulbMat.clone()));
                light.position.set(pos.x, pos.y, pos.z);
                light.castShadow = true;
                bulbLights.push(light);
                scene.add(light);
            }});

            // Floor material setup with increased reflectivity and enhanced bumpiness
            const floorMat = new THREE.MeshPhysicalMaterial({{
                roughness: 0.25, color: 0xffffff, metalness: 0.0,
                clearcoat: 0.95, clearcoatRoughness: 0.05, envMapIntensity: 1.2
            }});
            
            // Load the actual textures from Three.js examples
            const textureLoader = new THREE.TextureLoader();
            const PH = 'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k';
            const TJS = 'https://threejs.org/examples/textures';
            function phUrl(slug, map) {{ return PH + '/' + slug + '/' + slug + '_' + map + '_1k.jpg'; }}
            const aniso = renderer.capabilities.getMaxAnisotropy();

            function loadMap(url, encoding, dotId, repeat, cb) {{
                const dot = document.getElementById(dotId);
                if (!url) {{ if(dot) dot.className='dot err'; cb(null); return; }}
                if(dot) dot.className='dot loading';
                textureLoader.load(url, function(t) {{
                    t.wrapS = t.wrapT = THREE.RepeatWrapping;
                    t.anisotropy = aniso;
                    if(encoding) t.encoding = encoding;
                    if(repeat) t.repeat.set(repeat, repeat);
                    if(dot) dot.className='dot ok';
                    cb(t);
                }}, undefined, function() {{ if(dot) dot.className='dot err'; cb(null); }});
            }}

            function loadPBRFloor(slug, repeat) {{
                const isTJS = slug === 'hardwood2_tjs';
                const diffUrl = isTJS ? TJS+'/hardwood2_diffuse.jpg' : phUrl(slug,'diff');
                const norUrl  = isTJS ? null : phUrl(slug,'nor_gl');
                const roughUrl= isTJS ? TJS+'/hardwood2_roughness.jpg' : phUrl(slug,'rough');
                loadMap(diffUrl,  THREE.sRGBEncoding, 'f-d', repeat, function(t) {{ floorMat.map=t; floorMat.needsUpdate=true; }});
                loadMap(norUrl,   null,               'f-n', repeat, function(t) {{ floorMat.normalMap=t; floorMat.needsUpdate=true; }});
                loadMap(roughUrl, null,               'f-r', repeat, function(t) {{ floorMat.roughnessMap=t; floorMat.needsUpdate=true; }});
                floorMat.color.setHex(0xffffff);
            }}

            loadPBRFloor('herringbone_parquet', 4.0);
            
            // Use PlaneBufferGeometry exactly like the source
            const floorGeometry = new THREE.PlaneBufferGeometry(20, 20);
            const floorMesh = new THREE.Mesh(floorGeometry, floorMat);
            floorMesh.receiveShadow = true;
            floorMesh.rotation.x = -Math.PI / 2.0;
            scene.add(floorMesh);

            // Environment map for reflections - using a more neutral/indoor environment
            const envTextureLoader = new THREE.CubeTextureLoader();
            const envMap = envTextureLoader.load([
                'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/cube/pisa/px.png',
                'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/cube/pisa/nx.png',
                'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/cube/pisa/py.png',
                'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/cube/pisa/ny.png',
                'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/cube/pisa/pz.png',
                'https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/textures/cube/pisa/nz.png',
            ]);
            scene.environment = envMap;
            
            // Wood textures database (only local override survives; PH slugs handled by loadPBRInstrument)
            const woodTextures = {{
                "local": "{wood_texture_uri or ''}"
            }};

            // UV helper — always regenerate (build123d GLTF exports all-zero UVs)
            function genUVs(geo) {{
                geo.computeBoundingBox();
                if (!geo.attributes.normal) geo.computeVertexNormals();
                const pos = geo.attributes.position, nrm = geo.attributes.normal;
                const box = geo.boundingBox, sz = new THREE.Vector3(); box.getSize(sz);
                const n = pos.count, uvs = new Float32Array(n*2);
                const P = new THREE.Vector3(), N = new THREE.Vector3();
                for (let i=0; i<n; i++) {{
                    P.fromBufferAttribute(pos,i); N.fromBufferAttribute(nrm,i);
                    const ax=Math.abs(N.x), ay=Math.abs(N.y), az=Math.abs(N.z);
                    let u,v;
                    if(ax>=ay&&ax>=az)      {{ u=sz.z>0?(P.z-box.min.z)/sz.z:0; v=sz.y>0?(P.y-box.min.y)/sz.y:0; }}
                    else if(ay>=ax&&ay>=az) {{ u=sz.x>0?(P.x-box.min.x)/sz.x:0; v=sz.z>0?(P.z-box.min.z)/sz.z:0; }}
                    else                   {{ u=sz.x>0?(P.x-box.min.x)/sz.x:0; v=sz.y>0?(P.y-box.min.y)/sz.y:0; }}
                    uvs[i*2]=u; uvs[i*2+1]=v;
                }}
                geo.setAttribute('uv', new THREE.BufferAttribute(uvs,2));
                geo.attributes.uv.needsUpdate=true;
            }}

            // Current PBR sets for instrument
            let instDiff=null, instNor=null, instRough=null;
            let currentInstSlug = 'oak_veneer_ph';

            function loadPBRInstrument(slug) {{
                currentInstSlug = slug;
                const isTJS = slug === 'hardwood2_diffuse';
                const isLocal = slug === 'local';
                const diffUrl  = isLocal ? (woodTextures.local||'') : isTJS ? TJS+'/hardwood2_diffuse.jpg' : phUrl(slug,'diff');
                const norUrl   = (isLocal||isTJS) ? null : phUrl(slug,'nor_gl');
                const roughUrl = (isLocal||isTJS) ? null : phUrl(slug,'rough');
                loadMap(diffUrl,  THREE.sRGBEncoding, 'i-d', parseFloat(document.getElementById('gs').value), function(t) {{
                    instDiff=t; applyInstTextures();
                }});
                loadMap(norUrl,   null, 'i-n', parseFloat(document.getElementById('gs').value), function(t) {{
                    instNor=t; applyInstTextures();
                }});
                loadMap(roughUrl, null, 'i-r', parseFloat(document.getElementById('gs').value), function(t) {{
                    instRough=t; applyInstTextures();
                }});
            }}

            function applyInstTextures() {{
                const ns = parseFloat(document.getElementById('ns').value);
                modelMaterials.forEach(function(m) {{
                    m.map          = instDiff  || null;
                    m.normalMap    = instNor   || null;
                    m.roughnessMap = instRough || null;
                    m.color.setHex(instDiff ? 0xffffff : 0xA0722A);
                    if(m.normalMap) m.normalScale.set(ns,ns);
                    m.needsUpdate = true;
                }});
            }}

            function applyAllWoodProps() {{
                const r=parseFloat(document.getElementById('rough').value);
                const cc=parseFloat(document.getElementById('cc').value);
                const ccr=parseFloat(document.getElementById('ccr').value);
                const ns=parseFloat(document.getElementById('ns').value);
                const emi=parseFloat(document.getElementById('emi').value);
                modelMaterials.forEach(function(m) {{
                    m.roughness=r; m.clearcoat=cc; m.clearcoatRoughness=ccr;
                    m.envMapIntensity=emi;
                    if(m.normalMap) m.normalScale.set(ns,ns);
                    m.needsUpdate=true;
                }});
            }}

            function applyFloorProps() {{
                floorMat.roughness          = parseFloat(document.getElementById('fr').value);
                floorMat.clearcoat          = parseFloat(document.getElementById('fcc').value);
                floorMat.clearcoatRoughness = parseFloat(document.getElementById('fccr').value);
                floorMat.envMapIntensity    = parseFloat(document.getElementById('emi').value);
                if(floorMat.normalMap) floorMat.normalScale.set(parseFloat(document.getElementById('ns').value), parseFloat(document.getElementById('ns').value));
                floorMat.needsUpdate = true;
            }}

            // Special materials for non-wood parts (identified by mesh name containing "material:")
            const specialMaterials = {{
                "black": {{
                    color: 0x1a1a1a,
                    metalness: 0.1,
                    roughness: 0.4,
                    clearcoat: 0.3,
                    clearcoatRoughness: 0.2
                }},
                "white": {{
                    color: 0xf5f5f0,
                    metalness: 0.0,
                    roughness: 0.3,
                    clearcoat: 0.5,
                    clearcoatRoughness: 0.1
                }},
                "metal": {{
                    color: 0x888888,
                    metalness: 0.9,
                    roughness: 0.2,
                    clearcoat: 0.0,
                    clearcoatRoughness: 0.0
                }},
                "dark_wood": {{
                    color: 0x3d2817,
                    metalness: 0.0,
                    roughness: 0.3,
                    clearcoat: 0.6,
                    clearcoatRoughness: 0.1
                }},
                "ebony": {{
                    color: 0x1c1c1c,
                    metalness: 0.05,
                    roughness: 0.25,
                    clearcoat: 0.7,
                    clearcoatRoughness: 0.1
                }}
            }};

            // Helper function to check if a mesh should use a special material
            function getSpecialMaterial(meshName) {{
                if (!meshName) return null;
                // Match "material:black", "materialblack", or "materialblack_12" (with numeric suffix)
                // Use [a-zA-Z]+ to capture only letters (not underscores/numbers from GLTF suffixes)
                const match = meshName.match(/material:?([a-zA-Z]+)/);
                if (match && specialMaterials[match[1]]) {{
                    console.log('✓ Found special material:', match[1], 'for mesh:', meshName);
                    return specialMaterials[match[1]];
                }}
                return null;
            }}

            // Global variables for model texture management
            let currentModel = null;
            let modelMaterials = [];
            let mainModelScale = 1;
            const mainCenterOffset = new THREE.Vector3();
            const extraModelsList = [];

            // Create fallback wood material (warm oak color)
            function createWoodMaterial(textureUrl = null) {{
                const material = new THREE.MeshPhysicalMaterial({{
                    color: textureUrl ? 0xffffff : 0xA0722A, // White for texture, oak color for fallback
                    metalness: 0.0,
                    roughness: 0.2,
                    clearcoat: 0.8,
                    clearcoatRoughness: 0.1,
                    envMapIntensity: 1.0,
                    reflectivity: 0.8
                }});

                if (textureUrl && textureUrl !== '') {{
                    textureLoader.load(textureUrl, function(texture) {{
                        texture.wrapS = THREE.RepeatWrapping;
                        texture.wrapT = THREE.RepeatWrapping;
                        texture.repeat.set(2, 2);
                        texture.anisotropy = 4;
                        material.map = texture;
                        material.needsUpdate = true;
                        console.log('✅ Texture loaded and applied:', textureUrl);
                    }}, undefined, function(error) {{
                        console.warn('❌ Failed to load texture:', textureUrl, error);
                    }});
                }}

                return material;
            }}

            // Apply texture to existing materials (better approach)
            function applyTextureToModel(model, texture) {{
                modelMaterials = []; // Clear previous materials tracking
                model.traverse((child) => {{
                    if (child.isMesh) {{
                        // Always regenerate UVs (build123d GLTF exports all-zero UV attribute)
                        genUVs(child.geometry);
                        
                        // Keep the existing material but update its properties for wood look
                        const material = child.material;
                        
                        // Convert to MeshPhysicalMaterial if it isn't already
                        if (!(material instanceof THREE.MeshPhysicalMaterial)) {{
                            const newMaterial = new THREE.MeshPhysicalMaterial({{
                                color: 0xffffff,
                                metalness: 0.0,
                                roughness: 0.2,
                                clearcoat: 0.8,
                                clearcoatRoughness: 0.1,
                                envMapIntensity: 1.0,
                                reflectivity: 0.8
                            }});
                            child.material = newMaterial;
                        }}
                        
                        // Apply texture if provided
                        if (texture) {{
                            child.material.map = texture;
                            child.material.map.needsUpdate = true;
                            child.material.color.setHex(0xffffff); // White base for texture
                        }} else {{
                            // Use warm oak color as fallback and remove texture
                            child.material.map = null;
                            child.material.color.setHex(0xA0722A);
                        }}
                        
                        // Set wood material properties with fixed values
                        child.material.metalness = 0.0;
                        child.material.roughness = 0.2;
                        child.material.clearcoat = 0.8;
                        child.material.clearcoatRoughness = 0.1;
                        child.material.envMapIntensity = 1.0;
                        child.material.reflectivity = 0.8;
                        child.material.needsUpdate = true;
                        
                        child.castShadow = true;
                        child.receiveShadow = true;
                        modelMaterials.push(child.material);
                        console.log('🎨 Material updated for mesh:', child.name || 'unnamed');
                    }}
                }});
                console.log('🎨 Total meshes updated:', modelMaterials.length);
            }}

            // Apply material properties only (for sliders)
            function updateMaterialProperties() {{
                modelMaterials.forEach(material => {{
                    material.needsUpdate = true;
                }});
            }}

            // Load an extra model, center it like the main model, then apply offset and rotation
            function loadExtraModel(gltfBase64, offsetZ, rotateY) {{
                const extraLoader = new THREE.GLTFLoader();
                try {{
                    const binStr = atob(gltfBase64);
                    const bytes = new Uint8Array(binStr.length);
                    for (let i = 0; i < binStr.length; i++) bytes[i] = binStr.charCodeAt(i);
                    const blob = new Blob([bytes], {{ type: 'model/gltf+json' }});
                    const url = URL.createObjectURL(blob);
                    extraLoader.load(url, function(gltf) {{
                        const extraModel = gltf.scene;
                        // Center and scale like the main model, then shift by offsetZ
                        const box = new THREE.Box3().setFromObject(extraModel);
                        const center = box.getCenter(new THREE.Vector3());
                        extraModel.scale.setScalar(mainModelScale);
                        extraModel.position.sub(center.multiplyScalar(mainModelScale));
                        extraModel.position.y = 0;
                        extraModel.position.z += offsetZ;
                        if (rotateY) extraModel.rotation.y = rotateY;
                        scene.add(extraModel);
                        extraModelsList.push(extraModel);
                        URL.revokeObjectURL(url);
                        // Apply wood texture using current PBR instrument textures
                        applyTextureToModel(extraModel, instDiff);
                        console.log('✅ Extra model loaded, Z offset:', offsetZ);
                    }}, undefined, function(err) {{
                        console.error('❌ Extra model load failed:', err);
                    }});
                }} catch(e) {{
                    console.error('❌ Extra model processing failed:', e);
                }}
            }}

            // Load GLTF model
            const loader = new THREE.GLTFLoader();

            try {{
                // Convert base64 to blob URL for GLTF loader
                const binaryString = atob("{gltf_base64}");
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {{
                    bytes[i] = binaryString.charCodeAt(i);
                }}
                const blob = new Blob([bytes], {{ type: 'model/gltf+json' }});
                const gltfUrl = URL.createObjectURL(blob);

                loader.load(
                    gltfUrl,
                    function(gltf) {{
                        console.log('✅ GLTF loaded successfully');
                        
                        currentModel = gltf.scene;
                        
                        // Center and scale the model
                        const box = new THREE.Box3().setFromObject(currentModel);
                        const center = box.getCenter(new THREE.Vector3());
                        const size = box.getSize(new THREE.Vector3());
                        
                        const maxDim = Math.max(size.x, size.y, size.z);
                        const scale = 4 / maxDim;
                        mainModelScale = scale;
                        currentModel.scale.setScalar(scale);
                        currentModel.position.sub(center.multiplyScalar(scale));
                        currentModel.position.y = 0;
                        mainCenterOffset.copy(currentModel.position);
                        
                        // Apply initial wood texture — Oak Veneer (full PBR from Poly Haven)
                        const initialTextureUrl = woodTextures.local && woodTextures.local !== ''
                            ? woodTextures.local
                            : phUrl('oak_veneer_01', 'diff');

                        // Load initial texture and apply to model
                        textureLoader.load(initialTextureUrl, function(myTexture) {{
                            myTexture.wrapS = THREE.RepeatWrapping;
                            myTexture.wrapT = THREE.RepeatWrapping;
                            myTexture.encoding = THREE.sRGBEncoding;
                            myTexture.repeat.set(2, 2);
                            myTexture.anisotropy = aniso;
                            instDiff = myTexture;
                            
                            // Apply texture using your recommended pattern
                            currentModel.traverse(function(child) {{
                                if (child.isMesh) {{
                                    // Debug: log all mesh names to understand structure
                                    console.log('DEBUG mesh:', child.name, 'parent:', child.parent ? child.parent.name : 'none');

                                    // Check if this mesh OR its parent should use a special material
                                    // GLTFLoader sometimes puts the name on the parent node, not the mesh
                                    let meshName = child.name;
                                    if (!meshName && child.parent) {{
                                        meshName = child.parent.name;
                                    }}

                                    const specialMat = getSpecialMaterial(meshName);

                                    if (specialMat) {{
                                        // Use special material (no wood texture)
                                        const newMaterial = new THREE.MeshPhysicalMaterial({{
                                            color: specialMat.color,
                                            metalness: specialMat.metalness,
                                            roughness: specialMat.roughness,
                                            clearcoat: specialMat.clearcoat,
                                            clearcoatRoughness: specialMat.clearcoatRoughness,
                                            envMapIntensity: 0.5,
                                            reflectivity: 0.5
                                        }});

                                        child.material = newMaterial;
                                        child.material.needsUpdate = true;
                                        child.castShadow = true;
                                        child.receiveShadow = true;
                                        // Don't add to modelMaterials - wood texture changes won't affect these
                                        console.log('🎨 Special material applied to mesh:', meshName);
                                    }} else {{
                                        // Always regenerate UVs (build123d exports all-zero UV attribute)
                                        genUVs(child.geometry);

                                        // Convert to MeshPhysicalMaterial for lacquer effect
                                        const cc_v  = parseFloat(document.getElementById('cc').value);
                                        const ccr_v = parseFloat(document.getElementById('ccr').value);
                                        const r_v   = parseFloat(document.getElementById('rough').value);
                                        const emi_v = parseFloat(document.getElementById('emi').value);
                                        const newMaterial = new THREE.MeshPhysicalMaterial({{
                                            map: myTexture,
                                            color: 0xffffff,
                                            metalness: 0.0,
                                            roughness: r_v,
                                            clearcoat: cc_v,
                                            clearcoatRoughness: ccr_v,
                                            envMapIntensity: emi_v,
                                        }});

                                        child.material = newMaterial;
                                        child.material.needsUpdate = true;
                                        child.castShadow = true;
                                        child.receiveShadow = true;
                                        modelMaterials.push(child.material);
                                        console.log('🎨 Wood texture applied to mesh:', child.name || 'unnamed');
                                    }}
                                }}
                            }});
                            
                            console.log('✅ Initial wood texture applied successfully');
                            // Load normal and roughness maps for oak veneer
                            loadMap(phUrl('oak_veneer_01','nor_gl'),  null, 'i-n', 2.0, function(t) {{ instNor=t;   applyInstTextures(); }});
                            loadMap(phUrl('oak_veneer_01','rough'),   null, 'i-r', 2.0, function(t) {{ instRough=t; applyInstTextures(); }});
                        }}, undefined, function(error) {{
                            // Fallback to no texture
                            currentModel.traverse(function(child) {{
                                if (child.isMesh) {{
                                    const fallbackMaterial = new THREE.MeshPhysicalMaterial({{
                                        color: 0xA0722A, // Warm oak color
                                        metalness: 0.0,
                                        roughness: 0.2,
                                        clearcoat: 0.8,
                                        clearcoatRoughness: 0.1,
                                        envMapIntensity: 1.0,
                                        reflectivity: 0.8
                                    }});
                                    
                                    child.material = fallbackMaterial;
                                    child.material.needsUpdate = true;
                                    child.castShadow = true;
                                    child.receiveShadow = true;
                                    modelMaterials.push(child.material);
                                }}
                            }});
                            console.log('✅ Fallback oak material applied');
                        }});
                        
                        // Add model to scene
                        scene.add(currentModel);
                        
                        // Position camera for optimal view
                        camera.lookAt(0, 1, 0);
                        controls.target.set(0, 1, 0);
                        controls.update();
                        
                        // Hide loading indicator
                        loading.style.display = 'none';
                        
                        // Clean up blob URL
                        URL.revokeObjectURL(gltfUrl);

                        setupControls();

                        // Load extra models for combined view
                        {extra_model_calls}
                    }},
                    function(xhr) {{
                        const percent = (xhr.loaded / xhr.total * 100).toFixed(0);
                        loading.innerHTML = `
                            <div>Loading Lacquered Wood Model...</div>
                            <div style="font-size: 0.9em; margin-top: 10px;">Progress: ${{percent}}%</div>
                        `;
                    }},
                    function(error) {{
                        console.error('❌ GLTF loading failed:', error);
                        loading.innerHTML = `
                            <div class="error">
                                <strong>Error loading model:</strong><br>
                                ${{error.message || 'Unknown error'}}
                            </div>
                        `;
                    }}
                );
            }} catch (error) {{
                console.error('❌ Failed to process GLTF data:', error);
                loading.innerHTML = `
                    <div class="error">
                        <strong>Error processing model data:</strong><br>
                        ${{error.message}}
                    </div>
                `;
            }}

            // Setup UI controls
            function setupControls() {{
                // Toggle capsule panel
                document.getElementById('lacquer-toggle-btn').addEventListener('click', function() {{
                    const panel = document.getElementById('lacquer-panel');
                    const btn = document.getElementById('lacquer-toggle-btn');
                    if (panel.style.display === 'block') {{
                        panel.style.display = 'none';
                        btn.textContent = '▶ Render';
                    }} else {{
                        panel.style.display = 'block';
                        btn.textContent = '▼ Render';
                    }}
                }});

                // Lacquer finish toggle
                const LACQUER = {{rough:0.30,cc:0.90,ccr:0.08,ns:0.70,emi:1.20,fr:0.25,fcc:0.95,fccr:0.05}};
                const MATTE   = {{rough:0.65,cc:0.00,ccr:0.50,ns:0.80,emi:0.50,fr:0.70,fcc:0.00,fccr:0.50}};
                function applyPreset(p) {{
                    [['rough',p.rough,'rv'],['cc',p.cc,'ccv'],['ccr',p.ccr,'ccrv'],
                     ['ns',p.ns,'nsv'],['emi',p.emi,'emiv'],
                     ['fr',p.fr,'frv'],['fcc',p.fcc,'fccv'],['fccr',p.fccr,'fccrv']].forEach(function(x) {{
                        document.getElementById(x[0]).value = x[1];
                        document.getElementById(x[2]).textContent = x[1].toFixed(2);
                    }});
                    applyAllWoodProps(); applyFloorProps();
                }}
                document.getElementById('lacquer').addEventListener('change', function(e) {{
                    scene.environment = e.target.checked ? envMap : null;
                    applyPreset(e.target.checked ? LACQUER : MATTE);
                }});

                // Helper for slider binding
                function bindSlider(id, spanId, fn) {{
                    document.getElementById(id).addEventListener('input', function() {{
                        const v = parseFloat(this.value);
                        document.getElementById(spanId).textContent = v.toFixed(2);
                        fn(v);
                    }});
                }}

                bindSlider('rough','rv',  function() {{ applyAllWoodProps(); }});
                bindSlider('cc',   'ccv', function() {{ applyAllWoodProps(); }});
                bindSlider('ccr', 'ccrv', function() {{ applyAllWoodProps(); }});
                bindSlider('ns',  'nsv',  function() {{ applyAllWoodProps(); applyFloorProps(); }});
                bindSlider('emi', 'emiv', function() {{ applyAllWoodProps(); applyFloorProps(); }});
                bindSlider('fr',  'frv',  function() {{ applyFloorProps(); }});
                bindSlider('fcc', 'fccv', function() {{ applyFloorProps(); }});
                bindSlider('fccr','fccrv',function() {{ applyFloorProps(); }});
                bindSlider('expo','expv', function(v) {{ renderer.toneMappingExposure = v; }});
                bindSlider('kl',  'klv',  function(v) {{ dirLight.intensity = v; }});
                bindSlider('fl',  'flv',  function(v) {{ bulbLights.forEach(function(l) {{ l.intensity=v; }}); }});

                // Grain scale for instrument
                bindSlider('gs', 'gsv', function(v) {{
                    modelMaterials.forEach(function(m) {{
                        if(m.map) {{ m.map.repeat.set(v,v); m.map.needsUpdate=true; }}
                        if(m.normalMap) {{ m.normalMap.repeat.set(v,v); m.normalMap.needsUpdate=true; }}
                        if(m.roughnessMap) {{ m.roughnessMap.repeat.set(v,v); m.roughnessMap.needsUpdate=true; }}
                    }});
                }});

                // Grain scale for floor
                bindSlider('fgs', 'fgsv', function(v) {{
                    [floorMat.map, floorMat.normalMap, floorMat.roughnessMap].forEach(function(t) {{
                        if(t) {{ t.repeat.set(v,v); t.needsUpdate=true; }}
                    }});
                    floorMat.needsUpdate=true;
                }});

                // Instrument texture selector
                document.getElementById('woodTexture').addEventListener('change', function(e) {{
                    const slug = e.target.value;
                    instDiff=null; instNor=null; instRough=null;
                    loadPBRInstrument(slug);
                }});

                // Floor texture selector
                document.getElementById('floorTexture').addEventListener('change', function(e) {{
                    loadPBRFloor(e.target.value, parseFloat(document.getElementById('fgs').value));
                }});

                // Keyboard controls
                document.addEventListener('keydown', function(event) {{
                    switch(event.code) {{
                        case 'KeyA':
                            event.preventDefault();
                            controls.autoRotate = !controls.autoRotate;
                            break;
                        case 'KeyR':
                            camera.position.set(-5, 5, -5);
                            camera.lookAt(0, 1, 0);
                            controls.target.set(0, 1, 0);
                            controls.update();
                            break;
                    }}
                }});

                renderer.domElement.addEventListener('mousedown', function() {{ controls.autoRotate = false; }});
                renderer.domElement.addEventListener('wheel',     function() {{ controls.autoRotate = false; }});
                renderer.domElement.addEventListener('touchstart',function() {{ controls.autoRotate = false; }});

                // Export settings button
                document.getElementById('export-settings-btn').addEventListener('click', function() {{
                    const settings = {{
                        instrument_texture: document.getElementById('woodTexture').value,
                        floor_texture:      document.getElementById('floorTexture').value,
                        grain_scale:        parseFloat(document.getElementById('gs').value),
                        floor_scale:        parseFloat(document.getElementById('fgs').value),
                        lacquer:            document.getElementById('lacquer').checked,
                        roughness:          parseFloat(document.getElementById('rough').value),
                        clearcoat:          parseFloat(document.getElementById('cc').value),
                        clearcoat_roughness:parseFloat(document.getElementById('ccr').value),
                        normal_strength:    parseFloat(document.getElementById('ns').value),
                        env_intensity:      parseFloat(document.getElementById('emi').value),
                        floor_roughness:    parseFloat(document.getElementById('fr').value),
                        floor_clearcoat:    parseFloat(document.getElementById('fcc').value),
                        floor_cc_roughness: parseFloat(document.getElementById('fccr').value),
                        exposure:           parseFloat(document.getElementById('expo').value),
                        key_light:          parseFloat(document.getElementById('kl').value),
                        fill_lights:        parseFloat(document.getElementById('fl').value),
                    }};
                    const blob = new Blob([JSON.stringify(settings, null, 2)], {{type:'application/json'}});
                    const a = document.createElement('a');
                    a.href = URL.createObjectURL(blob);
                    a.download = 'render_settings.json';
                    a.click();
                    URL.revokeObjectURL(a.href);
                }});

                // Fullscreen button
                document.getElementById('fullscreen-btn').addEventListener('click', function() {{
                    const el = document.getElementById('container');
                    if (!document.fullscreenElement) {{
                        (el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen).call(el);
                        this.textContent = '\u26F6';
                    }} else {{
                        (document.exitFullscreen || document.webkitExitFullscreen || document.mozCancelFullScreen).call(document);
                    }}
                }});
                document.addEventListener('fullscreenchange', function() {{
                    const btn = document.getElementById('fullscreen-btn');
                    if(btn) btn.textContent = document.fullscreenElement ? '\u2715' : '\u26F6';
                }});
            }}

            // (Export scene as JSON removed)
            function exportSceneAsJSON() {{
                console.log('Exporting scene as JSON...');

                // Helper to convert texture to base64 (returns null if CORS blocks it)
                function textureToBase64(texture) {{
                    if (!texture || !texture.image) return null;
                    try {{
                        const canvas = document.createElement('canvas');
                        canvas.width = texture.image.width || 512;
                        canvas.height = texture.image.height || 512;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(texture.image, 0, 0, canvas.width, canvas.height);
                        return canvas.toDataURL('image/jpeg', 0.85);
                    }} catch (e) {{
                        console.warn('CORS blocked texture export:', e.message);
                        return null;
                    }}
                }}

                // Warm oak fallback color for wood materials
                const WOOD_COLOR = '#A0722A';
                const SPECIAL_MATERIALS = {{
                    'black': '#1a1a1a',
                    'white': '#f5f5f0',
                    'metal': '#888888',
                    'dark_wood': '#3d2817',
                    'ebony': '#1c1c1c'
                }};

                // Collect material data for meshes (MeshPhysicalMaterial doesn't serialize well)
                // Use array to handle multiple meshes, match by name on load
                const materialOverrides = [];
                let meshIndex = 0;

                scene.traverse((obj) => {{
                    if (obj.isMesh && obj.material) {{
                        const mat = obj.material;
                        const name = obj.name || '';

                        // Determine the correct color
                        let color = mat.color ? '#' + mat.color.getHexString() : WOOD_COLOR;

                        // Check for special material names
                        let isSpecialMaterial = false;
                        for (const [key, specialColor] of Object.entries(SPECIAL_MATERIALS)) {{
                            if (name.toLowerCase().includes('material:' + key)) {{
                                color = specialColor;
                                isSpecialMaterial = true;
                                break;
                            }}
                        }}

                        // If color is white/near-white and not special, it's wood expecting a texture
                        if (!isSpecialMaterial && (color === '#ffffff' || color === '#fefefe')) {{
                            color = WOOD_COLOR;
                        }}

                        // Try to capture texture
                        let textureData = null;
                        if (mat.map) {{
                            textureData = textureToBase64(mat.map);
                        }}

                        // Store material properties with index for matching
                        materialOverrides.push({{
                            index: meshIndex++,
                            name: name,
                            type: mat.type,
                            color: color,
                            texture: textureData,
                            metalness: mat.metalness ?? 0,
                            roughness: mat.roughness ?? 0.3,
                            clearcoat: mat.clearcoat ?? 0.8,
                            clearcoatRoughness: mat.clearcoatRoughness ?? 0.1,
                            reflectivity: mat.reflectivity ?? 0.5,
                            envMapIntensity: mat.envMapIntensity ?? 1,
                            emissive: mat.emissive ? '#' + mat.emissive.getHexString() : null,
                            emissiveIntensity: mat.emissiveIntensity ?? 0
                        }});
                    }}
                }});

                // Export scene to JSON
                const sceneJSON = scene.toJSON();

                // Also include camera data and material overrides
                const exportData = {{
                    metadata: {{
                        type: 'OrganConsoleScene',
                        version: '1.1',
                        generator: 'OrganConsoleDesigner'
                    }},
                    scene: sceneJSON,
                    materialOverrides: materialOverrides,
                    camera: {{
                        type: 'PerspectiveCamera',
                        fov: camera.fov,
                        aspect: camera.aspect,
                        near: camera.near,
                        far: camera.far,
                        position: camera.position.toArray(),
                        target: controls.target.toArray()
                    }},
                    rendererSettings: {{
                        toneMapping: 'ACESFilmicToneMapping',
                        toneMappingExposure: 1.0,
                        outputEncoding: 'sRGBEncoding',
                        shadowMapEnabled: true,
                        shadowMapType: 'PCFSoftShadowMap'
                    }}
                }};

                // Convert to JSON string
                const jsonString = JSON.stringify(exportData, null, 2);

                // Create download
                const blob = new Blob([jsonString], {{ type: 'application/json' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'organ_console_scene.json';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                console.log('Scene exported successfully!');
            }}


            // Animation loop
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();

            // Handle window resize
            window.addEventListener('resize', () => {{
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            }});
        </script>
    </body>
    </html>
    """
    
    return html_template
