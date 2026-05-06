# Geometry factory functions for different shapes
import numpy as np
import Elements.utils.normals as norm
def make_color_array(color, count):
    r, g, b = color
    return np.array([[r, g, b, 1.0]] * count, dtype=np.float32)

HARD_SURFACE_SHAPES = {
    "cube",
    "rectangular_prism",
    "pyramid",
    "triangular_pyramid",
    "plane",
}


def shape_uses_flat_normals(shape_type):
    return str(shape_type).lower() in HARD_SURFACE_SHAPES


def _safe_face_normal(v0, v1, v2):
    edge_1 = v1[:3] - v0[:3]
    edge_2 = v2[:3] - v0[:3]
    normal = np.cross(edge_1, edge_2)
    length = np.linalg.norm(normal)

    if length < 1e-8:
        return np.array([0.0, 1.0, 0.0], dtype=np.float32)

    return (normal / length).astype(np.float32)


def build_flat_shaded_mesh(vertices, indices, colors):
    vertices = np.asarray(vertices, dtype=np.float32)
    indices = np.asarray(indices, dtype=np.uint32)
    colors = np.asarray(colors, dtype=np.float32)

    flat_vertices = []
    flat_colors = []
    flat_normals = []
    flat_indices = []

    triangle_count = len(indices) // 3

    for tri_idx in range(triangle_count):
        ia = int(indices[tri_idx * 3 + 0])
        ib = int(indices[tri_idx * 3 + 1])
        ic = int(indices[tri_idx * 3 + 2])

        v0 = vertices[ia]
        v1 = vertices[ib]
        v2 = vertices[ic]

        c0 = colors[ia]
        c1 = colors[ib]
        c2 = colors[ic]

        normal3 = _safe_face_normal(v0, v1, v2)
        normal4 = np.array([normal3[0], normal3[1], normal3[2], 0.0], dtype=np.float32)

        base_index = len(flat_vertices)

        flat_vertices.extend([v0.tolist(), v1.tolist(), v2.tolist()])
        flat_colors.extend([c0.tolist(), c1.tolist(), c2.tolist()])
        flat_normals.extend([normal4.tolist(), normal4.tolist(), normal4.tolist()])
        flat_indices.extend([base_index, base_index + 1, base_index + 2])

    return (
        np.asarray(flat_vertices, dtype=np.float32),
        np.asarray(flat_indices, dtype=np.uint32),
        np.asarray(flat_colors, dtype=np.float32),
        np.asarray(flat_normals, dtype=np.float32),
    )


def build_smooth_shaded_mesh(vertices, indices, colors):
    vertices = np.asarray(vertices, dtype=np.float32)
    indices = np.asarray(indices, dtype=np.uint32)
    colors = np.asarray(colors, dtype=np.float32)

    normal_sums = np.zeros((len(vertices), 3), dtype=np.float32)
    triangle_count = len(indices) // 3

    for tri_idx in range(triangle_count):
        ia = int(indices[tri_idx * 3 + 0])
        ib = int(indices[tri_idx * 3 + 1])
        ic = int(indices[tri_idx * 3 + 2])

        normal3 = _safe_face_normal(vertices[ia], vertices[ib], vertices[ic])
        normal_sums[ia] += normal3
        normal_sums[ib] += normal3
        normal_sums[ic] += normal3

    normals = []
    for item in normal_sums:
        length = np.linalg.norm(item)
        if length < 1e-8:
            normals.append([0.0, 1.0, 0.0, 0.0])
        else:
            item = item / length
            normals.append([float(item[0]), float(item[1]), float(item[2]), 0.0])

    return (
        vertices.astype(np.float32),
        indices.astype(np.uint32),
        colors.astype(np.float32),
        np.asarray(normals, dtype=np.float32),
    )


def build_render_mesh(shape_type, params):
    vertices, indices, colors = create_geometry(shape_type, params)

    if shape_uses_flat_normals(shape_type):
        return build_flat_shaded_mesh(vertices, indices, colors)

    return build_smooth_shaded_mesh(vertices, indices, colors)


# TEXTURED CUBE  wwith uv map for each fase

