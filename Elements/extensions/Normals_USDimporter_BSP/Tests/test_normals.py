import numpy as np

from Elements.extensions.Normals_USDimporter_BSP.normals import generateNormals

def test_normals_are_unit_length():
    """
    This test checks that all generated normals have unit length.
    """
    V = np.array([
        [0.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
    ], dtype=np.float32)
    I = np.array([0, 1, 2], dtype=np.uint32)

    N = generateNormals(V, I)

    lengths = np.linalg.norm(N, axis=1)
    assert np.all(np.abs(lengths - 1.0) < 1e-4)


def test_normals_point_to_positive_z():
    """
    This test checks that the normals of a counter-clockwise triangle
    lying on the XY plane point towards the positive Z direction.
    Since the triangle is flat, all vertex normals should be equal.
    """
    V = np.array([
        [0.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
    ], dtype=np.float32)
    I = np.array([0, 1, 2], dtype=np.uint32)

    N = generateNormals(V, I)

    expected = np.array([0.0, 0.0, 1.0], dtype=np.float32)

    for k in range(3):
        assert np.linalg.norm(N[k] - expected) < 1e-4
