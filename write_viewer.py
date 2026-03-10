"""Writes viewer_dev.html — run `python write_viewer.py` then refresh browser."""

# Texture palettes
# format: (label, diff_url, nor_url, rough_url)
# nor_url / rough_url may be None if unavailable

TJS = "https://threejs.org/examples/textures"
PH  = "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k"

def ph(slug, m): return f"{PH}/{slug}/{slug}_{m}_1k.jpg"

INST_TEXTURES = [
    # Three.js built-in (always work, used as defaults)
    ("Classic Hardwood",   f"{TJS}/hardwood2_diffuse.jpg",  None,                              f"{TJS}/hardwood2_roughness.jpg"),
    ("Rich Hardwood (bump)",f"{TJS}/hardwood2_bump.jpg",    None,                              f"{TJS}/hardwood2_roughness.jpg"),
    # Poly Haven — veneer / furniture
    ("Oak Veneer",          ph("oak_veneer_01","diff"),       ph("oak_veneer_01","nor_gl"),      ph("oak_veneer_01","rough")),
    ("Fine Grain Wood",     ph("fine_grained_wood","diff"),   ph("fine_grained_wood","nor_gl"),  ph("fine_grained_wood","rough")),
    ("Wood Table",          ph("wood_table","diff"),          ph("wood_table","nor_gl"),         ph("wood_table","rough")),
    ("Wood Table 2",        ph("wood_table_001","diff"),      ph("wood_table_001","nor_gl"),     ph("wood_table_001","rough")),
    ("Wood Table Worn",     ph("wood_table_worn","diff"),     ph("wood_table_worn","nor_gl"),    ph("wood_table_worn","rough")),
    ("Rosewood Veneer",     ph("rosewood_veneer1","diff"),    ph("rosewood_veneer1","nor_gl"),   ph("rosewood_veneer1","rough")),
    ("Kitchen Wood",        ph("kitchen_wood","diff"),        ph("kitchen_wood","nor_gl"),       ph("kitchen_wood","rough")),
    ("Stained Pine",        ph("stained_pine","diff"),        ph("stained_pine","nor_gl"),       ph("stained_pine","rough")),
    ("Dark Wood",           ph("dark_wood","diff"),           ph("dark_wood","nor_gl"),          ph("dark_wood","rough")),
    ("Synthetic Wood",      ph("synthetic_wood","diff"),      ph("synthetic_wood","nor_gl"),     ph("synthetic_wood","rough")),
    ("Plywood",             ph("plywood","diff"),             ph("plywood","nor_gl"),            ph("plywood","rough")),
    ("Rough Wood",          ph("rough_wood","diff"),          ph("rough_wood","nor_gl"),         ph("rough_wood","rough")),
    ("Wood Cabinet Worn",   ph("wood_cabinet_worn_long","diff"), ph("wood_cabinet_worn_long","nor_gl"), ph("wood_cabinet_worn_long","rough")),
    # Poly Haven — planks
    ("Brown Planks",        ph("brown_planks_05","diff"),     ph("brown_planks_05","nor_gl"),    ph("brown_planks_05","rough")),
    ("Brown Planks 2",      ph("brown_planks_07","diff"),     ph("brown_planks_07","nor_gl"),    ph("brown_planks_07","rough")),
    ("Dark Planks",         ph("dark_planks","diff"),         ph("dark_planks","nor_gl"),        ph("dark_planks","rough")),
    ("Raw Plank Wall",      ph("raw_plank_wall","diff"),      ph("raw_plank_wall","nor_gl"),     ph("raw_plank_wall","rough")),
    ("Wooden Planks",       ph("wooden_planks","diff"),       ph("wooden_planks","nor_gl"),      ph("wooden_planks","rough")),
    ("Weathered Planks",    ph("weathered_planks","diff"),    ph("weathered_planks","nor_gl"),   ph("weathered_planks","rough")),
    ("Medieval Wood",       ph("medieval_wood","diff"),       ph("medieval_wood","nor_gl"),      ph("medieval_wood","rough")),
]

