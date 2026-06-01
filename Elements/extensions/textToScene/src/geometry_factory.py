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


# ============================================================
# Textured mesh builders — return (vertices, indices, uvs)
# Vertices are unit-sized; the transform TRS handles position/rotation.
# UV coordinates are in [0,1]² appropriate for each shape's geometry.
# ============================================================

def _textured_box(params):
    """Box/cube UV mapping — six faces each tiled [0,1]²."""
    scale = params.get("scale", [1.0, 1.0, 1.0])
    sx, sy, sz = 0.5 * scale[0], 0.5 * scale[1], 0.5 * scale[2]

    # 24 unique vertices (4 per face) so each face gets clean [0,1]² UVs
    verts = np.array([
        # +Z front
        [-sx, -sy,  sz, 1], [ sx, -sy,  sz, 1], [ sx,  sy,  sz, 1], [-sx,  sy,  sz, 1],
        # -Z back
        [ sx, -sy, -sz, 1], [-sx, -sy, -sz, 1], [-sx,  sy, -sz, 1], [ sx,  sy, -sz, 1],
        # +X right
        [ sx, -sy,  sz, 1], [ sx, -sy, -sz, 1], [ sx,  sy, -sz, 1], [ sx,  sy,  sz, 1],
        # -X left
        [-sx, -sy, -sz, 1], [-sx, -sy,  sz, 1], [-sx,  sy,  sz, 1], [-sx,  sy, -sz, 1],
        # +Y top
        [-sx,  sy,  sz, 1], [ sx,  sy,  sz, 1], [ sx,  sy, -sz, 1], [-sx,  sy, -sz, 1],
        # -Y bottom
        [-sx, -sy, -sz, 1], [ sx, -sy, -sz, 1], [ sx, -sy,  sz, 1], [-sx, -sy,  sz, 1],
    ], dtype=np.float32)

    face_uvs = np.array([[0,0],[1,0],[1,1],[0,1]], dtype=np.float32)
    uvs = np.tile(face_uvs, (6, 1))

    # Two triangles per face
    base = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
    indices = np.concatenate([base + i * 4 for i in range(6)])

    return verts, indices, uvs


def _textured_plane(params):
    """Flat plane, UVs span [0,1]² across the surface."""
    scale = params.get("scale", [1.0, 1.0, 1.0])
    sx, sz = 0.5 * scale[0], 0.5 * scale[2]

    verts = np.array([
        [-sx, 0,  sz, 1], [ sx, 0,  sz, 1],
        [ sx, 0, -sz, 1], [-sx, 0, -sz, 1],
    ], dtype=np.float32)
    uvs = np.array([[0, 1], [1, 1], [1, 0], [0, 0]], dtype=np.float32)
    indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)

    return verts, indices, uvs


def _textured_sphere(params):
    """Spherical UV mapping: u = longitude / 2π, v = latitude / π."""
    lat = params.get("lat", 20)
    lon = params.get("lon", 20)
    scale = params.get("scale", [1.0, 1.0, 1.0])
    rx, ry, rz = 0.5 * scale[0], 0.5 * scale[1], 0.5 * scale[2]

    verts, uvs = [], []
    for i in range(lat + 1):
        theta = np.pi * i / lat
        v = i / lat
        for j in range(lon + 1):
            phi = 2 * np.pi * j / lon
            u = j / lon
            verts.append([rx * np.sin(theta) * np.cos(phi),
                           ry * np.cos(theta),
                           rz * np.sin(theta) * np.sin(phi), 1.0])
            uvs.append([u, v])

    indices = []
    for i in range(lat):
        for j in range(lon):
            a = i * (lon + 1) + j
            b = a + lon + 1
            indices += [a, b, a + 1, b, b + 1, a + 1]

    return (np.array(verts, dtype=np.float32),
            np.array(indices, dtype=np.uint32),
            np.array(uvs, dtype=np.float32))


