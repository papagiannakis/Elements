import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pathlib import Path
from Elements.extensions.textToScene.src.code_generator import generate_scene_script, save_script

TEXTURES_DIR = Path(__file__).resolve().parents[2] / "assets" / "textures"

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1200,
        "height": 800,
        "title": "Texture Test"
    },
    "children": [

        {
            "node_type": "mesh_object",
            "name": "cube_tex",
            "shape": "cube",
            "transform": {
                "position": [0.0, 0.5, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            "material": {
                "texture": {
                    "enabled": True,
                    "path": str(TEXTURES_DIR / "brick.jpg")
                }
            }
        }

    ]
}

script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")

save_script(script, scene_ir=scene_ir)
print("Saved successfully")
