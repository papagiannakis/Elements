import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
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
            "node_type": "light",
            "name": "light_main",
            "light_type": "directional",
            "properties": {
                "direction": [-1.0, -1.0, -1.0],
                "color": [1.0, 1.0, 1.0],
                "intensity": 1.0
            }
        },
        {
            "node_type": "light",
            "name": "light_fill",
            "light_type": "directional",
            "properties": {
                "direction": [0.5, -0.5, 0.5],
                "color": [1.0, 1.0, 1.0],
                "intensity": 0.5
            }
        },
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
                        "color": [0.97, 0.97, 0.96]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "cube",
                    "shape": "cube",
                    "transform": {
                        "position": [-2.7, 0.7, 0.0],
                        "scale": [0.7, 0.7, 0.7]
                    },
                    "material": {
                        "color": [0.95, 0.50, 0.45]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "rectangular_prism",
                    "shape": "rectangular_prism",
                    "transform": {
                        "position": [-1.8, 0.7, 0.0],
                        "scale": [0.9, 0.6, 0.6]
                    },
                    "material": {
                        "color": [0.95, 0.75, 0.30]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "sphere",
                    "shape": "sphere",
                    "transform": {
                        "position": [-0.9, 0.7, 0.0],
                        "scale": [0.7, 0.7, 0.7]
                    },
                    "material": {
                        "color": [0.55, 0.80, 0.60]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "cylinder",
                    "shape": "cylinder",
                    "transform": {
                        "position": [0.0, 0.8, 0.0],
                        "scale": [0.6, 1.0, 0.6]
                    },
                    "material": {
                        "color": [0.40, 0.72, 0.90]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "cone",
                    "shape": "cone",
                    "transform": {
                        "position": [0.9, 0.8, 0.0],
                        "scale": [0.6, 1.0, 0.6]
                    },
                    "material": {
                        "color": [0.70, 0.55, 0.90]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "pyramid",
                    "shape": "pyramid",
                    "transform": {
                        "position": [1.8, 0.8, 0.0],
                        "scale": [0.7, 0.9, 0.7]
                    },
                    "material": {
                        "color": [0.90, 0.52, 0.70]
                    }
                },

                {
                    "node_type": "mesh_object",
                    "name": "triangular_pyramid",
                    "shape": "triangular_pyramid",
                    "transform": {
                        "position": [2.7, 0.8, 0.0],
                        "scale": [0.7, 0.9, 0.7]
                    },
                    "material": {
                        "color": [0.65, 0.85, 0.55]
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

