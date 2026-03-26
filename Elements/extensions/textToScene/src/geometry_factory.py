# Geometry factory functions for different shapes
import numpy as np

def make_color_array(color, count):
    r, g, b = color
    return np.array([[r, g, b, 1.0]] * count, dtype=np.float32)

#-------------------------
# Cube + Rectangular Prism
#-------------------------  
def create_cube(params):
    return create_rectangular_prism({
        "size": [1.0, 1.0, 1.0],
        "color": params.get("color", [0.8, 0.0, 0.8])
    })

def create_rectangular_prism(params):
    sx, sy, sz = params.get("size", [1.0, 1.0, 1.0])
    sx/= 2.0
    sy/= 2.0
    sz/= 2.0
    vertices = np.array([
        [-sx, -sy, -sz, 1],  # 0
        [ sx, -sy, -sz, 1],  # 1
        [ sx,  sy, -sz, 1],  # 2
        [-sx,  sy, -sz, 1],  # 3
        [-sx, -sy,  sz, 1],  # 4
        [ sx, -sy,  sz, 1],  # 5
        [ sx,  sy,  sz, 1],  # 6
        [-sx,  sy,  sz, 1]   # 7
    ], dtype=np.float32)
    
    indices = np.array((
        1,0,3, 1,3,2,
        2,3,7, 2,7,6,
        3,0,4, 3,4,7,
        6,5,1, 6,1,2,
        4,5,6, 4,6,7,
        5,4,0, 5,0,1
    ), dtype=np.uint32)
    colors = make_color_array(params.get("color"), 8)
    return vertices, indices, colors

# ------------------------
# Plane 
# ------------------------

def create_plane(params):
    size = params.get("size", 2.0)
    s = size / 2.0
    vertices = np.array([
        [-s, 0, -s, 1],  # 0
        [ s, 0, -s, 1],  # 1
        [ s, 0,  s, 1],  # 2
        [-s, 0,  s, 1]   # 3
    ], dtype=np.float32)
    indices = np.array((0, 1, 2, 0, 2, 3), dtype=np.uint32)
    colors = make_color_array(params.get("color"), 4)
    return vertices, indices, colors

#-------------------------
# Pyramid (square base)
#-------------------------
def create_pyramid(params):
    h = params.get("height", 1.0)
    s = 0.5

    vertices = np.array([
        [-s, 0, -s, 1],
        [ s, 0, -s, 1],
        [ s, 0,  s, 1],
        [-s, 0,  s, 1],
        [0, h, 0, 1]
    ], dtype=np.float32)

    indices = np.array((
        0,1,2, 0,2,3,
        0,1,4,
        1,2,4,
        2,3,4,
        3,0,4
    ), dtype=np.uint32)
    colors = make_color_array(params.get("color"), 5)
    return vertices, indices, colors

#-------------------------
# Triangular Pyramid (tetrahedron)
#-------------------------
def create_triangular_pyramid(params):
    vertices = np.array([
        [0,1,0,1],
        [-1,0,-1,1],
        [1,0,-1,1],
        [0,0,1,1]
        ], dtype=np.float32)
    indices = np.array((
        0,1,2,
        0,2,3,
        0,3,1,
        1,3,2
    ), dtype=np.uint32)
    colors = make_color_array(params.get("color"), 4)
    return vertices, indices, colors

#----------------------
# cylinder
#----------------------

def create_cylinder(params):
    segments = 20
    radius = 0.5
    height = 1.0

    vertices = []
    indices = []

    for i in range(segments):
        angle = 2 * np.pi * i / segments
        x = radius * np.cos(angle)
        z = radius * np.sin(angle)

        vertices.append([x, -height/2, z, 1])
        vertices.append([x, height/2, z, 1])

    for i in range(segments):
        i1 = i * 2
        i2 = (i * 2 + 2) % (segments * 2)

        indices += [i1, i1+1, i2+1]
        indices += [i1, i2+1, i2]

    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)
    colors = make_color_array(params.get("color"), len(vertices))

    return vertices, indices, colors


# --------------------
# Cone
# --------------------
def create_cone(params):
    segments = 20
    radius = 0.5
    height = 1.0

    vertices = [[0, height/2, 0, 1]]
    indices = []

    for i in range(segments):
        angle = 2*np.pi*i/segments
        x = radius*np.cos(angle)
        z = radius*np.sin(angle)
        vertices.append([x, -height/2, z, 1])

    for i in range(1, segments):
        indices += [0, i, i+1]
    indices += [0, segments, 1]

    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)
    colors = make_color_array(params.get("color"), len(vertices))

    return vertices, indices, colors


# ---------------------
# Sphere 
# ---------------------
def create_sphere(params):
    lat = 10
    lon = 10
    r = 0.5

    vertices = []
    indices = []

    for i in range(lat+1):
        theta = np.pi * i / lat
        for j in range(lon+1):
            phi = 2*np.pi*j/lon

            x = r*np.sin(theta)*np.cos(phi)
            y = r*np.cos(theta)
            z = r*np.sin(theta)*np.sin(phi)

            vertices.append([x,y,z,1])

    for i in range(lat):
        for j in range(lon):
            a = i*(lon+1)+j
            b = a+lon+1

            indices += [a,b,a+1]
            indices += [b,b+1,a+1]

    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)
    colors = make_color_array(params.get("color"), len(vertices))

    return vertices, indices, colors

def create_geometry(shape_type, params):
    if shape_type == "cube":
        return create_cube(params)
    elif shape_type == "rectangular_prism":
        return create_rectangular_prism(params)
    elif shape_type == "plane":
        return create_plane(params)
    elif shape_type == "pyramid":
        return create_pyramid(params)
    elif shape_type == "triangular_pyramid":
        return create_triangular_pyramid(params)
    elif shape_type == "cylinder":
        return create_cylinder(params)
    elif shape_type == "cone":
        return create_cone(params)
    elif shape_type == "sphere":
        return create_sphere(params)
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