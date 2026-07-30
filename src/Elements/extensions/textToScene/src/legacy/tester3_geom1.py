import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Elements.extensions.textToScene.src.code_generator import generate_scene_script, save_script
# This is a test script to generate a scene with all the supported shapes,
# and save the generated code to a file. You can run this to verify that
# the geometry generation and code generation are working correctly.
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
            "transform": {
                "position": [0.0, 0.0, 0.0],
                "scale": [0.5, 0.5, 0.5]
            },
            "children": [
                {
                    "node_type": "mesh_object",
                    "name": "cube",
                    "shape": "cube",
                    "transform": {
                        "position": [-6.0, 0.5, 0.0],
                        "scale": [0.6, 0.6, 0.6]
                    },
                    "material": {
                        "color": [1.0, 0.0, 0.0]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "rect",
                    "shape": "rectangular_prism",
                    "transform": {
                        "position": [-3.5, 0.5, 0.0],
                        "scale": [0.8, 0.5, 0.5]
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
                        "position": [-1.0, 0.5, 0.0],
                        "scale": [0.6, 0.6, 0.6]
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
                        "position": [1.5, 0.5, 0.0],
                        "scale": [0.6, 0.8, 0.6]
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
                        "position": [4.0, 0.5, 0.0],
                        "scale": [0.6, 0.8, 0.6]
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
                        "position": [-2.5, 0.5, 3.5],
                        "scale": [0.7, 0.7, 0.7]
                    },
                    "material": {
                        "color": [0.0, 1.0, 1.0]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "tri_pyramid",
                    "shape": "triangular_pyramid",
                    "transform": {
                        "position": [2.5, 0.5, 3.5],
                        "scale": [0.7, 0.7, 0.7]
                    },
                    "material": {
                        "color": [1.0, 0.5, 0.0]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "plane",
                    "shape": "plane",
                    "transform": {
                        "position": [0.0, 0.0, 1.5],
                        "scale": [8.0, 1.0, 8.0]
                    },
                    "material": {
                        "color": [0.5, 0.5, 0.5]
                    }
                }
            ]
        }
    ]
}

script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")

save_script(script, scene_ir=scene_ir)
print("Saved successfully")
