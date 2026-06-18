import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from code_generator import generate_scene_script, save_script
from prefabs import build_house, build_tree, build_bench

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1280,
        "height": 720,
        "title": "Text-to-Scene: Neighbourhood Park"
    },
    "children": [

        # --- Golden hour sun (warm, from upper-right) ---
        {
            "node_type": "light",
            "name": "sun",
            "light_type": "directional",
            "properties": {
                "direction": [-0.5, -0.7, -0.5],
                "color": [1.0, 0.90, 0.65],
                "intensity": 1.6
            }
        },
        # --- Cool sky fill ---
        {
            "node_type": "light",
            "name": "sky_fill",
            "light_type": "directional",
            "properties": {
                "direction": [0.5, -0.4, 0.5],
                "color": [0.72, 0.85, 1.0],
                "intensity": 0.8
            }
        },

        # --- Ground ---
        {
            "node_type": "mesh_object",
            "name": "ground",
            "shape": "plane",
            "transform": {
                "position": [0.0, 0.0, 0.0],
                "scale": [18.0, 18.0, 18.0]
            },
            "material": {
                "color": [0.50, 0.68, 0.38]
            }
        },

        # --- Stone path ---
        {
            "node_type": "mesh_object",
            "name": "path",
            "shape": "rectangular_prism",
            "transform": {
                "position": [0.0, 0.01, -0.8],
                "scale": [0.65, 0.02, 2.8]
            },
            "material": {
                "color": [0.68, 0.63, 0.52]
            }
        },

        # --- House (back-left) ---
        build_house("house", [-1.6, 0.0, -2.0]),

        # --- Trees ---
        build_tree("tree_right",  [ 1.8, 0.0, -2.0]),
        build_tree("tree_back",   [-0.3, 0.0, -3.2]),
        build_tree("tree_close",  [ 2.4, 0.0, -0.4]),

        # --- Bench (right of path) ---
        build_bench("bench", [0.9, 0.0, 0.5]),

        # --- Fountain base ---
        {
            "node_type": "mesh_object",
            "name": "fountain_base",
            "shape": "cylinder",
            "transform": {
                "position": [0.0, 0.08, -1.2],
                "scale": [0.50, 0.14, 0.50]
            },
            "material": {
                "color": [0.68, 0.66, 0.62]
            }
        },
        {
            "node_type": "mesh_object",
            "name": "fountain_water",
            "shape": "sphere",
            "transform": {
                "position": [0.0, 0.35, -1.2],
                "scale": [0.22, 0.22, 0.22]
            },
            "material": {
                "color": [0.45, 0.74, 0.92]
            }
        },

        # --- Decorative rocks near path ---
        {
            "node_type": "mesh_object",
            "name": "rock1",
            "shape": "sphere",
            "transform": {
                "position": [-0.5, 0.08, 0.3],
                "scale": [0.12, 0.10, 0.14]
            },
            "material": {"color": [0.58, 0.55, 0.52]}
        },
        {
            "node_type": "mesh_object",
            "name": "rock2",
            "shape": "sphere",
            "transform": {
                "position": [-0.6, 0.06, 0.5],
                "scale": [0.09, 0.08, 0.11]
            },
            "material": {"color": [0.55, 0.52, 0.50]}
        },
        {
            "node_type": "mesh_object",
            "name": "rock3",
            "shape": "sphere",
            "transform": {
                "position": [-0.42, 0.07, 0.48],
                "scale": [0.10, 0.08, 0.10]
            },
            "material": {"color": [0.60, 0.57, 0.54]}
        }
    ]
}

script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")

save_script(script, r"C:\Users\yanni\Desktop\scene_out.py")
print("Saved successfully")
