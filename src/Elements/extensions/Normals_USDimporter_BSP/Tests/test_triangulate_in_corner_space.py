import numpy as np
from Elements.extensions.Normals_USDimporter_BSP.UsdImporter import triangulate_in_corner_space

def test_single_quad():
    faceVertexCounts = np.array([4], dtype=np.int32)

    indices = triangulate_in_corner_space(faceVertexCounts)

    assert indices.tolist() == [0, 1, 2, 0, 2, 3]
