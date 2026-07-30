import numpy as np
from Elements.extensions.Normals_USDimporter_BSP.BSPTree import BSPTree

def test_classify_triangles():
    """
    Verify correct triangle classification and inheritance across a BSP split.

    After building the BSP tree, the test checks that two leaf nodes are created
    and that the intersecting triangle is correctly inherited into both leaves.
    """
     
    # Central triangle intersects x=0, and two side triangles are left/right.
    vertices = np.array([
        # tri 0 (both)
        [-1.0, 0.0, 0.0],
        [ 1.0, 0.0, 0.0],
        [ 0.0, 0.0, 1.0],

        # tri 1 (left)
        [-2.0, 0.0, -1.0],
        [-1.0, 0.0, -1.0],
        [-1.5, 0.0,  0.0],

        # tri 2 (right)
        [ 1.0, 0.0, -1.0],
        [ 2.0, 0.0, -1.0],
        [ 1.5, 0.0,  0.0],
    ], dtype=np.float32)

    indices = np.array([
        0, 1, 2,   # tri 0
        3, 4, 5,   # tri 1
        6, 7, 8,   # tri 2
    ], dtype=np.int32)

    tree = BSPTree(vertices, indices, max_depth=4)
    tree.build()

    # Collect leaves
    stack = [tree.root]
    leaves = []
    while stack:
        n = stack.pop()
        if n.isLeaf():
            leaves.append(n)
        else:
            stack.append(n.left)
            stack.append(n.right)

    # Expect 2 leaves (left/right), and tri 0 inherited into both
    assert len(leaves) == 2
    for leaf in leaves:
        assert 0 in leaf.triangles