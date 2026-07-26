from pxr import Usd, UsdGeom
import tempfile
from Elements.extensions.Normals_USDimporter_BSP.UsdImporter import get_color
from pathlib import Path
import numpy as np
from pxr import UsdGeom

def test_get_color():
    """
    This test ensures that the color extraction function behaves robustly.
    """ 
    
    path = Path(__file__).resolve().parent.parent / "cubes_and_planes.usd"
    stage = Usd.Stage.Open(str(path))
    mesh_prim = None
    for p in stage.Traverse():
        if p.IsA(UsdGeom.Mesh):
            mesh_prim = p
            break

    assert mesh_prim is not None, "No Mesh prim found in USD"

    color = get_color(mesh_prim)

    assert isinstance(color, np.ndarray)
    assert color.shape == (3,)
    assert color.dtype == np.float32

