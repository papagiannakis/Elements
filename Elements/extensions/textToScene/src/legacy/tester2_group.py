import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from code_generator import generate_scene_script, save_script

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1200,
        "height": 800,
        "title": "Group with 2 children"
    },
    "children": [
        {
            "node_type": "group",
            "name": "pair1",
            "transform": {
                "position": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            "children": [
                {
                    "node_type": "mesh_object",
                    "name": "cube_left",
                    "shape": "cube",
                    "transform": {
                        "position": [-1.0, 0.5, 0.0],
                        "scale": [1.0, 1.0, 1.0]
                    },
                    "material": {
                        "color": [0.8, 0.0, 0.8]
                    }
                },
                {
                    "node_type": "mesh_object",
                    "name": "cube_right",
                    "shape": "cube",
                    "transform": {
                        "position": [1.0, 0.5, 0.0],
                        "scale": [1.0, 1.0, 1.0]
                    },
                    "material": {
                        "color": [0.0, 0.8, 0.2]
                    }
                }
            ]
        }
    ]
}

script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")

save_script(script, r"C:\Users\yanni\Desktop\scene_out.py")
print("Saved successfully")