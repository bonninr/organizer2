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
    Create a Three.js GLTF viewer with lacquered wood material.
    
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
    
    # Handle wood texture - get as base64
    wood_texture_uri = get_wood_texture_base64(wood_texture_path)
    
    # Create the HTML template with Three.js
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lacquered Wood GLTF Viewer</title>
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
            <div class="controls">
                <strong>Controls:</strong><br>
                Mouse: Rotate • Wheel: Zoom<br>
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
            const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.2;
            container.appendChild(renderer.domElement);

            // Camera controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.enableZoom = true;
            controls.autoRotate = true;
            controls.autoRotateSpeed = 1.0;

            // Lighting setup for lacquered wood
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
            scene.add(ambientLight);

            // Main directional light (cathedral style)
            const mainLight = new THREE.DirectionalLight(0xfff8e1, 2.5);
            mainLight.position.set(10, 15, 5);
            mainLight.castShadow = true;
            mainLight.shadow.mapSize.width = 2048;
            mainLight.shadow.mapSize.height = 2048;
            scene.add(mainLight);

            // Secondary warm light
            const warmLight = new THREE.SpotLight(0xffcc80, 1.5);
            warmLight.position.set(-8, 12, 8);
            warmLight.angle = Math.PI / 4;
            warmLight.penumbra = 0.3;
            scene.add(warmLight);

            // Accent light for highlights
            const accentLight = new THREE.PointLight(0xffffff, 0.8);
            accentLight.position.set(5, 8, -5);
            scene.add(accentLight);

            // Reflective floor
            const floorGeometry = new THREE.PlaneGeometry(50, 50);
            const floorMaterial = new THREE.MeshPhysicalMaterial({{
                color: 0x1a1a1a,
                metalness: 0.1,
                roughness: 0.05,
                clearcoat: 0.8,
                reflectivity: 0.9,
                transparent: true,
                opacity: 0.8
            }});
            const floor = new THREE.Mesh(floorGeometry, floorMaterial);
            floor.rotation.x = -Math.PI / 2;
            floor.position.y = 0;
            floor.receiveShadow = true;
            scene.add(floor);

            // Load GLTF model
            const loader = new THREE.GLTFLoader();
            const textureLoader = new THREE.TextureLoader();

            // Promise-based texture loading function
            function loadAndApplyWoodTexture(model) {{
                return new Promise((resolve, reject) => {{
                    const materialProps = {{
                        color: 0xd2b48c, // Default tan wood color
                        metalness: 0.0,
                        roughness: 0.4,
                        clearcoat: 0.6,
                        clearcoatRoughness: 0.1,
                        reflectivity: 0.8,
                        envMapIntensity: 1.0
                    }};

                    {"" if not wood_texture_uri else f'''
                    // Load wood texture if available
                    console.log('🔄 Loading wood texture...');
                    
                    const textureLoader = new THREE.TextureLoader();
                    textureLoader.load(
                        "{wood_texture_uri}",
                        function(texture) {{
                            console.log('✅ Wood texture loaded successfully');
                            
                            // Configure texture
                            texture.wrapS = THREE.RepeatWrapping;
                            texture.wrapT = THREE.RepeatWrapping;
                            texture.repeat.set(2, 2);
                            texture.encoding = THREE.sRGBEncoding;
                            texture.needsUpdate = true;
                            
                            // Create material with texture
                            const woodMaterial = new THREE.MeshPhysicalMaterial({{
                                map: texture,
                                color: 0xffffff, // White to show texture
                                metalness: 0.0,
                                roughness: 0.4,
                                clearcoat: 0.6,
                                clearcoatRoughness: 0.1,
                                reflectivity: 0.8,
                                envMapIntensity: 1.0
                            }});
                            
                            // Apply to all meshes
                            model.traverse((child) => {{
                                if (child.isMesh) {{
                                    child.material = woodMaterial.clone();
                                    child.material.needsUpdate = true;
                                }}
                            }});
                            
                            console.log('✅ Wood material applied to all meshes');
                            resolve(model);
                        }},
                        undefined,
                        function(error) {{
                            console.error('❌ Failed to load texture:', error);
                            // Apply fallback material without texture
                            const fallbackMaterial = new THREE.MeshPhysicalMaterial(materialProps);
                            model.traverse((child) => {{
                                if (child.isMesh) {{
                                    child.material = fallbackMaterial.clone();
                                }}
                            }});
                            resolve(model); // Still resolve, just with fallback material
                        }}
                    );
                    '''}
                    
                    {"" if wood_texture_uri else f'''
                    // No texture available, use fallback material
                    console.log('ℹ️ No texture available, using fallback material');
                    const fallbackMaterial = new THREE.MeshPhysicalMaterial(materialProps);
                    model.traverse((child) => {{
                        if (child.isMesh) {{
                            child.material = fallbackMaterial.clone();
                        }}
                    }});
                    resolve(model);
                    '''}
                }});
            }}

            // Load and process GLTF
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
                    async function(gltf) {{
                        console.log('✅ GLTF loaded successfully');
                        
                        const model = gltf.scene;
                        
                        // Center and scale the model
                        const box = new THREE.Box3().setFromObject(model);
                        const center = box.getCenter(new THREE.Vector3());
                        const size = box.getSize(new THREE.Vector3());
                        
                        const maxDim = Math.max(size.x, size.y, size.z);
                        const scale = 4 / maxDim;
                        model.scale.setScalar(scale);
                        model.position.sub(center.multiplyScalar(scale));
                        model.position.y = 0;
                        
                        // Set shadow properties for all meshes
                        model.traverse((child) => {{
                            if (child.isMesh) {{
                                child.castShadow = true;
                                child.receiveShadow = true;
                            }}
                        }});
                        
                        // Load texture first, then apply materials and add to scene
                        await loadAndApplyWoodTexture(model);
                        
                        // Add model to scene only after texture is loaded
                        scene.add(model);
                        
                        // Position camera for optimal view
                        camera.position.set(3.32, 4.05, -2.71);
                        camera.lookAt(-0.06, 1.59, 0.44);
                        controls.target.set(-0.06, 1.59, 0.44);
                        controls.update();
                        
                        // Hide loading indicator
                        loading.style.display = 'none';
                        
                        // Clean up blob URL
                        URL.revokeObjectURL(gltfUrl);
                        
                        // Setup controls and animation
                        setupInteraction(model);
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

            function setupInteraction(model) {{
                let hasUserInteracted = false;
                
                // Stop auto-rotation on first user interaction
                function stopAutoRotateOnInteraction() {{
                    if (!hasUserInteracted) {{
                        hasUserInteracted = true;
                        controls.autoRotate = false;
                        console.log('Auto-rotation stopped due to user interaction');
                    }}
                }}
                
                // Add event listeners for user interactions (only to stop auto-rotation once)
                controls.addEventListener('start', stopAutoRotateOnInteraction);
                renderer.domElement.addEventListener('wheel', stopAutoRotateOnInteraction, {{ passive: false }});
                renderer.domElement.addEventListener('mousedown', stopAutoRotateOnInteraction);
                renderer.domElement.addEventListener('touchstart', stopAutoRotateOnInteraction);
                
                // Keyboard controls
                document.addEventListener('keydown', (event) => {{
                    switch(event.code) {{
                        case 'KeyA':
                            event.preventDefault();
                            controls.autoRotate = !controls.autoRotate;
                            hasUserInteracted = true; // Mark as interacted when manually toggling
                            console.log('Auto-rotation toggled:', controls.autoRotate);
                            break;
                        case 'KeyR':
                            // Reset camera position
                            camera.position.set(3.32, 4.05, -2.71);
                            camera.lookAt(-0.06, 1.59, 0.44);
                            controls.target.set(-0.06, 1.59, 0.44);
                            controls.update();
                            break;
                    }}
                }});

                // Animation loop
                function animate() {{
                    requestAnimationFrame(animate);
                    controls.update();
                    renderer.render(scene, camera);
                }}
                animate();
            }}

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
