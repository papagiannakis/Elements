from code_generator import generate_scene_script, save_script
from prefarbs import build_house, build_street_light, build_tree, build_gift_box

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1200,
        "height": 800,
        "title": "Prefabs Test"
    },
    "children": [
        {
            "node_type": "mesh_object",
            "name": "ground",
            "shape": "plane",
            "transform": {
                "position": [0.0, 0.0, 0.0],
                "scale": [14.0, 14.0, 14.0]
            },
            "material": {
                "color": [0.6, 0.6, 0.6]
            }
        },

        build_house("house1", [-3.5, 0.0, 0.0]),
        build_house("house2", [3.0, 0.0, 1.5]),

        build_tree("tree1", [-6.0, 0.0, -1.0]),
        build_tree("tree2", [0.0, 0.0, -2.0]),
        build_tree("tree3", [5.5, 0.0, -1.5]),

        build_street_light("street_light1", [-1.0, 0.0, 2.5])
    ]
}

script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")

save_script(script, r"C:\Users\yanni\Desktop\scene_out.py")
print("Saved successfully")