import numpy as np
import pytest

from Elements.extensions.UV_Mapping.ObjectGenerator import UVObjectGenerator


def test_uv_sphere():
    verts = np.array([
        [1.0, 0.0, 0.0, 1.0],   
        [0.0, 1.0, 0.0, 1.0],   
        [0.0, -1.0, 0.0, 1.0],  
        [0.0, 0.0, 1.0, 1.0],   
    ], dtype=np.float32)

    uvs = UVObjectGenerator.ProjectUV_Sphere(verts)

    assert uvs.shape == (4, 2)

    assert pytest.approx(0.5, rel=1e-6) == float(uvs[0, 1])
    assert pytest.approx(0.5, rel=1e-6) == float(uvs[3, 1])

    
    assert pytest.approx(0.5, rel=1e-6) == float(uvs[0, 0])
    assert pytest.approx(0.25, rel=1e-6) == float(uvs[3, 0])

    pole1_v = float(uvs[1, 1])
    pole2_v = float(uvs[2, 1])
    def is_pole_val(x):
        return min(abs(x - 0.0), abs(x - 1.0)) < 1e-6

    assert is_pole_val(pole1_v)
    assert is_pole_val(pole2_v)


def test_uv_cylinder():
    verts = np.array([
        [1.0, 0.0, 0.0, 1.0],
        [1.0, 2.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 1.0],
    ], dtype=np.float32)

    uvs = UVObjectGenerator.ProjectUV_Cylinder(verts)

    assert uvs.shape == (3, 2)

    
    assert pytest.approx(0.5, rel=1e-6) == float(uvs[0, 0])
    assert pytest.approx(0.5, rel=1e-6) == float(uvs[1, 0])

    assert pytest.approx(0.0, rel=1e-6) == float(uvs[0, 1])

    v1 = float(uvs[1, 1])
    assert min(abs(v1 - 0.0), abs(v1 - 1.0)) < 1e-6

    assert pytest.approx(0.25, rel=1e-6) == float(uvs[2, 0])

    flipped = UVObjectGenerator.ProjectUV_Cylinder(verts, flip_u=True, flip_v=True)
    assert pytest.approx(0.75, rel=1e-6) == float(flipped[2, 0])
    fv = float(flipped[0, 1])
    assert min(abs(fv - 0.0), abs(fv - 1.0)) < 1e-6


def test_auto_project_uv():
    
    tall = np.array([
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 10.0, 0.0, 1.0],
        [0.0, 5.0, 0.0, 1.0],
    ], dtype=np.float32)

    uvs, ptype = UVObjectGenerator.AutoProjectUV(tall, return_type=True)
    assert ptype == 'cylinder'
    assert uvs.shape[0] == tall.shape[0]

   
    cube = np.array([
        [1.0, 1.0, 1.0, 1.0],
        [-1.0, 1.0, -1.0, 1.0],
        [1.0, -1.0, 1.0, 1.0],
    ], dtype=np.float32)

    uvs2, ptype2 = UVObjectGenerator.AutoProjectUV(cube, return_type=True)
    assert ptype2 == 'sphere'
    assert uvs2.shape[0] == cube.shape[0]
