import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Elements.extensions.textToScene.src.code_generator import generate_scene_script, save_script
from Elements.extensions.textToScene.src.prefabs import build_house, build_tree, build_street_light

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1280,
        "height": 720,
        "title": "Text-to-Scene: Neighbourhood"
    },
    "children": [

        # β”€β”€ Lighting β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€
        {
            "node_type": "light",
            "name": "sun",
            "light_type": "directional",
            "properties": {
                "direction": [-0.6, -0.8, -0.4],
                "color": [1.0, 0.92, 0.70],
                "intensity": 1.5
            }
        },
        {
            "node_type": "light",
            "name": "sky_fill",
            "light_type": "directional",
            "properties": {
                "direction": [0.4, -0.3, 0.6],
                "color": [0.65, 0.80, 1.0],
                "intensity": 0.6
            }
        },
        # Two point lights above the lamps β€” warm glow
        {
            "node_type": "light",
            "name": "lamp_glow_left",
            "light_type": "point",
            "properties": {
                "position": [-1.5, 2.8, 0.6],
                "color": [1.0, 0.88, 0.45],
                "intensity": 1.2
            }
        },
        {
            "node_type": "light",
            "name": "lamp_glow_right",
            "light_type": "point",
            "properties": {
                "position": [1.5, 2.8, 0.6],
                "color": [1.0, 0.88, 0.45],
                "intensity": 1.2
            }
        },

        # β”€β”€ Ground β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€
        {
            "node_type": "mesh_object",
            "name": "ground",
            "shape": "plane",
            "transform": {
                "position": [0.0, 0.0, 0.0],
                "scale": [22.0, 22.0, 22.0]
            },
            "material": {"color": [0.48, 0.66, 0.36]}
        },

        # β”€β”€ Houses β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€
        build_house("house_left",  [-2.8, 0.0, -2.0]),
        build_house("house_right", [ 2.8, 0.0, -2.0]),

        # β”€β”€ Trees β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€
        build_tree("tree_left",  [-4.2, 0.0, -0.6]),
        build_tree("tree_right", [ 4.2, 0.0, -0.6]),

        # β”€β”€ Street lamps β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€β”€
        build_street_light("lamp_left",  [-1.5, 0.0, 0.6]),
        build_street_light("lamp_right", [ 1.5, 0.0, 0.6]),
    ]
}

script = generate_scene_script(scene_ir)
compile(script, "tester12_neighbourhood.py", "exec")
print("Syntax OK")
save_script(script, scene_ir=scene_ir)
print("Saved successfully")

