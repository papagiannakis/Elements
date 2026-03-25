import numpy as np 

DEFAULT_COLOR = (0.8, 0.8, 0.8) # default color for objects

#helper functions for geometry creation
def check_prosimo(value, name:str)-> float:
    # Check if the value is a positive number (prosimo)
    if value is None:
        raise ValueError(f"{name} is required and cannot be None.")
    value = float(value)
    if value <= 0.0: 
        raise ValueError(f"{name} must be a positive number. Got {value}.")
    return value

def get_color(params: dict)-> np.ndarray:
    
    color = params.get("color", DEFAULT_COLOR)

    if len(color) == 3:
        color = (*color, 1.0)
    elif len(color) != 4:
        raise ValueError("Color must have 3 or 4 components: [r,g,b] or [r,g,b,a]")

    return np.array(color, dtype=np.float32)

def make_color(vertex_count: int , color: np.ndarray) -> np.ndarray:
    # Create a vertex color array with the same color for all vertices
    return np.tile(color, (vertex_count, 1))

def convert_to_vec3(vec):
    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)
    colors = np.array(colors, dtype=np.float32)
    return vertices, indices, colors

# Geometry factory functions for different shapes
import numpy as np


def create_cube(params):
    color = params.get("color", [0.8, 0.0, 0.8])

    vertices = np.array([
        [-0.5, -0.5,  0.5, 1.0],
        [-0.5,  0.5,  0.5, 1.0],
        [ 0.5,  0.5,  0.5, 1.0],
        [ 0.5, -0.5,  0.5, 1.0],
        [-0.5, -0.5, -0.5, 1.0],
        [-0.5,  0.5, -0.5, 1.0],
        [ 0.5,  0.5, -0.5, 1.0],
        [ 0.5, -0.5, -0.5, 1.0]
    ], dtype=np.float32)

    indices = np.array((
        1,0,3, 1,3,2,
        2,3,7, 2,7,6,
        3,0,4, 3,4,7,
        6,5,1, 6,1,2,
        4,5,6, 4,6,7,
        5,4,0, 5,0,1
    ), dtype=np.uint32)

    r, g, b = float(color[0]), float(color[1]), float(color[2])
    colors = np.array([
        [r, g, b, 1.0],
        [r, g, b, 1.0],
        [r, g, b, 1.0],
        [r, g, b, 1.0],
        [r, g, b, 1.0],
        [r, g, b, 1.0],
        [r, g, b, 1.0],
        [r, g, b, 1.0]
    ], dtype=np.float32)

    return vertices, indices, colors

def create_geometry(shape_type, params):
    if shape_type == "cube":
        return create_cube(params)
    else:
        raise ValueError("Unsupported shape type: {}".format(shape_type))

#  Main idea: code_generator.py asks for geometry code 
#  for a given shape type and parameters,
#  and it uses the appropriate function to generate
#  that code. Each shape type has its own function
#  that knows how to create the geometry for that 
#  shape based on the provided parameters. 
#  The create_geometry function acts as a dispatcher 
#  that routes the request to the correct function.