import numpy as np

from Elements.extensions.Normals_USDimporter_BSP.normals import generateFlatNormalsMesh


def test_flat_shading_makes_indices_unique():
    """
    This test checks that flat shading expands the mesh so that
    each triangle has its own unique vertices.
    """
    V = np.array([
        [0.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [1.0, 1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
    ], dtype=np.float32)
    I = np.array([0, 1, 2,  0, 2, 3], dtype=np.uint32)

    V2, I2, C2, N2 = generateFlatNormalsMesh(V, I, color=None)

    # flat -> 2 triangles -> 6 vertices
    assert V2.shape[0] == 6
    assert np.array_equal(I2, np.arange(6, dtype=np.uint32))


def test_flat_shading_normals_constant_per_triangle():
    """
    This test checks that in flat shading, all three vertices of
    the same triangle have identical normals.
    """
    V = np.array([
        [0.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [1.0, 1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
    ], dtype=np.float32)
    I = np.array([0, 1, 2,  0, 2, 3], dtype=np.uint32)

    V2, I2, C2, N2 = generateFlatNormalsMesh(V, I, color=None)

    for t in range(2):
        n0 = N2[3*t + 0]
        n1 = N2[3*t + 1]
        n2 = N2[3*t + 2]
        assert np.linalg.norm(n0 - n1) < 1e-6
        assert np.linalg.norm(n1 - n2) < 1e-6
