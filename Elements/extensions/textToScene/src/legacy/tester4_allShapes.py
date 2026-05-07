from code_generator import generate_scene_script, save_script

scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1200,
        "height": 800,
        "title": "Shapes on Plane"
    },
    "children": [
        {
            "node_type": "group",
            "name": "scene_group",
            "transform": {
                "position": [0.0, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            "children": [
                {
                    "node_type": "mesh_object",
                    "name": "ground",
                    "shape": "plane",
                    "transform": {
                        "position": [0.0, 0.0, 0.0],
                        "scale": [12.0, 12.0, 12.0]
                    },
                    "material": {
                        "color": [0.6, 0.6, 0.6]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "cube",
                    "shape": "cube",
                    "transform": {
                        "position": [-4.5, 0.35, 0.0],
                        "scale": [0.35, 0.35, 0.35]
                    },
                    "material": {
                        "color": [1.0, 0.0, 0.0]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "rectangular_prism",
                    "shape": "rectangular_prism",
                    "transform": {
                        "position": [-3.0, 0.35, 0.0],
                        "scale": [0.45, 0.30, 0.30]
                    },
                    "material": {
                        "color": [0.0, 1.0, 0.0]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "sphere",
                    "shape": "sphere",
                    "transform": {
                        "position": [-1.5, 0.35, 0.0],
                        "scale": [0.35, 0.35, 0.35]
                    },
                    "material": {
                        "color": [0.0, 0.0, 1.0]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "cylinder",
                    "shape": "cylinder",
                    "transform": {
                        "position": [0.0, 0.4, 0.0],
                        "scale": [0.30, 0.50, 0.30]
                    },
                    "material": {
                        "color": [1.0, 1.0, 0.0]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "cone",
                    "shape": "cone",
                    "transform": {
                        "position": [1.5, 0.4, 0.0],
                        "scale": [0.30, 0.50, 0.30]
                    },
                    "material": {
                        "color": [1.0, 0.0, 1.0]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "pyramid",
                    "shape": "pyramid",
                    "transform": {
                        "position": [3.0, 0.4, 0.0],
                        "scale": [0.35, 0.45, 0.35]
                    },
                    "material": {
                        "color": [0.0, 1.0, 1.0]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "triangular_pyramid",
                    "shape": "triangular_pyramid",
                    "transform": {
                        "position": [4.5, 0.4, 0.0],
                        "scale": [0.35, 0.45, 0.35]
                    },
                    "material": {
                        "color": [1.0, 0.5, 0.0]
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