def create_textured_cube():
    vertexCube = np.array([
        [-1, -1,  1, 1.0],
        [-1,  1,  1, 1.0],
        [ 1,  1,  1, 1.0],
        [ 1, -1,  1, 1.0], 
        [-1, -1, -1, 1.0], 
        [-1,  1, -1, 1.0], 
        [ 1,  1, -1, 1.0], 
        [ 1, -1, -1, 1.0]
    ], dtype=np.float32)

    indexCube = np.array((
        1,0,3, 1,3,2, 
        2,3,7, 2,7,6,
        3,0,4, 3,4,7,
        6,5,1, 6,1,2,
        4,5,6, 4,6,7,
        5,4,0, 5,0,1
    ), dtype=np.uint32)

    vertices, indices, _ = norm.generateUniqueVertices(vertexCube, indexCube)

    UV_MAP = np.array([
        [0,1],[0,0],[1,0],[0,1],[1,0],[1,1],
        [0,2],[0,0],[2,0],[0,2],[2,0],[2,2],
        [0,2/3],[0,1/3],[1/3,1/3],[0,2/3],[1/3,1/3],[1/3,2/3],
        [1/3,1],[1/3,2/3],[2/3,2/3],[1/3,1],[2/3,2/3],[2/3,1],
        [2/3,1/3],[2/3,0],[1,0],[2/3,1/3],[1,0],[1,1/3],
        [0,1],[0,2/3],[1/3,2/3],[0,1],[1/3,2/3],[1/3,1]
    ], dtype=np.float32)

    return vertices, indices, UV_MAP
#-------------------------
# Cube + Rectangular Prism
#-------------------------  
def create_cube(params):
    scale = params.get("scale", [1.0, 1.0, 1.0])
    color = params.get("color", [0.8, 0.0, 0.8])

    return create_rectangular_prism({
        "scale": scale,
        "color": color
    })

def create_rectangular_prism(params):
    scale = params.get("scale", [1.0, 1.0, 1.0])
    color = params.get("color", [0.8, 0.0, 0.8])

    sx = 0.5 * scale[0]
    sy = 0.5 * scale[1]
    sz = 0.5 * scale[2]
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
    colors = make_color_array(color, len(vertices))
    return vertices, indices, colors

# ------------------------
# Plane 
# ------------------------

def create_plane(params):
    scale = params.get("scale", [1.0, 1.0, 1.0])
    color = params.get("color", [0.8, 0.0, 0.8])

    sx = 0.5 * scale[0]
    sz = 0.5 * scale[2]

    vertices = np.array([
        [-sx, 0, -sz, 1],  # 0
        [ sx, 0, -sz, 1],  # 1
        [ sx, 0,  sz, 1],  # 2
        [-sx, 0,  sz, 1]   # 3
    ], dtype=np.float32)
    indices = np.array((0, 1, 2, 0, 2, 3), dtype=np.uint32)
    colors = make_color_array(color, len(vertices))
    return vertices, indices, colors

#-------------------------
# Pyramid (square base)
#-------------------------
def create_pyramid(params):
    scale = params.get("scale", [1.0, 1.0, 1.0])
    color = params.get("color", [0.8, 0.0, 0.8])
    sx = 0.5 * scale[0]
    sy = scale[1]
    sz = 0.5 * scale[2]
    
    vertices = np.array([
        [-sx, 0, -sz, 1],
        [ sx, 0, -sz, 1],
        [ sx, 0,  sz, 1],
        [-sx, 0,  sz, 1],
        [0, sy, 0, 1]
    ], dtype=np.float32)

    indices = np.array((
        0,1,2, 0,2,3,
        0,1,4,
        1,2,4,
        2,3,4,
        3,0,4
    ), dtype=np.uint32)
    colors = make_color_array(color, len(vertices))
    return vertices, indices, colors

