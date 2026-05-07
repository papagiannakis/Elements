# This file defines prefabs for common objects 
# like houses, trees, etc.
# it provides functions that return node 
# definitions for these objects,
#  which can be used in the scene graph.

# Example usage:
# house_node = build_house("house1", [0, 0, 0])
# This would create a house prefab with the name "house1" at the origin.

def build_house(name, position):
    return {
        "node_type": "group",
        "name": name,
        "transform": {
            "position": position,
            "scale": [1.0, 1.0, 1.0]
        },
        "children": [
            {
                "node_type": "mesh_object",
                "name": f"{name}_body",
                "shape": "rectangular_prism",
                "transform": {
                    "position": [0.0, 0.5, 0.0],
                    "scale": [1.2, 1.0, 1.2]
                },
                "material": {
                    "color": [0.8, 0.7, 0.5]
                }
            },
            {
                "node_type": "mesh_object",
                "name": f"{name}_roof",
                "shape": "pyramid",
                "transform": {
                    "position": [0.0, 1.0, 0.0],
                    "scale": [1.2, 0.8, 1.2]
                },
                "material": {
                    "color": [0.7, 0.1, 0.1]
                }
            }
        ]
    }

def build_tree(name, position):
    return {
        "node_type": "group",
        "name": name,
        "transform": {
            "position": position,
            "scale": [1.0, 1.0, 1.0]
        },
        "children": [
            {
                "node_type": "mesh_object",
                "name": f"{name}_trunk",
                "shape": "cylinder",
                "transform": {
                    "position": [0.0, 0.22, 0.0],
                    "scale": [0.18, 0.45, 0.18]
                },
                "material": {
                    "color": [0.45, 0.28, 0.12]
                }
            },
            {
                "node_type": "mesh_object",
                "name": f"{name}_crown",
                "shape": "sphere",
                "transform": {
                    "position": [0.0, 0.62, 0.0],
                    "scale": [0.75, 0.75, 0.75]
                },
                "material": {
                    "color": [0.1, 0.6, 0.2]
                }
            }
        ]
    }

def build_gift_box(name, position):
    return {
        "node_type": "group",
        "name": name,
        "transform": {
            "position": position,
            "scale": [1.0, 1.0, 1.0]
        },
        "children": [
            {
                "node_type": "mesh_object",
                "name": f"{name}_box",
                "shape": "cube",
                "transform": {
                    "position": [0.0, 0.3, 0.0],
                    "scale": [0.6, 0.6, 0.6]
                },
                "material": {
                    "color": [0.85, 0.1, 0.2]
                }
            },
            {
                "node_type": "mesh_object",
                "name": f"{name}_ribbon_x",
                "shape": "rectangular_prism",
                "transform": {
                    "position": [0.0, 0.31, 0.0],
                    "scale": [0.62, 0.08, 0.10]
                },
                "material": {
                    "color": [1.0, 0.85, 0.1]
                }
            },
            {
                "node_type": "mesh_object",
                "name": f"{name}_ribbon_z",
                "shape": "rectangular_prism",
                "transform": {
                    "position": [0.0, 0.31, 0.0],
                    "scale": [0.10, 0.08, 0.62]
                },
                "material": {
                    "color": [1.0, 0.85, 0.1]
                }
            }
        ]
    }

def build_street_light(name, position):
    return {
        "node_type": "group",
        "name": name,
        "transform": {
            "position": position,
            "scale": [1.0, 1.0, 1.0]
        },
        "children": [
            # 1. Ο Στύλος (Pole)
            {
                "node_type": "mesh_object",
                "name": f"{name}_pole",
                "shape": "cylinder",
                "transform": {
                    "position": [0.0, 1.25, 0.0],
                    "scale": [0.1, 2.5, 0.1]
                },
                "material": {
                    "color": [0.3, 0.3, 0.3]
                }
            },
            
            {
                "node_type": "mesh_object",
                "name": f"{name}_arm",
                "shape": "rectangular_prism",
                "transform": {
                    "position": [0.3, 2.4, 0.0],  
                    "scale": [0.6, 0.1, 0.1]      
                },
                "material": {
                    "color": [0.3, 0.3, 0.3]
                }
            },
            
            {
                "node_type": "mesh_object",
                "name": f"{name}_lamp",
                "shape": "cube",
                "transform": {
                    "position": [0.6, 2.3, 0.0], 
                    "scale": [0.2, 0.15, 0.2]
                },
                "material": {
                    "color": [1.0, 0.9, 0.0]
                }
            }
        ]
    }