FLOOR_TEXTURES = [
    # Three.js built-in
    ("Classic Hardwood",   f"{TJS}/hardwood2_diffuse.jpg",  None,                              f"{TJS}/hardwood2_roughness.jpg"),
    # Poly Haven — parquet
    ("Herringbone Parquet", ph("herringbone_parquet","diff"), ph("herringbone_parquet","nor_gl"), ph("herringbone_parquet","rough")),
    ("Rectangular Parquet", ph("rectangular_parquet","diff"), ph("rectangular_parquet","nor_gl"), ph("rectangular_parquet","rough")),
    ("Diagonal Parquet",    ph("diagonal_parquet","diff"),    ph("diagonal_parquet","nor_gl"),    ph("diagonal_parquet","rough")),
    # Poly Haven — floor planks
    ("Wood Floor",          ph("wood_floor","diff"),          ph("wood_floor","nor_gl"),          ph("wood_floor","rough")),
    ("Wood Floor Deck",     ph("wood_floor_deck","diff"),     ph("wood_floor_deck","nor_gl"),     ph("wood_floor_deck","rough")),
    ("Wood Floor Worn",     ph("wood_floor_worn","diff"),     ph("wood_floor_worn","nor_gl"),     ph("wood_floor_worn","rough")),
    ("Plank Flooring",      ph("plank_flooring","diff"),      ph("plank_flooring","nor_gl"),      ph("plank_flooring","rough")),
    ("Plank Flooring 2",    ph("plank_flooring_02","diff"),   ph("plank_flooring_02","nor_gl"),   ph("plank_flooring_02","rough")),
    ("Plank Flooring 3",    ph("plank_flooring_03","diff"),   ph("plank_flooring_03","nor_gl"),   ph("plank_flooring_03","rough")),
    ("Old Wood Floor",      ph("old_wood_floor","diff"),      ph("old_wood_floor","nor_gl"),      ph("old_wood_floor","rough")),
    ("Laminate Floor",      ph("laminate_floor","diff"),      ph("laminate_floor","nor_gl"),      ph("laminate_floor","rough")),
    ("Laminate Floor 2",    ph("laminate_floor_02","diff"),   ph("laminate_floor_02","nor_gl"),   ph("laminate_floor_02","rough")),
    ("Dark Wood Planks",    ph("dark_wooden_planks","diff"),  ph("dark_wooden_planks","nor_gl"),  ph("dark_wooden_planks","rough")),
    ("Worn Planks",         ph("worn_planks","diff"),         ph("worn_planks","nor_gl"),         ph("worn_planks","rough")),
    ("Weathered Brown",     ph("weathered_brown_planks","diff"), ph("weathered_brown_planks","nor_gl"), ph("weathered_brown_planks","rough")),
]

def make_options(textures, default_idx=0):
    opts = []
    for i, (label, d, n, r) in enumerate(textures):
        sel = ' selected' if i == default_idx else ''
        opts.append(f'<option value="{i}"{sel}>{label}</option>')
    return "\n    ".join(opts)

def make_tex_array(textures):
    rows = []
    for label, d, n, r in textures:
        d = d or "null"
        n = n or "null"
        r = r or "null"
        if d != "null": d = f'"{d}"'
        if n != "null": n = f'"{n}"'
        if r != "null": r = f'"{r}"'
        rows.append(f'  {{label:{repr(label)}, d:{d}, n:{n}, r:{r}}}')
    return "[\n" + ",\n".join(rows) + "\n]"


