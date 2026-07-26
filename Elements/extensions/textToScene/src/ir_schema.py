scene_ir = {
    "node_type": "scene",
    "name": "root",
    "children": [
        {
            "node_type": "mesh_object",
            "shape": "cube",
            "name": "cube1",
            "transform": {
                "position": [0.0, 0.5, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            "material": {
                "color": [0.8, 0.0, 0.8]
            }
        }
    ]
}
# This is a simple IR schema for a scene with one cube. 
# The root node is of type "scene" and has one child, 
# which is a "mesh_object" representing the cube. 
# The cube has a name, shape type, transform properties (position and scale),
#  and material properties (color). 
# This schema can be extended to include more complex scenes 
# with multiple objects, different shapes, 
# and additional properties as needed.