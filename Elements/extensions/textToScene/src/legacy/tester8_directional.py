import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from code_generator import generate_scene_script, save_script
from prefabs import build_house, build_tree, build_gift_box

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1200,
        "height": 800,
        "title": "Directional Light Test"
    },
    "children": [
        {
            "node_type": "light",
            "name": "sun1",
            "light_type": "directional",
            "properties": {
                "direction": [1.0, -1.0, -0.5],
                "color": [1.0, 1.0, 1.0],
                "intensity": 1.0
            }
        },

        {
            "node_type": "mesh_object",
            "name": "ground",
            "shape": "plane",
            "transform": {
                "position": [0.0, 0.0, 0.0],
                "scale": [14.0, 1.0, 10.0]
            },
            "material": {
                "color": [0.55, 0.55, 0.55]
            }
        },

        build_house("house1", [-3.0, 0.0, 0.0]),
        build_tree("tree1", [2.5, 0.0, -1.5]),
        build_gift_box("gift1", [1.0, 0.0, 2.0])
    ]
}
print("CHILDREN DEBUG:")
for i, child in enumerate(scene_ir["children"]):
    print(i, type(child), child)
script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")

save_script(script, r"C:\Users\yanni\Desktop\scene_out.py")
print("Saved successfully")