HTML_TPL = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Organ Console - Dev Renderer</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#1a1008; overflow:hidden; font-family:Arial,sans-serif; }}
#c {{ display:block; width:100vw; height:100vh; }}
#ui {{
  position:absolute; top:12px; left:12px;
  background:rgba(0,0,0,.82); color:#ddd;
  padding:12px 14px; border-radius:8px;
  font-size:12px; line-height:2.0; min-width:220px; z-index:10;
  max-height:calc(100vh - 24px); overflow-y:auto;
}}
#ui label {{ display:block; margin-top:5px; font-weight:bold; font-size:11px; color:#aaa; }}
#ui input[type=range] {{ width:100%; margin:1px 0 3px; accent-color:#c8922a; }}
#ui select {{ width:100%; background:#1e1e1e; color:#ddd; border:1px solid #555; padding:3px 4px; border-radius:4px; }}
.section {{ color:#c8922a; font-size:11px; font-weight:bold; margin-top:10px; border-top:1px solid #333; padding-top:6px; }}
.tex-status {{
  font-size:10px; color:#888; margin:2px 0 4px;
  display:flex; gap:6px; align-items:center;
}}
.tex-status span {{ display:inline-flex; align-items:center; gap:2px; }}
.dot {{ width:7px; height:7px; border-radius:50%; background:#444; display:inline-block; }}
.dot.ok  {{ background:#5a5; }}
.dot.err {{ background:#a44; }}
.dot.loading {{ background:#c8922a; }}
.file-btn {{
  display:block; margin-top:4px; padding:3px 8px;
  background:#1e1208; border:1px solid #5a3c10; border-radius:4px;
  color:#c8922a; cursor:pointer; font-size:11px; text-align:center;
}}
.file-btn:hover {{ background:#2a1a0a; }}
#hint {{
  position:absolute; bottom:10px; left:12px;
  background:rgba(0,0,0,.55); color:#666;
  padding:5px 10px; border-radius:5px; font-size:11px;
}}
</style>
</head>
<body>
<canvas id="c"></canvas>
<input type="file" id="file-inst"  accept="image/*" style="display:none">
<input type="file" id="file-floor" accept="image/*" style="display:none">

<div id="ui">
  <strong style="color:#c8922a;font-size:13px;">Renderer Dev</strong>

  <div class="section">LACQUER / FINISH</div>
  <label style="display:flex;align-items:center;gap:6px;cursor:pointer;color:#ddd;">
    <input type="checkbox" id="lacquer" checked style="accent-color:#c8922a;width:13px;height:13px;">
    Lacquer finish
  </label>
  <label>Roughness <span id="rv">0.30</span></label>
  <input type="range" id="rough" min="0" max="1" step="0.01" value="0.30">
  <label>Clearcoat <span id="ccv">0.90</span></label>
  <input type="range" id="cc" min="0" max="1" step="0.01" value="0.90">
  <label>Clearcoat Roughness <span id="ccrv">0.08</span></label>
  <input type="range" id="ccr" min="0" max="1" step="0.01" value="0.08">
  <label>Normal strength <span id="nsv">0.70</span></label>
  <input type="range" id="ns" min="0" max="4" step="0.05" value="0.70">
  <label>Env map intensity <span id="emiv">1.20</span></label>
  <input type="range" id="emi" min="0" max="4" step="0.05" value="1.20">
  <label>Floor roughness <span id="frv">0.25</span></label>
  <input type="range" id="fr" min="0" max="1" step="0.01" value="0.25">
  <label>Floor clearcoat <span id="fccv">0.95</span></label>
  <input type="range" id="fcc" min="0" max="1" step="0.01" value="0.95">
  <label>Floor cc roughness <span id="fccrv">0.05</span></label>
  <input type="range" id="fccr" min="0" max="1" step="0.01" value="0.05">

  <div class="section">INSTRUMENT TEXTURE</div>
  <label>Grain scale <span id="gsv">2.0</span></label>
  <input type="range" id="gs" min="0.3" max="10" step="0.1" value="2.0">
  <select id="tex-inst">
    ___INST_OPTIONS___
  </select>
  <div class="tex-status" id="inst-status">
    <span><span class="dot" id="i-d"></span>diff</span>
    <span><span class="dot" id="i-n"></span>nor</span>
    <span><span class="dot" id="i-r"></span>rough</span>
    <span id="inst-label" style="color:#888;font-size:10px;flex:1;text-align:right"></span>
  </div>
  <label class="file-btn" for="file-inst">Browse local file (diff only)…</label>

  <div class="section">FLOOR TEXTURE</div>
  <label>Grain scale <span id="fgsv">4.0</span></label>
  <input type="range" id="fgs" min="0.5" max="20" step="0.5" value="4.0">
  <select id="tex-floor">
    ___FLOOR_OPTIONS___
  </select>
  <div class="tex-status" id="floor-status">
    <span><span class="dot" id="f-d"></span>diff</span>
    <span><span class="dot" id="f-n"></span>nor</span>
    <span><span class="dot" id="f-r"></span>rough</span>
    <span id="floor-label" style="color:#888;font-size:10px;flex:1;text-align:right"></span>
  </div>
  <label class="file-btn" for="file-floor">Browse local file (diff only)…</label>

  <div class="section">LIGHTING</div>
  <label>Exposure <span id="expv">1.35</span></label>
  <input type="range" id="expo" min="0.4" max="3" step="0.05" value="1.35">
  <label>Key <span id="klv">4.0</span></label>
  <input type="range" id="kl" min="0" max="10" step="0.1" value="4.0">
  <label>Fill <span id="flv">1.4</span></label>
  <input type="range" id="fl" min="0" max="6" step="0.1" value="1.4">
  <label>Rim <span id="rlv">0.9</span></label>
  <input type="range" id="rl" min="0" max="4" step="0.1" value="0.9">

  <br><span style="color:#555;font-size:10px;">A = auto-rotate &nbsp; R = reset view</span>
</div>
<div id="hint">Drag: rotate | Right-drag: pan | Scroll: zoom</div>

___IMPORTMAP___
<script type="module">
import * as THREE from 'three';
import { OrbitControls }  from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader }     from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

// ── Renderer ───────────────────────────────────────────────────────────────
const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true }});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.35;
renderer.outputColorSpace = THREE.SRGBColorSpace;

// ── Environment (needed for clearcoat/lacquer reflections) ─────────────────
const pmrem = new THREE.PMREMGenerator(renderer);
pmrem.compileEquirectangularShader();
const envTexture = pmrem.fromScene(new RoomEnvironment(renderer)).texture;

// ── Scene ──────────────────────────────────────────────────────────────────
const scene = new THREE.Scene();
scene.environment = envTexture;
scene.background = new THREE.Color(0x180e04);
scene.fog = new THREE.FogExp2(0x180e04, 0.055);

const camera = new THREE.PerspectiveCamera(42, innerWidth/innerHeight, 0.05, 300);
camera.position.set(-5, 4, -5);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true; controls.dampingFactor = 0.07;
controls.autoRotate = true; controls.autoRotateSpeed = 0.7;
controls.target.set(0, 0.8, 0); controls.update();

// ── Lights ─────────────────────────────────────────────────────────────────
const hemi = new THREE.HemisphereLight(0xffe8c0, 0x1a0800, 0.22);
scene.add(hemi);

const keyLight = new THREE.DirectionalLight(0xffd080, 4.0);
keyLight.position.set(-4, 8, -3);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048);
keyLight.shadow.camera.near=0.5; keyLight.shadow.camera.far=25;
keyLight.shadow.camera.top=7; keyLight.shadow.camera.bottom=-7;
keyLight.shadow.camera.left=-7; keyLight.shadow.camera.right=7;
keyLight.shadow.bias=-0.0003;
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0xfff8f0, 1.4);
fillLight.position.set(6, 5, -1);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0xff9933, 0.9);
rimLight.position.set(0.5, 1.5, 7);
scene.add(rimLight);

// ── Floor ──────────────────────────────────────────────────────────────────
const floorMat = new THREE.MeshPhysicalMaterial({{
  color:0xb08050, roughness:0.25, metalness:0.0,
  clearcoat:0.95, clearcoatRoughness:0.05, envMapIntensity:1.2
}});
const floorGeo = new THREE.PlaneGeometry(30, 30);
const floor = new THREE.Mesh(floorGeo, floorMat);
floor.rotation.x = -Math.PI/2; floor.receiveShadow = true; floor.position.y = -0.002;
scene.add(floor);

// ── Texture palettes ───────────────────────────────────────────────────────
const INST_TEXTURES  = ___INST_ARRAY___;
const FLOOR_TEXTURES = ___FLOOR_ARRAY___;

// ── Texture loader helper ──────────────────────────────────────────────────
const texLoader = new THREE.TextureLoader();
const aniso = renderer.capabilities.getMaxAnisotropy();

function loadMap(url, srgb, dotId, repeat, cb) {{
  const dot = document.getElementById(dotId);
  if (!url) {{ if(dot) {{ dot.className='dot err'; }} cb(null); return; }}
  if(dot) dot.className = 'dot loading';
  texLoader.load(url,
    tex => {{
      tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
      tex.anisotropy = aniso;
      if(srgb) tex.colorSpace = THREE.SRGBColorSpace;
      if(repeat) tex.repeat.set(repeat, repeat);
      if(dot) dot.className = 'dot ok';
      cb(tex);
    }},
    undefined,
    () => {{ if(dot) dot.className='dot err'; cb(null); }}
  );
}}

// Load a full PBR set from a palette entry and fire cb({diff,nor,rough})
function loadTexSet(entry, prefix, repeat, cb) {{
  const sets = {{ diff:null, nor:null, rough:null }};
  let pending = 3;
  function done() {{ if(--pending === 0) cb(sets); }}
  loadMap(entry.d, true,  prefix+'-d', repeat, t=>{{ sets.diff=t;  done(); }});
  loadMap(entry.n, false, prefix+'-n', repeat, t=>{{ sets.nor=t;   done(); }});
  loadMap(entry.r, false, prefix+'-r', repeat, t=>{{ sets.rough=t; done(); }});
  const lbl = document.getElementById(prefix+'-label');
  if(lbl) lbl.textContent = entry.label;
}}

// ── UV generation (triplanar box-projection — always regenerate) ───────────
// build123d GLTF exports all-zero UV attribute — must overwrite, not skip
function genUVs(geo) {{
  geo.computeBoundingBox();
  if (!geo.attributes.normal) geo.computeVertexNormals();
  const pos = geo.attributes.position;
  const nrm = geo.attributes.normal;
  const box = geo.boundingBox;
  const sz  = new THREE.Vector3(); box.getSize(sz);
  const n   = pos.count;
  const uvs = new Float32Array(n * 2);
  const P   = new THREE.Vector3();
  const N   = new THREE.Vector3();
  for (let i = 0; i < n; i++) {{
    P.fromBufferAttribute(pos, i);
    N.fromBufferAttribute(nrm, i);
    const ax = Math.abs(N.x), ay = Math.abs(N.y), az = Math.abs(N.z);
    let u, v;
    if (ax >= ay && ax >= az) {{
      u = sz.z > 0 ? (P.z - box.min.z) / sz.z : 0;
      v = sz.y > 0 ? (P.y - box.min.y) / sz.y : 0;
    }} else if (ay >= ax && ay >= az) {{
      u = sz.x > 0 ? (P.x - box.min.x) / sz.x : 0;
      v = sz.z > 0 ? (P.z - box.min.z) / sz.z : 0;
    }} else {{
      u = sz.x > 0 ? (P.x - box.min.x) / sz.x : 0;
      v = sz.y > 0 ? (P.y - box.min.y) / sz.y : 0;
    }}
    uvs[i * 2] = u; uvs[i * 2 + 1] = v;
  }}
  geo.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
  geo.attributes.uv.needsUpdate = true;
}}

// ── Special materials (keys, metal) ───────────────────────────────────────
const SPECIAL = {{
  black: {{ color:0x111111, metalness:0.05, roughness:0.35, clearcoat:0.25, clearcoatRoughness:0.3  }},
  white: {{ color:0xf2efe8, metalness:0.00, roughness:0.42, clearcoat:0.35, clearcoatRoughness:0.35 }},
  metal: {{ color:0x888888, metalness:0.90, roughness:0.20, clearcoat:0.0,  clearcoatRoughness:0.0  }},
}};
function specDef(name) {{
  const m = (name||'').match(/material:?([a-zA-Z]+)/);
  return (m && SPECIAL[m[1]]) ? SPECIAL[m[1]] : null;
}}

// ── Apply PBR set to instrument meshes ────────────────────────────────────
let woodMats = [];

function uiv(id) {{ return parseFloat(document.getElementById(id).value); }}

function applyInstSet(model, set) {{
  woodMats = [];
  const ns = uiv('ns');
  model.traverse(child => {{
    if (!child.isMesh) return;
    child.castShadow = child.receiveShadow = true;
    const name = child.name || (child.parent && child.parent.name) || '';
    const spec = specDef(name);
    if (spec) {{
      child.material = new THREE.MeshPhysicalMaterial({{ ...spec, envMapIntensity:0.3 }});
    }} else {{
      // Always regenerate UVs — build123d GLTF has all-zero UV attribute
      genUVs(child.geometry);
      const mat = new THREE.MeshPhysicalMaterial({{
        map:               set.diff  || null,
        normalMap:         set.nor   || null,
        roughnessMap:      set.rough || null,
        color:             set.diff  ? 0xeedcb8 : 0xd4a874,
        metalness:         0.0,
        roughness:         uiv('rough'),
        clearcoat:         uiv('cc'),
        clearcoatRoughness:uiv('ccr'),
        envMapIntensity:   uiv('emi'),
      }});
      if (set.nor) mat.normalScale.set(ns, ns);
      child.material = mat;
      woodMats.push(mat);
    }}
  }});
}}

function applyWoodProps() {{
  const r=uiv('rough'), cc=uiv('cc'), ccr=uiv('ccr'), ns=uiv('ns'), emi=uiv('emi');
  woodMats.forEach(m => {{
    m.roughness=r; m.clearcoat=cc; m.clearcoatRoughness=ccr;
    m.envMapIntensity=emi;
    if(m.normalMap) m.normalScale.set(ns,ns);
    m.needsUpdate=true;
  }});
}}

function applyFloorProps() {{
  floorMat.roughness          = uiv('fr');
  floorMat.clearcoat          = uiv('fcc');
  floorMat.clearcoatRoughness = uiv('fccr');
  floorMat.envMapIntensity    = uiv('emi');
  if(floorMat.normalMap) floorMat.normalScale.set(uiv('ns'), uiv('ns'));
  floorMat.needsUpdate = true;
}}

function setInstRepeat(sc) {{
  woodMats.forEach(m => {{
    [m.map, m.normalMap, m.roughnessMap].forEach(t => {{
      if(t) {{ t.repeat.set(sc,sc); t.needsUpdate=true; }}
    }});
  }});
}}

// ── Apply PBR set to floor ─────────────────────────────────────────────────
function applyFloorSet(set) {{
  floorMat.map          = set.diff  || null;
  floorMat.normalMap    = set.nor   || null;
  floorMat.roughnessMap = set.rough || null;
  floorMat.color.setHex(set.diff ? 0xffffff : 0xb08050);
  applyFloorProps();
}}

function setFloorRepeat(sc) {{
  [floorMat.map, floorMat.normalMap, floorMat.roughnessMap].forEach(t => {{
    if(t) {{ t.repeat.set(sc,sc); t.needsUpdate=true; }}
  }});
  floorMat.needsUpdate=true;
}}

// ── Load GLTF model ────────────────────────────────────────────────────────
let model = null;
new GLTFLoader().load('sample_console.gltf', gltf => {{
  model = gltf.scene;
  const box    = new THREE.Box3().setFromObject(model);
  const size   = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const scale  = 4 / Math.max(size.x, size.y, size.z);
  model.scale.setScalar(scale);
  model.position.copy(center.negate().multiplyScalar(scale));
  model.position.y = 0;
  scene.add(model);

  // Load default instrument texture (index 2 = Oak Veneer, full PBR)
  const instEntry = INST_TEXTURES[2];
  loadTexSet(instEntry, 'inst', uiv('gs'), set => {{ applyInstSet(model, set); }});

  // Load default floor texture (index 1 = Herringbone Parquet)
  const floorEntry = FLOOR_TEXTURES[1];
  loadTexSet(floorEntry, 'floor', uiv('fgs'), set => {{ applyFloorSet(set); }});

}}, undefined, err => {{
  console.error('GLTF load error:', err);
  document.body.insertAdjacentHTML('beforeend',
    '<div style="color:#f66;position:absolute;top:38%;left:50%;transform:translateX(-50%);' +
    'background:rgba(0,0,0,.85);padding:24px 32px;border-radius:10px;font-size:14px;text-align:center;line-height:2">' +
    '<b>Cannot load sample_console.gltf</b><br>' +
    'Run: <code style="color:#fc0">python -m http.server 8000</code><br>' +
    'Then open: <a href="http://localhost:8000/viewer_dev.html" style="color:#fc0">http://localhost:8000/viewer_dev.html</a>' +
    '</div>');
}});

// ── UI bindings ────────────────────────────────────────────────────────────
function bind(id, spanId, fn) {{
  const el = document.getElementById(id);
  el.addEventListener('input', () => {{
    document.getElementById(spanId).textContent = parseFloat(el.value).toFixed(2);
    fn(parseFloat(el.value));
  }});
}}
bind('rough','rv',  () => applyWoodProps());
bind('cc',   'ccv', () => applyWoodProps());
bind('ccr', 'ccrv', () => applyWoodProps());
bind('ns',   'nsv', () => {{ applyWoodProps(); applyFloorProps(); }});
bind('emi', 'emiv', () => {{ applyWoodProps(); applyFloorProps(); }});
bind('fr',   'frv',  () => applyFloorProps());
bind('fcc', 'fccv',  () => applyFloorProps());
bind('fccr','fccrv', () => applyFloorProps());
bind('expo', 'expv', v => renderer.toneMappingExposure = v);
bind('kl',   'klv',  v => keyLight.intensity  = v);
bind('fl',   'flv',  v => fillLight.intensity = v);
bind('rl',   'rlv',  v => rimLight.intensity  = v);
bind('gs',   'gsv',  v => setInstRepeat(v));
bind('fgs', 'fgsv',  v => setFloorRepeat(v));

const LACQUER_PRESET = {{ rough:0.30, cc:0.90, ccr:0.08, ns:0.70, emi:1.20, fr:0.25, fcc:0.95, fccr:0.05 }};
const MATTE_PRESET   = {{ rough:0.65, cc:0.00, ccr:0.50, ns:0.80, emi:0.50, fr:0.70, fcc:0.00, fccr:0.50 }};

function applyPreset(p) {{
  const ids = ['rough','cc','ccr','ns','emi','fr','fcc','fccr'];
  const spans = ['rv','ccv','ccrv','nsv','emiv','frv','fccv','fccrv'];
  const vals = [p.rough, p.cc, p.ccr, p.ns, p.emi, p.fr, p.fcc, p.fccr];
  ids.forEach((id,i) => {{
    document.getElementById(id).value = vals[i];
    document.getElementById(spans[i]).textContent = vals[i].toFixed(2);
  }});
  applyWoodProps();
  applyFloorProps();
}}

document.getElementById('lacquer').addEventListener('change', e => {{
  scene.environment = e.target.checked ? envTexture : null;
  applyPreset(e.target.checked ? LACQUER_PRESET : MATTE_PRESET);
}});

document.getElementById('tex-inst').addEventListener('change', e => {{
  const entry = INST_TEXTURES[+e.target.value];
  loadTexSet(entry, 'inst', uiv('gs'), set => {{ if(model) applyInstSet(model, set); }});
}});

document.getElementById('tex-floor').addEventListener('change', e => {{
  const entry = FLOOR_TEXTURES[+e.target.value];
  loadTexSet(entry, 'floor', uiv('fgs'), set => {{ applyFloorSet(set); }});
}});

// Local file pickers (diff only)
function setupPicker(inputId, prefix, onTex) {{
  document.getElementById(inputId).addEventListener('change', e => {{
    const file = e.target.files[0]; if (!file) return;
    const url = URL.createObjectURL(file);
    const lbl = document.getElementById(prefix+'-label');
    if(lbl) lbl.textContent = file.name;
    loadMap(url, true, prefix+'-d', uiv(prefix==='inst'?'gs':'fgs'), t => {{
      document.getElementById(prefix+'-n').className = 'dot err';
      document.getElementById(prefix+'-r').className = 'dot err';
      onTex({{ diff:t, nor:null, rough:null }});
    }});
  }});
}}
setupPicker('file-inst',  'inst',  set => {{ if(model) applyInstSet(model, set); }});
setupPicker('file-floor', 'floor', set => applyFloorSet(set));

// Keyboard shortcuts
document.addEventListener('keydown', e => {{
  if(e.code==='KeyA') controls.autoRotate = !controls.autoRotate;
  if(e.code==='KeyR') {{ camera.position.set(-5,4,-5); controls.target.set(0,.8,0); controls.update(); }}
}});
['mousedown','wheel','touchstart'].forEach(ev =>
  canvas.addEventListener(ev, () => {{ controls.autoRotate = false; }})
);

window.addEventListener('resize', () => {{
  camera.aspect = innerWidth/innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
}});

(function tick() {{ requestAnimationFrame(tick); controls.update(); renderer.render(scene, camera); }})();
</script>
</body>
</html>
"""

IMPORTMAP = '<script type="importmap">\n{"imports":{"three":"https://unpkg.com/three@0.158.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.158.0/examples/jsm/"}}\n</script>'

html = HTML_TPL.replace('{{', '{').replace('}}', '}')
html = html.replace('___IMPORTMAP___',   IMPORTMAP)
html = html.replace('___INST_OPTIONS___',  make_options(INST_TEXTURES,  default_idx=2))
html = html.replace('___FLOOR_OPTIONS___', make_options(FLOOR_TEXTURES, default_idx=1))
html = html.replace('___INST_ARRAY___',   make_tex_array(INST_TEXTURES))
html = html.replace('___FLOOR_ARRAY___',  make_tex_array(FLOOR_TEXTURES))

with open("viewer_dev.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"Written viewer_dev.html ({len(html):,} bytes)")
