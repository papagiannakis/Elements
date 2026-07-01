import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from code_generator import generate_scene_script, save_script

_MODELS   = r"C:\Users\yanni\Documents\GitHub\Elements\Elements\extensions\textToScene\models"
BASEBALL  = _MODELS + r"\ball_baseball_realistic.usdz"
TEAPOT    = _MODELS + r"\teapot.usdz"
CHAMELEON = _MODELS + r"\chameleon_anim_mtl_variant.usdz"

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {"width": 1200, "height": 800, "title": "USDZ Own Texture Test"},
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
        {
            "node_type": "mesh_object",
            "name": "baseball",
            "shape": "custom",
            "custom_model_path": BASEBALL,
            "transform": {
                "position": [-2.5, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "rotation": [0.0, 0.0, 0.0]
            },
            "material": {"color": [1.0, 1.0, 1.0]}
        },
        {
            "node_type": "mesh_object",
            "name": "teapot",
            "shape": "custom",
            "custom_model_path": TEAPOT,
            "transform": {
                "position": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "rotation": [0.0, 0.0, 0.0]
            },
            "material": {"color": [1.0, 1.0, 1.0]}
        },
        {
            "node_type": "mesh_object",
            "name": "chameleon",
            "shape": "custom",
            "custom_model_path": CHAMELEON,
            "transform": {
                "position": [2.5, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0],
                "rotation": [0.0, 0.0, 0.0]
            },
            "material": {"color": [1.0, 1.0, 1.0]}
        },
    ]
}

script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")
save_script(script)
print("Saved — run: python C:\\Users\\yanni\\.textToScene\\scene_out.py")
