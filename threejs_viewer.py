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


def create_threejs_gltf_viewer(gltf_file_path, wood_texture_path=None, height=500):
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
        </style>
    </head>
    <body>
        <div id="container">
            <div id="loading">
                <div>Loading Lacquered Wood Model...</div>
                <div style="font-size: 0.9em; margin-top: 10px;">Applying materials...</div>
            </div>
            
            <div id="menu">
                <div class="control">
                    <label>Wood Texture:</label>
                    <select id="woodTexture">
                        <option value="hardwood2_diffuse">Classic Hardwood</option>
                        <option value="hardwood2_bump">Rich Hardwood</option>
                        <option value="oak_veneer">Oak Veneer</option>
                        <option value="local" {"selected" if wood_texture_uri else ""}>Local Wood</option>
                        <option value="fallback">Warm Oak (Fallback)</option>
                    </select>
                </div>
            </div>
            
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

            // Camera position
            camera.position.set(5, 5, 5);

            // Camera controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.enableZoom = true;
            controls.enablePan = true;
            controls.autoRotate = true;
            controls.autoRotateSpeed = 1.0;

            // Hemisphere light with warm tones for church-like ambience
            const hemiLight = new THREE.HemisphereLight(0xffd4a3, 0x0f0e0d, 0.4);
            scene.add(hemiLight);
            
            // Add directional light from above with warmer tone
            const dirLight = new THREE.DirectionalLight(0xffcc99, 0.24); // Reduced by 20% from 0.3
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
                const light = new THREE.PointLight(0xffbb66, 0.64, 100, 2); // Reduced by 40% total, warmer color
                light.add(new THREE.Mesh(bulbGeometry, bulbMat.clone()));
                light.position.set(pos.x, pos.y, pos.z);
                light.castShadow = true;
                bulbLights.push(light);
                scene.add(light);
            }});

            // Floor material setup with increased reflectivity and bumpiness
            const floorMat = new THREE.MeshStandardMaterial({{
                roughness: 0.3,
                color: 0xffffff,
                metalness: 0.6,
                bumpScale: 0.002, // Increased from 0.0005 for more visible floor tiles
                envMapIntensity: 1.5,
            }});
            
            // Load the actual textures from Three.js examples
            const textureLoader = new THREE.TextureLoader();
            
            // Load hardwood2_diffuse.jpg for floor with 40% larger scale
            textureLoader.load("https://threejs.org/examples/textures/hardwood2_diffuse.jpg", function(map) {{
                map.wrapS = THREE.RepeatWrapping;
                map.wrapT = THREE.RepeatWrapping;
                map.anisotropy = 4;
                map.repeat.set(14, 33.6); // Increased by 40%
                floorMat.map = map;
                floorMat.needsUpdate = true;
            }});
            
            // Load hardwood2_bump.jpg for floor with increased effect
            textureLoader.load("https://threejs.org/examples/textures/hardwood2_bump.jpg", function(map) {{
                map.wrapS = THREE.RepeatWrapping;
                map.wrapT = THREE.RepeatWrapping;
                map.anisotropy = 4;
                map.repeat.set(14, 33.6); // Increased by 40%
                floorMat.bumpMap = map;
                floorMat.needsUpdate = true;
            }});
            
            // Load hardwood2_roughness.jpg for floor
            textureLoader.load("https://threejs.org/examples/textures/hardwood2_roughness.jpg", function(map) {{
                map.wrapS = THREE.RepeatWrapping;
                map.wrapT = THREE.RepeatWrapping;
                map.anisotropy = 4;
                map.repeat.set(14, 33.6); // Increased by 40%
                floorMat.roughnessMap = map;
                floorMat.needsUpdate = true;
            }});
            
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
            
            // Wood textures database
            const woodTextures = {{
                "hardwood2_diffuse": 'https://threejs.org/examples/textures/hardwood2_diffuse.jpg',
                "hardwood2_bump": 'https://threejs.org/examples/textures/hardwood2_bump.jpg',
                "oak_veneer": 'https://www.openpipes.org/beta/organizer_woods/oak_veneer.jpg',
                "local": "{wood_texture_uri or ''}",
                "fallback": null // Will use procedural color
            }};

            // Global variables for model texture management
            let currentModel = null;
            let modelMaterials = []; 

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
                        // CRITICAL: Ensure UV coordinates exist for texture mapping
                        if (!child.geometry.attributes.uv) {{
                            console.log('🔧 Generating UV coordinates for mesh:', child.name || 'unnamed');
                            
                            // Get geometry
                            const geometry = child.geometry;
                            const positionAttribute = geometry.attributes.position;
                            const vertexCount = positionAttribute.count;
                            
                            // Create UV coordinates using triplanar projection
                            const uvs = new Float32Array(vertexCount * 2);
                            const position = new THREE.Vector3();
                            const normal = new THREE.Vector3();
                            
                            // Calculate bounding box for normalization
                            geometry.computeBoundingBox();
                            const box = geometry.boundingBox;
                            const size = new THREE.Vector3();
                            box.getSize(size);
                            
                            // Compute vertex normals if not present
                            if (!geometry.attributes.normal) {{
                                geometry.computeVertexNormals();
                            }}
                            
                            const normalAttribute = geometry.attributes.normal;
                            
                            for (let i = 0; i < vertexCount; i++) {{
                                position.fromBufferAttribute(positionAttribute, i);
                                normal.fromBufferAttribute(normalAttribute, i);
                                
                                // Use triplanar mapping - project based on normal direction
                                let u, v;
                                const absNormal = new THREE.Vector3(
                                    Math.abs(normal.x),
                                    Math.abs(normal.y), 
                                    Math.abs(normal.z)
                                );
                                
                                if (absNormal.x >= absNormal.y && absNormal.x >= absNormal.z) {{
                                    // Project on YZ plane (for X-facing surfaces)
                                    u = (position.z - box.min.z) / size.z;
                                    v = (position.y - box.min.y) / size.y;
                                }} else if (absNormal.y >= absNormal.x && absNormal.y >= absNormal.z) {{
                                    // Project on XZ plane (for Y-facing surfaces)
                                    u = (position.x - box.min.x) / size.x;
                                    v = (position.z - box.min.z) / size.z;
                                }} else {{
                                    // Project on XY plane (for Z-facing surfaces)
                                    u = (position.x - box.min.x) / size.x;
                                    v = (position.y - box.min.y) / size.y;
                                }}
                                
                                uvs[i * 2] = u;
                                uvs[i * 2 + 1] = v;
                            }}
                            
                            // Add UV attribute to geometry
                            geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
                            console.log('✅ UV coordinates generated');
                        }}
                        
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
                        currentModel.scale.setScalar(scale);
                        currentModel.position.sub(center.multiplyScalar(scale));
                        currentModel.position.y = 0;
                        
                        // Apply initial wood texture using your recommended approach
                        const initialTextureUrl = woodTextures.local && woodTextures.local !== '' 
                            ? woodTextures.local
                            : 'https://threejs.org/examples/textures/hardwood2_diffuse.jpg'; // Default hardwood
                        
                        // Load initial texture and apply to model
                        textureLoader.load(initialTextureUrl, function(myTexture) {{
                            myTexture.wrapS = THREE.RepeatWrapping;
                            myTexture.wrapT = THREE.RepeatWrapping;
                            myTexture.repeat.set(2, 2);
                            myTexture.anisotropy = 4;
                            
                            // Apply texture using your recommended pattern
                            currentModel.traverse(function(child) {{
                                if (child.isMesh) {{
                                    // CRITICAL: Generate UV coordinates if missing
                                    if (!child.geometry.attributes.uv) {{
                                        console.log('🔧 Generating UV coordinates for mesh:', child.name || 'unnamed');
                                        
                                        // Get geometry
                                        const geometry = child.geometry;
                                        const positionAttribute = geometry.attributes.position;
                                        const vertexCount = positionAttribute.count;
                                        
                                        // Create UV coordinates using triplanar projection
                                        const uvs = new Float32Array(vertexCount * 2);
                                        const position = new THREE.Vector3();
                                        const normal = new THREE.Vector3();
                                        
                                        // Calculate bounding box for normalization
                                        geometry.computeBoundingBox();
                                        const box = geometry.boundingBox;
                                        const size = new THREE.Vector3();
                                        box.getSize(size);
                                        
                                        // Compute vertex normals if not present
                                        if (!geometry.attributes.normal) {{
                                            geometry.computeVertexNormals();
                                        }}
                                        
                                        const normalAttribute = geometry.attributes.normal;
                                        
                                        for (let i = 0; i < vertexCount; i++) {{
                                            position.fromBufferAttribute(positionAttribute, i);
                                            normal.fromBufferAttribute(normalAttribute, i);
                                            
                                            // Use triplanar mapping - project based on normal direction
                                            let u, v;
                                            const absNormal = new THREE.Vector3(
                                                Math.abs(normal.x),
                                                Math.abs(normal.y), 
                                                Math.abs(normal.z)
                                            );
                                            
                                            if (absNormal.x >= absNormal.y && absNormal.x >= absNormal.z) {{
                                                // Project on YZ plane (for X-facing surfaces)
                                                u = (position.z - box.min.z) / size.z;
                                                v = (position.y - box.min.y) / size.y;
                                            }} else if (absNormal.y >= absNormal.x && absNormal.y >= absNormal.z) {{
                                                // Project on XZ plane (for Y-facing surfaces)
                                                u = (position.x - box.min.x) / size.x;
                                                v = (position.z - box.min.z) / size.z;
                                            }} else {{
                                                // Project on XY plane (for Z-facing surfaces)
                                                u = (position.x - box.min.x) / size.x;
                                                v = (position.y - box.min.y) / size.y;
                                            }}
                                            
                                            uvs[i * 2] = u;
                                            uvs[i * 2 + 1] = v;
                                        }}
                                        
                                        // Add UV attribute to geometry
                                        geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
                                        console.log('✅ UV coordinates generated');
                                    }}
                                    
                                    // Convert to MeshPhysicalMaterial for lacquer effect
                                    const newMaterial = new THREE.MeshPhysicalMaterial({{
                                        map: myTexture,
                                        color: 0xffffff,
                                        metalness: 0.0,
                                        roughness: 0.2,
                                        clearcoat: 0.8,
                                        clearcoatRoughness: 0.1,
                                        envMapIntensity: 1.0,
                                        reflectivity: 0.8
                                    }});
                                    
                                    child.material = newMaterial;
                                    child.material.needsUpdate = true;
                                    child.castShadow = true;
                                    child.receiveShadow = true;
                                    modelMaterials.push(child.material);
                                    console.log('🎨 Texture applied to mesh:', child.name || 'unnamed');
                                }}
                            }});
                            
                            console.log('✅ Initial wood texture applied successfully');
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
                const woodTextureSelect = document.getElementById('woodTexture');

                // Wood texture selector - using proper texture replacement approach
                woodTextureSelect.addEventListener('change', (event) => {{
                    const selectedTexture = event.target.value;
                    
                    if (selectedTexture === 'fallback') {{
                        // Apply fallback material without texture
                        applyTextureToModel(currentModel, null);
                    }} else {{
                        const textureUrl = woodTextures[selectedTexture];
                        
                        // Load new texture and apply
                        textureLoader.load(textureUrl, function(newTexture) {{
                            newTexture.wrapS = THREE.RepeatWrapping;
                            newTexture.wrapT = THREE.RepeatWrapping;
                            newTexture.repeat.set(2, 2);
                            newTexture.anisotropy = 4;
                            
                            // Apply texture to model using proper approach
                            applyTextureToModel(currentModel, newTexture);
                            
                            console.log('🎨 Wood texture changed to:', selectedTexture);
                        }}, undefined, function(error) {{
                            console.warn('❌ Failed to load texture:', textureUrl, error);
                            // Apply fallback if texture loading fails
                            applyTextureToModel(currentModel, null);
                        }});
                    }}
                }});

                // Keyboard controls
                let hasUserInteracted = false;
                
                document.addEventListener('keydown', (event) => {{
                    switch(event.code) {{
                        case 'KeyA':
                            event.preventDefault();
                            controls.autoRotate = !controls.autoRotate;
                            hasUserInteracted = true;
                            console.log('Auto-rotation toggled:', controls.autoRotate);
                            break;
                        case 'KeyR':
                            // Reset camera position
                            camera.position.set(5, 5, 5);
                            camera.lookAt(0, 1, 0);
                            controls.target.set(0, 1, 0);
                            controls.update();
                            break;
                    }}
                }});

                // Stop auto-rotation on first user interaction
                const stopAutoRotateOnInteraction = () => {{
                    if (!hasUserInteracted) {{
                        hasUserInteracted = true;
                        controls.autoRotate = false;
                        console.log('Auto-rotation stopped due to user interaction');
                    }}
                }};
                
                renderer.domElement.addEventListener('wheel', stopAutoRotateOnInteraction, {{ passive: false }});
                renderer.domElement.addEventListener('mousedown', stopAutoRotateOnInteraction);
                renderer.domElement.addEventListener('touchstart', stopAutoRotateOnInteraction);
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
