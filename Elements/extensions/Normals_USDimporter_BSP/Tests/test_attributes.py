import numpy as np
from pxr import Usd, UsdGeom

from Elements.extensions.Normals_USDimporter_BSP.UsdImporter import triangulate, triangulate_in_corner_space

def load_attr(prim: Usd.Prim):
    """
    Loads points, indices, normals.
    """

    points = np.array(prim.GetAttribute("points").Get(), dtype=np.float32)

    fvi = np.array(prim.GetAttribute("faceVertexIndices").Get(), dtype=np.int32)
    fvc = np.array(prim.GetAttribute("faceVertexCounts").Get(), dtype=np.int32)

    attr = prim.GetAttribute("normals")
    interpolation = attr.GetMetadata("interpolation")
    normals = np.array(attr.Get(), dtype=np.float32)

    if interpolation == "faceVarying":
        # ===== FLAT SHADING =====
        points = points[fvi]  # unindex
        indices = triangulate_in_corner_space(fvc)

    else:
        # ===== SMOOTH SHADING =====
        indices = triangulate(fvc, fvi).astype(np.uint32)
        normals = np.array(normals, dtype=np.float32)

    return points, indices, normals


def test_attributes_smooth():
    """
    This test checks if points, indices and normals have the proper format when smooth shading is used.
    """

    stage = Usd.Stage.CreateInMemory()
    mesh = UsdGeom.Mesh.Define(stage, "/root/Mesh")

    mesh.CreatePointsAttr([
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
    ])
    mesh.CreateFaceVertexCountsAttr([3])
    mesh.CreateFaceVertexIndicesAttr([0, 1, 2])

    n_attr = mesh.CreateNormalsAttr([
        (0.0, 0.0, 1.0),
        (0.0, 0.0, 1.0),
        (0.0, 0.0, 1.0),
    ])

    n_attr.SetMetadata("interpolation", "vertex")

    points, indices, normals = load_attr(mesh.GetPrim())

    assert points.shape == (3, 3)
    assert indices.shape == (3,)
    assert indices.dtype == np.uint32
    assert normals.shape == (3, 3)
    assert normals.dtype == np.float32


def test_attributes_faceVarying():
    """
    This test checks if points, indices and normals have the proper format when sharp shading is used.
    """

    stage = Usd.Stage.CreateInMemory()
    mesh = UsdGeom.Mesh.Define(stage, "/root/Mesh")

    mesh.CreatePointsAttr([
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
    ])
    mesh.CreateFaceVertexCountsAttr([4])
    mesh.CreateFaceVertexIndicesAttr([0, 1, 2, 3])

    n_attr = mesh.CreateNormalsAttr([
        (0.0, 0.0, 1.0),
        (0.0, 0.0, 1.0),
        (0.0, 0.0, 1.0),
        (0.0, 0.0, 1.0),
    ])
    n_attr.SetMetadata("interpolation", "faceVarying")

    points, indices, normals = load_attr(mesh.GetPrim())

    assert points.shape == (4, 3)

    assert indices.shape == (6,)
    assert indices.dtype == np.uint32
    assert indices.max() <= 3
    assert normals.dtype == np.float32
