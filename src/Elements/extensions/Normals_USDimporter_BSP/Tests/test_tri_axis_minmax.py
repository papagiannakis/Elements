import numpy as np
from Elements.extensions.Normals_USDimporter_BSP.BSPTree import BSPTree

def test_tri_axis_minmax():
    """
    Verify that tri_axis_minmax correctly computes the minimum and maximum
    coordinates of a triangle along each axis.
    """
    vertices = np.array([
        [-1.0,  5.0,  2.0],
        [ 2.0,  7.0, -1.0],
        [ 0.5, -1.0,  1.0],
    ], dtype=np.float32)
    indices = np.array([0, 1, 2], dtype=np.int32)

    tree = BSPTree(vertices, indices, max_depth=1)
    tree.build()

    tri_ids = np.array([0], dtype=np.int32)

    # axis=0 -> x
    minA, maxA = tree.tri_axis_minmax(tri_ids, axis=0)
    assert float(minA[0]) == -1.0
    assert float(maxA[0]) ==  2.0

    # axis=1 -> y
    minA, maxA = tree.tri_axis_minmax(tri_ids, axis=1)
    assert float(minA[0]) == -1.0
    assert float(maxA[0]) ==  7.0

    # axis=2 -> z
    minA, maxA = tree.tri_axis_minmax(tri_ids, axis=2)
    assert float(minA[0]) == -1.0
    assert float(maxA[0]) ==  2.0