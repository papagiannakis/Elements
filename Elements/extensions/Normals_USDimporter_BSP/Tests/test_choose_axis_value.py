import numpy as np
from Elements.extensions.Normals_USDimporter_BSP.BSPTree import BSPTree

def make_test_mesh():
    """
    5 triangles:
      - tri 0 intersects both x=0 and z=0 (central triangle)
      - tri 1..4 live in the 4 (x,z) quadrants
    """

    # tri 0: spans across x=0 and z=0
    t0 = np.array([
        [-1.0, 100, -1.0],
        [ 1.0, 100, -1.0],
        [ 0.0, 100,  1.0],
    ], dtype=np.float32)

    t1 = np.array([[-2,0,-2],[-1.5,0,-2],[-2,0,-1.5]], dtype=np.float32)
    t2 = np.array([[ 1.5,0,-2],[ 2,0,-2],[ 2,0,-1.5]], dtype=np.float32)
    t3 = np.array([[-2,0, 1.5],[-1.5,0,2],[-2,0,2]], dtype=np.float32)
    t4 = np.array([[ 1.5,0,1.5],[2,0,1.5],[2,0,2]], dtype=np.float32)

    vertices = np.vstack([t0, t1, t2, t3, t4]).astype(np.float32)

    indices = np.array([
        0,1,2,       # tri 0
        3,4,5,       # tri 1
        6,7,8,       # tri 2
        9,10,11,     # tri 3
        12,13,14     # tri 4
    ], dtype=np.int32)

    return vertices, indices

def test_choose_axis_value():
    verts, inds = make_test_mesh()
    tree = BSPTree(verts, inds, max_depth=1)

    # prepare internal arrays without building the full tree
    tree.indices = inds.reshape(-1, 3).astype(np.int32)
    tri_ids = np.arange(tree.indices.shape[0], dtype=np.int32)

    axis, value = tree.choose_axis_value(tri_ids)

    assert axis in (0, 1, 2)

    # Verify that chosen (axis, value) can split triangles into both sides
    tris = tree.indices[tri_ids]
    v = tree.vertices[tris]
    tri_min = v.min(axis=1)
    tri_max = v.max(axis=1)

    minA = tri_min[:, axis]
    maxA = tri_max[:, axis]

    assert np.any(maxA < value)
    assert np.any(minA > value)