import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from code_generator import generate_scene_script, save_script

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1200,
        "height": 800,
        "title": "Hierarchical Cube Scene"
    },
    "children": [
        {
            "node_type": "mesh_object",
            "name": "cube1",
            "shape": "cube",
            "transform": {
                "position": [0.0, 0.5, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            "material": {
                "color": [0.8, 0.0, 0.8]
            }
        }
    ]
}

script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")
save_script(script, scene_ir=scene_ir)
print("Saved successfully")
