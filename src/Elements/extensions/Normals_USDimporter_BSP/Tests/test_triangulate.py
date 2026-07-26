import numpy as np
from Elements.extensions.Normals_USDimporter_BSP.UsdImporter import triangulate


def test_triangulate_quad():
    """
    This test validates the core triangulation logic used by the USD importer.
    It checks that a quadrilateral face (4 vertices) is correctly decomposed.
    """
    faceVertexCounts = np.array([4], dtype=np.int32)
    faceVertexIndices = np.array([0, 1, 2, 3], dtype=np.int32)

    indices = triangulate(faceVertexCounts, faceVertexIndices)

    assert indices.tolist() == [0, 1, 2, 0, 2, 3]
