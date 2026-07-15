

from Elements.extensions.ImplicitSurface.marching_cubes import MarchingCubes
from Elements.pyGLV.GL.VertexArray import VertexArray
import time


m = MarchingCubes(VertexArray())


def test_iter(n, res):
	start = time.perf_counter()
	for _ in range(n):
		m.update_surface("x**2 + y**2 + x*y*z - 1", [-5, -5, -5], [5, 5, 5], [res, res, res])
	end = time.perf_counter()

	return (end - start) / n

# force compile taichi code
m.update_surface("x", [-5, -5, -5], [5, 5, 5], [10, 10, 10])

for n in [30, 50, 70, 100, 150, 200]:
	print(n, test_iter(100, n))
	
print('finished')