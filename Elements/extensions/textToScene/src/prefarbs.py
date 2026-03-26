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
                    "scale": [1.5, 1.0, 1.5]
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