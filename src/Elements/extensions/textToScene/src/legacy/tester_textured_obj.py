import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Elements.extensions.textToScene.src.code_generator import generate_scene_script, save_script

from Elements.definitions import MODEL_DIR
# str(), not Path: save_script json.dumps the scene_ir these end up in.
CUBE_OBJ     = str(MODEL_DIR / "cube" / "cube.obj")
CUBE_TEX     = str(MODEL_DIR / "cube" / "CubeTexture.png")
HAND_OBJ     = str(MODEL_DIR / "Hand" / "Hand.obj")
HAND_TEX     = str(MODEL_DIR / "Hand" / "HandTexture.png")

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1200,
        "height": 800,
        "title": "Textured OBJ Test"
    },
    "children": [
        {
            "node_type": "light",
            "name": "sun",
            "light_type": "point",
            "properties": {
                "position": [4.0, 6.0, 4.0],
                "color": [1.0, 1.0, 1.0],
                "intensity": 1.5
            }
        },
        # Textured cube OBJ (left)
        {
            "node_type": "mesh_object",
            "name": "textured_cube",
            "shape": "custom",
            "custom_model_path": CUBE_OBJ,
            "transform": {
                "position": [-2.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            "material": {
                "color": [1.0, 1.0, 1.0],
                "texture": {
                    "enabled": True,
                    "path": CUBE_TEX
                }
            }
        },
        # Textured hand OBJ (right)
        {
            "node_type": "mesh_object",
            "name": "textured_hand",
            "shape": "custom",
            "custom_model_path": HAND_OBJ,
            "transform": {
                "position": [2.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            "material": {
                "color": [1.0, 1.0, 1.0],
                "texture": {
                    "enabled": True,
                    "path": HAND_TEX
                }
            }
        },
    ]
}

script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")
save_script(script, scene_ir=scene_ir)
print("Saved successfully")

