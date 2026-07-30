import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Elements.extensions.textToScene.src.code_generator import generate_scene_script, save_script
from Elements.extensions.textToScene.src.prefabs import build_house, build_street_light, build_tree, build_bench

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1280,
        "height": 720,
        "title": "Village Street"
    },
    "children": [

        {
            "node_type": "light",
            "name": "sun",
            "light_type": "directional",
            "properties": {
                "direction": [-0.6, -0.7, -0.4],
                "color": [1.0, 0.90, 0.62],
                "intensity": 1.6
            }
        },
        
        {
            "node_type": "light",
            "name": "sky_light",
            "light_type": "directional",
            "properties": {
                "direction": [0.5, -0.4, 0.5],
                "color": [0.70, 0.84, 1.0],
                "intensity": 0.7
            }
        },

        {
            "node_type": "mesh_object",
            "name": "ground",
            "shape": "plane",
            "transform": {
                "position": [0.0, 0.0, 0.0],
                "scale": [20.0, 20.0, 20.0]
            },
            "material": {
                "color": [0.48, 0.66, 0.36]
            }
        },

        # --- Road (runs along Z into the distance) ---
        {
            "node_type": "mesh_object",
            "name": "road",
            "shape": "rectangular_prism",
            "transform": {
                "position": [0.0, 0.01, -2.0],
                "scale": [1.1, 0.02, 6.5]
            },
            "material": {
                "color": [0.52, 0.50, 0.48]
            }
        },
        # Road centre dashes
        {
            "node_type": "mesh_object",
            "name": "dash1",
            "shape": "rectangular_prism",
            "transform": {
                "position": [0.0, 0.02, -0.6],
                "scale": [0.06, 0.02, 0.35]
            },
            "material": {"color": [0.92, 0.88, 0.60]}
        },
        {
            "node_type": "mesh_object",
            "name": "dash2",
            "shape": "rectangular_prism",
            "transform": {
                "position": [0.0, 0.02, -1.6],
                "scale": [0.06, 0.02, 0.35]
            },
            "material": {"color": [0.92, 0.88, 0.60]}
        },
        {
            "node_type": "mesh_object",
            "name": "dash3",
            "shape": "rectangular_prism",
            "transform": {
                "position": [0.0, 0.02, -2.6],
                "scale": [0.06, 0.02, 0.35]
            },
            "material": {"color": [0.92, 0.88, 0.60]}
        },
        {
            "node_type": "mesh_object",
            "name": "dash4",
            "shape": "rectangular_prism",
            "transform": {
                "position": [0.0, 0.02, -3.6],
                "scale": [0.06, 0.02, 0.35]
            },
            "material": {"color": [0.92, 0.88, 0.60]}
        },
        {
            "node_type": "mesh_object",
            "name": "pavement_left",
            "shape": "rectangular_prism",
            "transform": {
                "position": [-0.95, 0.01, -2.0],
                "scale": [0.40, 0.02, 6.5]
            },
            "material": {"color": [0.72, 0.69, 0.62]}
        },
        {
            "node_type": "mesh_object",
            "name": "pavement_right",
            "shape": "rectangular_prism",
            "transform": {
                "position": [0.95, 0.01, -2.0],
                "scale": [0.40, 0.02, 6.5]
            },
            "material": {"color": [0.72, 0.69, 0.62]}
        },

    
        build_house("house_left_front", [-2.2, 0.0, -0.8]),
        build_house("house_left_back",  [-2.2, 0.0, -3.0]),
        build_house("house_right_front", [2.5, 0.0, -1.2]),
        build_house("house_right_back",  [2.2, 0.0, -3.4]),

        build_tree("tree1", [-3.6, 0.0, -0.3]),
        build_tree("tree2", [-3.4, 0.0, -2.2]),
        build_tree("tree3", [-1.2, 0.0, -4.2]),
        build_tree("tree4", [ 3.6, 0.0, -0.5]),
        build_tree("tree5", [ 3.5, 0.0, -2.8]),

        build_street_light("lamp_left",  [-0.75, 0.0, -0.7]),
        build_street_light("lamp_right", [ 0.75, 0.0, -2.8]),
        build_bench("bench", [1.25, 0.0, -1.8]),

        {
            "node_type": "mesh_object",
            "name": "post1",
            "shape": "cylinder",
            "transform": {
                "position": [-1.22, 0.18, -0.2],
                "scale": [0.05, 0.35, 0.05]
            },
            "material": {"color": [0.72, 0.55, 0.35]}
        },
        {
            "node_type": "mesh_object",
            "name": "post2",
            "shape": "cylinder",
            "transform": {
                "position": [-1.22, 0.18, -0.7],
                "scale": [0.05, 0.35, 0.05]
            },
            "material": {"color": [0.72, 0.55, 0.35]}
        },
        {
            "node_type": "mesh_object",
            "name": "post3",
            "shape": "cylinder",
            "transform": {
                "position": [-1.22, 0.18, -1.2],
                "scale": [0.05, 0.35, 0.05]
            },
            "material": {"color": [0.72, 0.55, 0.35]}
        },
        {
            "node_type": "mesh_object",
            "name": "fence_rail",
            "shape": "rectangular_prism",
            "transform": {
                "position": [-1.22, 0.28, -0.7],
                "scale": [0.03, 0.04, 1.05]
            },
            "material": {"color": [0.72, 0.55, 0.35]}
        },
    ]
}

script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")

save_script(script, scene_ir=scene_ir)
print("Saved successfully")
