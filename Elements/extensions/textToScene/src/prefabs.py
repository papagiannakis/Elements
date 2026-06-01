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

def build_chair(name, position):
    return {
        "node_type": "group",
        "name": name,
        "transform": {"position": position, "scale": [1.0, 1.0, 1.0]},
        "children": [
            {"node_type": "mesh_object", "name": f"{name}_seat",
             "shape": "cube", "transform": {"position": [0.0, 0.45, 0.0], "scale": [0.5, 0.05, 0.5]},
             "material": {"color": [0.6, 0.4, 0.2]}},
            {"node_type": "mesh_object", "name": f"{name}_back",
             "shape": "cube", "transform": {"position": [0.0, 0.80, -0.23], "scale": [0.5, 0.70, 0.05]},
             "material": {"color": [0.6, 0.4, 0.2]}},
            {"node_type": "mesh_object", "name": f"{name}_leg_fl",
             "shape": "cube", "transform": {"position": [-0.22, 0.225, 0.22], "scale": [0.05, 0.45, 0.05]},
             "material": {"color": [0.5, 0.3, 0.1]}},
            {"node_type": "mesh_object", "name": f"{name}_leg_fr",
             "shape": "cube", "transform": {"position": [0.22, 0.225, 0.22], "scale": [0.05, 0.45, 0.05]},
             "material": {"color": [0.5, 0.3, 0.1]}},
            {"node_type": "mesh_object", "name": f"{name}_leg_bl",
             "shape": "cube", "transform": {"position": [-0.22, 0.225, -0.22], "scale": [0.05, 0.45, 0.05]},
             "material": {"color": [0.5, 0.3, 0.1]}},
            {"node_type": "mesh_object", "name": f"{name}_leg_br",
             "shape": "cube", "transform": {"position": [0.22, 0.225, -0.22], "scale": [0.05, 0.45, 0.05]},
             "material": {"color": [0.5, 0.3, 0.1]}},
        ]
    }


def build_bench(name, position):
    return {
        "node_type": "group",
        "name": name,
        "transform": {"position": position, "scale": [1.0, 1.0, 1.0]},
        "children": [
            {"node_type": "mesh_object", "name": f"{name}_top",
             "shape": "cube", "transform": {"position": [0.0, 0.50, 0.0], "scale": [1.0, 0.08, 0.35]},
             "material": {"color": [0.55, 0.35, 0.15]}},
            {"node_type": "mesh_object", "name": f"{name}_leg_l",
             "shape": "cube", "transform": {"position": [-0.45, 0.25, 0.0], "scale": [0.08, 0.50, 0.35]},
             "material": {"color": [0.45, 0.28, 0.10]}},
            {"node_type": "mesh_object", "name": f"{name}_leg_r",
             "shape": "cube", "transform": {"position": [0.45, 0.25, 0.0], "scale": [0.08, 0.50, 0.35]},
             "material": {"color": [0.45, 0.28, 0.10]}},
        ]
    }


def build_bed(name, position):
    return {
        "node_type": "group",
        "name": name,
        "transform": {"position": position, "scale": [1.0, 1.0, 1.0]},
        "children": [
            {"node_type": "mesh_object", "name": f"{name}_frame",
             "shape": "cube", "transform": {"position": [0.0, 0.12, 0.0], "scale": [0.95, 0.24, 1.8]},
             "material": {"color": [0.5, 0.3, 0.1]}},
            {"node_type": "mesh_object", "name": f"{name}_mattress",
             "shape": "cube", "transform": {"position": [0.0, 0.38, 0.0], "scale": [0.9, 0.28, 1.7]},
             "material": {"color": [0.9, 0.9, 0.85]}},
            {"node_type": "mesh_object", "name": f"{name}_headboard",
             "shape": "cube", "transform": {"position": [0.0, 0.75, -0.88], "scale": [0.95, 0.80, 0.08]},
             "material": {"color": [0.5, 0.3, 0.1]}},
            {"node_type": "mesh_object", "name": f"{name}_pillow",
             "shape": "cube", "transform": {"position": [0.0, 0.55, -0.65], "scale": [0.7, 0.12, 0.35]},
             "material": {"color": [1.0, 1.0, 1.0]}},
        ]
    }


def build_table(name, position):
    return {
        "node_type": "group",
        "name": name,
        "transform": {"position": position, "scale": [1.0, 1.0, 1.0]},
        "children": [
            {"node_type": "mesh_object", "name": f"{name}_top",
             "shape": "cube", "transform": {"position": [0.0, 1.66, 0.0], "scale": [2.0, 0.12, 1.2]},
             "material": {"color": [0.6, 0.4, 0.2]}},
            {"node_type": "mesh_object", "name": f"{name}_leg_fl",
             "shape": "cube", "transform": {"position": [-0.88, 0.8, -0.54], "scale": [0.12, 1.6, 0.12]},
             "material": {"color": [0.5, 0.3, 0.1]}},
            {"node_type": "mesh_object", "name": f"{name}_leg_fr",
             "shape": "cube", "transform": {"position": [0.88, 0.8, -0.54], "scale": [0.12, 1.6, 0.12]},
             "material": {"color": [0.5, 0.3, 0.1]}},
            {"node_type": "mesh_object", "name": f"{name}_leg_bl",
             "shape": "cube", "transform": {"position": [-0.88, 0.8, 0.54], "scale": [0.12, 1.6, 0.12]},
             "material": {"color": [0.5, 0.3, 0.1]}},
            {"node_type": "mesh_object", "name": f"{name}_leg_br",
             "shape": "cube", "transform": {"position": [0.88, 0.8, 0.54], "scale": [0.12, 1.6, 0.12]},
             "material": {"color": [0.5, 0.3, 0.1]}},
        ]
    }


def build_lamp(name, position):
    return {
        "node_type": "group",
        "name": name,
        "transform": {"position": position, "scale": [1.0, 1.0, 1.0]},
        "children": [
            {"node_type": "mesh_object", "name": f"{name}_base",
             "shape": "cylinder", "transform": {"position": [0.0, 0.1, 0.0], "scale": [0.5, 0.2, 0.5]},
             "material": {"color": [0.3, 0.3, 0.3]}},
            {"node_type": "mesh_object", "name": f"{name}_pole",
             "shape": "cylinder", "transform": {"position": [0.0, 1.2, 0.0], "scale": [0.08, 2.0, 0.08]},
             "material": {"color": [0.3, 0.3, 0.3]}},
            {"node_type": "mesh_object", "name": f"{name}_shade",
             "shape": "cone", "transform": {"position": [0.0, 2.35, 0.0], "scale": [0.7, 0.4, 0.7]},
             "material": {"color": [1.0, 0.95, 0.6]}},
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