#-------------------------
# Triangular Pyramid (tetrahedron)
#-------------------------
def create_triangular_pyramid(params):
    scale = params.get("scale", [1.0, 1.0, 1.0])
    color = params.get("color", [0.8, 0.0, 0.8])
    sx = 0.5 * scale[0]
    sy = scale[1]
    sz = 0.5 * scale[2]

    vertices = np.array([
        [ 0.0, sy,  0.0, 1.0],   # top
        [-sx, 0.0,  sz, 1.0],
        [ sx, 0.0,  sz, 1.0],
        [ 0.0, 0.0, -sz, 1.0]
    ], dtype=np.float32)

    indices = np.array((
        0,1,2,
        0,2,3,
        0,3,1,
        1,3,2
    ), dtype=np.uint32)
    colors = make_color_array(color, len(vertices))
    return vertices, indices, colors

#----------------------
# cylinder
#----------------------

def create_cylinder(params):
    segments = params.get("segments", 20)
    scale = params.get("scale", [1.0, 1.0, 1.0])
    
    radius_x = params.get("radius", 0.5) * scale[0]
    radius_z = params.get("radius", 0.5) * scale[2]
    height = params.get("height", 1.0) * scale[1]
    color = params.get("color", [0.8, 0.0, 0.8])

    vertices = []
    indices = []

    # ring vertices
    for i in range(segments):
        angle = 2 * np.pi * i / segments
        x = radius_x * np.cos(angle)
        z = radius_z * np.sin(angle)

        # bottom
        vertices.append([x, -height / 2, z, 1.0])
        # top
        vertices.append([x, height / 2, z, 1.0])

    # side faces
    for i in range(segments):
        i_bottom_1 = i * 2
        i_top_1 = i * 2 + 1
        i_bottom_2 = (i * 2 + 2) % (segments * 2)
        i_top_2 = (i * 2 + 3) % (segments * 2)

        indices += [i_bottom_1, i_top_1, i_top_2]
        indices += [i_bottom_1, i_top_2, i_bottom_2]

    # center vertices for caps
    top_center_index = len(vertices)
    vertices.append([0.0, height / 2, 0.0, 1.0])

    bottom_center_index = len(vertices)
    vertices.append([0.0, -height / 2, 0.0, 1.0])

    # top cap
    for i in range(segments):
        top_1 = i * 2 + 1
        top_2 = (i * 2 + 3) % (segments * 2)
        indices += [top_center_index, top_1, top_2]

    # bottom cap
    for i in range(segments):
        bottom_1 = i * 2
        bottom_2 = (i * 2 + 2) % (segments * 2)
        indices += [bottom_center_index, bottom_2, bottom_1]

    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)
    colors = make_color_array(color, len(vertices))

    return vertices, indices, colors


# --------------------
# Cone
# --------------------
def create_cone(params):
    segments = params.get("segments", 20)
    scale = params.get("scale", [1.0, 1.0, 1.0])

    radius = params.get("radius", 0.5) * scale[0]
    height = params.get("height", 1.0) * scale[1]
    color = params.get("color", [0.8, 0.0, 0.8])

    vertices = [[0.0, height / 2, 0.0, 1.0]]
    indices = []

    for i in range(segments):
        angle = 2 * np.pi * i / segments
        x = radius * np.cos(angle)
        z = radius * np.sin(angle)
        vertices.append([x, -height / 2, z, 1.0])

    for i in range(1, segments):
        indices += [0, i, i + 1]
    indices += [0, segments, 1]

    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)
    colors = make_color_array(color, len(vertices))

    return vertices, indices, colors



# ---------------------
# Sphere 
# ---------------------
def create_sphere(params):
    lat = params.get("lat", 10)
    lon = params.get("lon", 10)
    scale = params.get("scale", [1.0, 1.0, 1.0])
    color = params.get("color", [0.8, 0.0, 0.8])

    rx = 0.5 * scale[0]
    ry = 0.5 * scale[1]
    rz = 0.5 * scale[2]

    vertices = []
    indices = []

    for i in range(lat+1):
        theta = np.pi * i / lat
        for j in range(lon+1):
            phi = 2*np.pi*j/lon

            x = rx*np.sin(theta)*np.cos(phi)
            y = ry*np.cos(theta)
            z = rz*np.sin(theta)*np.sin(phi)

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
    elif shape_type == "textured_cube":
        return create_textured_cube()
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