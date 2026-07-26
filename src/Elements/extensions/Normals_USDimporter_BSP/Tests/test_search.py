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

def test_search_with_paths_returns_decisions():
    """
    This test expects you to have the version of search that stores decisions:
    path entries like (axis, value, decision) where decision is 'LEFT'/'RIGHT'/'BOTH'.
    """
    verts, inds = make_test_mesh()
    tree = BSPTree(verts, inds, max_depth=8)
    tree.build()

    results = tree.search(tri_id=0)
    assert len(results) >= 1

    valid = {"LEFT", "RIGHT", "BOTH"}

    for _, path in results:
        assert len(path) >= 1
        for axis, value, decision in path:
            assert axis in (0, 1, 2)
            assert isinstance(value, (float, np.floating))
            assert decision in valid

