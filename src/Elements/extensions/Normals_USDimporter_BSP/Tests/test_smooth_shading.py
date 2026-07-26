import numpy as np

from Elements.extensions.Normals_USDimporter_BSP.normals import generateSmoothNormalsMesh


def test_smooth_shading_does_not_share_vertices():
    """
    This test checks that smooth shading does not duplicate vertices
    when the mesh already uses shared indices.
    """
    V = np.array([
        [0.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [1.0, 1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
    ], dtype=np.float32)
    I = np.array([0, 1, 2,  0, 2, 3], dtype=np.uint32)

    V2, I2, C2, N2 = generateSmoothNormalsMesh(V, I, color=None)

    assert V2.shape[0] == V.shape[0]
    assert I2.shape[0] == I.shape[0]
    assert N2.shape[0] == V2.shape[0]


def test_smooth_shading_normals_make_sense_on_xy_plane():
    """
    This test checks that smooth shading produces reasonable normals
    for a flat surface lying on the XY plane.
    Since all triangles lie on the same plane, all normals should
    """
    V = np.array([
        [0.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [1.0, 1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
    ], dtype=np.float32)
    I = np.array([0, 1, 2,  0, 2, 3], dtype=np.uint32)

    V2, I2, C2, N2 = generateSmoothNormalsMesh(V, I, color=None)

    expected = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    max_err = np.max(np.linalg.norm(N2 - expected, axis=1))
    assert max_err < 1e-4