def _textured_cylinder(params):
    """Cylindrical UV: side uses u=angle, v=height; caps use planar disk UV."""
    segments = params.get("segments", 20)
    scale = params.get("scale", [1.0, 1.0, 1.0])
    r, h = 0.5 * scale[0], 0.5 * scale[1]

    verts, uvs, indices = [], [], []

    # --- Side (segments+1 pairs of bottom/top) ---
    for i in range(segments + 1):
        u = i / segments
        angle = 2 * np.pi * i / segments
        x, z = r * np.cos(angle), r * np.sin(angle)
        verts.append([x, -h, z, 1.0]); uvs.append([u, 0.0])
        verts.append([x,  h, z, 1.0]); uvs.append([u, 1.0])

    for i in range(segments):
        b1, t1 = i * 2, i * 2 + 1
        b2, t2 = b1 + 2, t1 + 2
        indices += [b1, b2, t2, b1, t2, t1]

    # --- Top cap ---
    tc = len(verts)
    verts.append([0.0, h, 0.0, 1.0]); uvs.append([0.5, 0.5])
    for i in range(segments):
        angle = 2 * np.pi * i / segments
        x, z = r * np.cos(angle), r * np.sin(angle)
        verts.append([x, h, z, 1.0])
        uvs.append([0.5 + 0.5 * np.cos(angle), 0.5 + 0.5 * np.sin(angle)])
    for i in range(segments):
        a = tc + 1 + i
        b = tc + 1 + (i + 1) % segments
        indices += [tc, a, b]

    # --- Bottom cap ---
    bc = len(verts)
    verts.append([0.0, -h, 0.0, 1.0]); uvs.append([0.5, 0.5])
    for i in range(segments):
        angle = 2 * np.pi * i / segments
        x, z = r * np.cos(angle), r * np.sin(angle)
        verts.append([x, -h, z, 1.0])
        uvs.append([0.5 + 0.5 * np.cos(angle), 0.5 + 0.5 * np.sin(angle)])
    for i in range(segments):
        a = bc + 1 + i
        b = bc + 1 + (i + 1) % segments
        indices += [bc, b, a]  # reversed winding for bottom

    return (np.array(verts, dtype=np.float32),
            np.array(indices, dtype=np.uint32),
            np.array(uvs, dtype=np.float32))


def _textured_cone(params):
    """Conical UV: side uses u=angle, v=0 at apex → 1 at base; base cap planar."""
    segments = params.get("segments", 20)
    scale = params.get("scale", [1.0, 1.0, 1.0])
    r, h = 0.5 * scale[0], 0.5 * scale[1]

    verts, uvs, indices = [], [], []

    # --- Side: apex + base ring, unique vertex per segment for clean UVs ---
    for i in range(segments):
        u = i / segments
        u_next = (i + 1) / segments
        angle      = 2 * np.pi * i / segments
        angle_next = 2 * np.pi * (i + 1) / segments

        apex = len(verts)
        verts.append([0.0, h, 0.0, 1.0]);                                       uvs.append([u + 0.5 / segments, 0.0])
        verts.append([r * np.cos(angle),      -h, r * np.sin(angle),      1.0]); uvs.append([u,      1.0])
        verts.append([r * np.cos(angle_next), -h, r * np.sin(angle_next), 1.0]); uvs.append([u_next, 1.0])
        indices += [apex, apex + 1, apex + 2]

    # --- Base cap ---
    bc = len(verts)
    verts.append([0.0, -h, 0.0, 1.0]); uvs.append([0.5, 0.5])
    for i in range(segments):
        angle = 2 * np.pi * i / segments
        x, z = r * np.cos(angle), r * np.sin(angle)
        verts.append([x, -h, z, 1.0])
        uvs.append([0.5 + 0.5 * np.cos(angle), 0.5 + 0.5 * np.sin(angle)])
    for i in range(segments):
        a = bc + 1 + i
        b = bc + 1 + (i + 1) % segments
        indices += [bc, b, a]

    return (np.array(verts, dtype=np.float32),
            np.array(indices, dtype=np.uint32),
            np.array(uvs, dtype=np.float32))


