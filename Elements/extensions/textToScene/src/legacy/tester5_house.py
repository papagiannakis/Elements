import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from code_generator import generate_scene_script, save_script
from prefabs import build_house

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1200,
        "height": 800,
        "title": "House Scene"
    },
    "children": [
        # Warm point light β€” high and to the side, like afternoon sun
        {
            "node_type": "light",
            "name": "sun",
            "light_type": "point",
            "properties": {
                "position": [5.0, 8.0, 5.0],
                "color": [1.0, 0.95, 0.8],
                "intensity": 1.4
            }
        },
        # Green grass ground
        {
            "node_type": "mesh_object",
            "name": "ground",
            "shape": "plane",
            "transform": {
                "position": [0.0, 0.0, 0.0],
                "scale": [10.0, 10.0, 10.0]
            },
            "material": {
                "color": [0.28, 0.55, 0.22]
            }
        },
        build_house("house1", [-1.8, 0.0, 0.0]),
        build_house("house2", [ 1.8, 0.0, 0.0]),
    ]
}

script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")

save_script(script, scene_ir=scene_ir)
print("Saved successfully")
