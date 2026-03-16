# src/test_codegen.py
from code_generator import generate_scene, save_script

ir = {
    "window": {
        "width": 1200,
        "height": 800,
        "title": "Cube Test"
    },
    "objects": [
        {
            "type": "cube",
            "name": "cube1",
            "position": [0.0, 0.5, 0.0],
            "scale": [1.0, 1.0, 1.0],
            "color": [0.8, 0.0, 0.8]
        }
    ]
}

script = generate_scene(ir)
save_script(script)
print("Scene script generated at generated/scene_out.py")
