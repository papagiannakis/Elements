from code_generator import generate_scene_script, save_script

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1200,
        "height": 800,
        "title": "All Shapes Test"
    },
    "children": [
        {
            "node_type": "group",
            "name": "shapes",
            "children": [
                {"node_type": "mesh_object", "name": "cube", "shape": "cube",
                 "transform": {"position": [-3,0.5,0]}, "material": {"color":[1,0,0]}},

                {"node_type": "mesh_object", "name": "rect", "shape": "rectangular_prism",
                 "transform": {"position": [-1.5,0.5,0]}, "material": {"color":[0,1,0]}},

                {"node_type": "mesh_object", "name": "pyramid", "shape": "pyramid",
                 "transform": {"position": [0,-1,2]}, "material": {"color":[0,1,1]}},

                {"node_type": "mesh_object", "name": "plane", "shape": "plane",
                 "transform": {"position": [0,0,0]}, "material": {"color":[0.5,0.5,0.5]}},

                {"node_type": "mesh_object", "name": "triangular_pyramid", "shape": "triangular_pyramid",
                 "transform": {"position": [2,0.5,0]}, "material": {"color":[1,0,1]}}

            ]
        }
    ]
}

script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")

save_script(script, r"C:\Users\yanni\Desktop\scene_out.py")
print("Saved successfully")