def _textured_pyramid(params):
    """Square-base pyramid: base gets [0,1]² UV, each side face gets a unit triangle UV."""
    scale = params.get("scale", [1.0, 1.0, 1.0])
    sx, sy, sz = 0.5 * scale[0], scale[1], 0.5 * scale[2]

    base_corners = [
        [-sx, 0, -sz, 1], [ sx, 0, -sz, 1],
        [ sx, 0,  sz, 1], [-sx, 0,  sz, 1],
    ]
    apex = [0, sy, 0, 1]

    verts, uvs, indices = [], [], []

    # Base (2 triangles, 4 unique verts)
    base_start = 0
    for c in base_corners:
        verts.append(c)
    uvs += [[0, 0], [1, 0], [1, 1], [0, 1]]
    indices += [0, 1, 2, 0, 2, 3]

    # Four side faces
    side_order = [(0, 1), (1, 2), (2, 3), (3, 0)]
    for a_idx, b_idx in side_order:
        s = len(verts)
        verts.append(base_corners[a_idx])
        verts.append(base_corners[b_idx])
        verts.append(apex)
        uvs += [[0, 0], [1, 0], [0.5, 1]]
        indices += [s, s + 1, s + 2]

    return (np.array(verts, dtype=np.float32),
            np.array(indices, dtype=np.uint32),
            np.array(uvs, dtype=np.float32))


def _textured_triangular_pyramid(params):
    """Tetrahedron: each of the 4 faces gets an independent unit triangle UV."""
    scale = params.get("scale", [1.0, 1.0, 1.0])
    sx, sy, sz = 0.5 * scale[0], scale[1], 0.5 * scale[2]

    p = [
        [ 0.0,  sy,  0.0, 1.0],
        [-sx,  0.0,  sz,  1.0],
        [ sx,  0.0,  sz,  1.0],
        [ 0.0, 0.0, -sz,  1.0],
    ]
    faces = [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)]
    tri_uvs = [[0, 0], [1, 0], [0.5, 1]]

    verts, uvs, indices = [], [], []
    for f in faces:
        s = len(verts)
        for vi in f:
            verts.append(p[vi])
        uvs += tri_uvs
        indices += [s, s + 1, s + 2]

    return (np.array(verts, dtype=np.float32),
            np.array(indices, dtype=np.uint32),
            np.array(uvs, dtype=np.float32))


def create_textured_mesh(shape_type, params):
    """Return (vertices, indices, uvs) for *shape_type* with UV coordinates.

    Each returned array has matching length (len(vertices) == len(uvs)).
    Use this instead of create_textured_cube() when the shape is not known
    to be a cube at generation time.
    """
    shape_type = str(shape_type).lower()
    dispatch = {
        "cube":               _textured_box,
        "rectangular_prism":  _textured_box,
        "plane":              _textured_plane,
        "sphere":             _textured_sphere,
        "cylinder":           _textured_cylinder,
        "cone":               _textured_cone,
        "pyramid":            _textured_pyramid,
        "triangular_pyramid": _textured_triangular_pyramid,
    }
    fn = dispatch.get(shape_type)
    if fn is None:
        # Fallback for unknown shapes: spherical UV projection on the untextured mesh
        vertices, indices, colors = create_geometry(shape_type, params)
        uvs = []
        for v in vertices:
            x, y, z = float(v[0]), float(v[1]), float(v[2])
            length = (x*x + y*y + z*z) ** 0.5
            if length < 1e-8:
                uvs.append([0.5, 0.5])
            else:
                u = 0.5 + np.arctan2(z, x) / (2 * np.pi)
                v_coord = 0.5 - np.arcsin(max(-1.0, min(1.0, y / length))) / np.pi
                uvs.append([float(u), float(v_coord)])
        return vertices, indices, np.array(uvs, dtype=np.float32)
    return fn(params)