'''
Marching cubes and 2D surface generation.

author: Kostis Lymperakis (kostis1101.github.io)
'''

import numpy as np
import time
# import numexpr as ne
import math
from Elements.extensions.ImplicitSurface.triangulation_table import Ttable, Ttable2

from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.utils.normals import generateNormals

import taichi as ti

# CPU seems to runs. The delay with datatrasfer is not worth the small performance gain
ti.init(arch=ti.cpu)

try:
	from numexpr import evaluate
except:
	evaluate = eval
	print('Module numexpr not found, using native evaluation!')


from numpy import sin, cos, tan, arcsin, arccos, arctan
from numpy import sinh, cosh, tanh, arcsinh, arccosh, arctanh
from numpy import floor, ceil, rint
from numpy import exp, exp2, log, log10, log2, sinc
from numpy import gcd, lcm, mod, remainder
from numpy import power
from numpy import maximum, minimum
from numpy import sqrt, cbrt


class InvalidExpression(Exception):
	def __init__(self, message):
		super().__init__(message)

def save_obj(filename, verts, norms, tris):
	'''a very simple mesh to wavefront file function'''
	with open(filename, 'w') as file:
		file.write('v ' + '\nv '.join(f"{v[0]} {v[1]} {v[2]}" for v in verts))
		file.write('\n\nvn ' + '\nvn '.join(f"{vn[0]} {vn[1]} {vn[2]}" for vn in norms))
		file.write('\n\nf ' + '\nf '.join(f"{t[0] + 1} {t[1] + 1} {t[2] + 1}" for t in [tris[n:n+3] for n in range(0, len(tris), 3)]))


## TAICHI Precomputed stuff
__ti_neighbour_coords = ti.Vector.field(n=3, dtype=int, shape=3)
__ti_neighbour_coords[0] = [1, 0, 0]
__ti_neighbour_coords[1] = [0, 1, 0]
__ti_neighbour_coords[2] = [0, 0, 1]

neighbour_coords = np.array([
	[1, 0, 0], [0, 1, 0], [0, 0, 1]
])

ti_Ttable = ti.field(int, shape=Ttable2.shape)
ti_Ttable.from_numpy(Ttable2)

# map (reduced hindex, edge index) -> vertex index offest
rh_ei2vo = np.array([
	[0, 0, 0],
	[0, 1, 2],
	[0, 0, 0],
	[0, 0, 1],
	[0, 0, 1],
	[0, 1, 1],
	[0, 1, 1],
	[0, 1, 0],
	[0, 1, 0],
	[0, 1, 1],
	[0, 1, 1],
	[0, 0, 1],
	[0, 0, 1],
	[0, 0, 0],
	[0, 1, 2],
	[0, 0, 0]
])

# converting to taichi data structures
ti_rh_ei2vo = ti.field(ti.int32, shape=(16, 3))
ti_rh_ei2vo.from_numpy(rh_ei2vo)

hi2tc = np.array([0, 3, 3, 6, 3, 6, 6, 9, 3, 6, 6, 9, 6, 9, 9, 6, 3, 6, 6, 9, 6, 9, 9, 12, 6, 9, 9, 12, 9, 12, 12, 9, 3, 6, 6, 9, 6, 9, 9, 12, 6, 9, 9, 12, 9, 12, 12, 9, 6, 9, 9, 6, 9, 12, 12, 9, 9, 12, 12, 9, 12, 9, 9, 6, 3, 6, 6, 9, 6, 9, 9, 12, 6, 9, 9, 12, 9, 12, 12, 9, 6, 9, 9, 12, 9, 6, 12, 9, 9, 12, 12, 9, 12, 9, 9, 6, 6, 9, 9, 12, 9, 12, 12, 9, 9, 12, 12, 9, 12, 9, 9, 6, 9, 12, 12, 9, 12, 9, 9, 6, 12, 9, 9, 6, 9, 6, 6, 3, 3, 6, 6, 9, 6, 9, 9, 12, 6, 9, 9, 12, 9, 12, 12, 9, 6, 9, 9, 12, 9, 12, 12, 9, 9, 12, 12, 9, 12, 9, 9, 6, 6, 9, 9, 12, 9, 12, 12, 9, 9, 12, 6, 9, 12, 9, 9, 6, 9, 12, 12, 9, 12, 9, 9, 6, 12, 9, 9, 6, 9, 6, 6, 3, 6, 9, 9, 12, 9, 12, 12, 9, 9, 12, 12, 9, 6, 9, 9, 6, 9, 12, 12, 9, 12, 9, 9, 6, 12, 9, 9, 6, 9, 6, 6, 3, 9, 12, 12, 9, 12, 9, 9, 6, 12, 9, 9, 6, 9, 6, 6, 3, 6, 9, 9, 6, 9, 6, 6, 3, 9, 6, 6, 3, 6, 3, 3, 0])
ti_hi2tc = ti.field(ti.int8, shape=hi2tc.shape)
ti_hi2tc.from_numpy(hi2tc)

'''double-face vertex shader'''
Surface3D_VERT = """
#version 410

layout (location=0) in vec4 vPosition;
layout (location=1) in vec4 vNormal;

out vec3 position;
out vec3 normal;

uniform mat4 modelViewProj;
uniform mat4 model;

void main()
{
    gl_Position = modelViewProj * vPosition;
    position = (model * vPosition).xyz;
    normal = mat3(transpose(inverse(model))) * vNormal.xyz;
    normal = normalize(normal);
}
"""

'''double-face fragmant shader'''
Surface3D_FRAG = """
#version 410

uniform vec3 colour_front;
uniform vec3 colour_back;
uniform vec3 view_pos;

uniform float specular_strength;

in vec3 position;
in vec3 normal;

out vec4 outputColor;

void main()
{
	vec3 lighting_dir = vec3(-0.71f, 0.71f, 0.0f);
	vec3 view_dir = normalize(view_pos - position);
    vec3 reflectDir = reflect(-lighting_dir, normal);

	float diffuseStr = (dot(normal, lighting_dir) + 2) / 3;
	float specularStr = pow(max(dot(view_dir, reflectDir), 0.0), 32) * specular_strength;
	float ambientStr = 0.2f;
	float lightIntensity = 0.7f;

	float factor = ambientStr + (diffuseStr + specularStr) * lightIntensity; // (pow(dot(lighting_dir, normal), 5) + 1) / 2;

	if (dot(normal, view_dir) >= 0) {
		outputColor = vec4(colour_front - normal * 0.07f, 1.0f);
	}
	else {
		outputColor = vec4(colour_back - normal * 0.07f, 1.0f);
	}

	outputColor *= factor;

	// outputColor = vec4(normal, 1.f);
}

"""



@ti.func
def hindex2redh(x):
	return ((x >> 1) & 0b1000) | (x & 0b0111)

@ti.kernel
def get_verts_taichi(
		ti_values: ti.types.ndarray(), coords: ti.types.ndarray(), verts: ti.types.ndarray(), ti_sign: ti.types.ndarray(),
		ti_vertex_indices_start: ti.types.ndarray(), maxv: ti.types.vector(3, float), minv: ti.types.vector(3, float),
		res: ti.types.vector(3, int)
	):
	'''generate verticies for the taichi implementation'''
	
	ti_transf = (maxv - minv) / res

	for i in range(coords.shape[0]):
		x = coords[i, 0]
		y = coords[i, 1]
		z = coords[i, 2]

		# value at current point
		v1 = ti_values[x, y, z]
		s = ti_sign[x, y, z]

		nv = ti_vertex_indices_start[x, y, z]
		c = ti.Vector([x, y, z])
		for L in ti.static(range(3)):
			u = __ti_neighbour_coords[L]
			if ti_sign[x + u.x, y + u.y, z + u.z] != s: # there should be a vertex between (x, y, z) and (x, y, z) + u
				v2 = ti_values[x + u.x, y + u.y, z + u.z]
				t = 0.5
				if v2 != v1 and not ti.math.isinf(v1) and not ti.math.isinf(v2):
					t = v1 / (v1 - v2)

				# interpolate between the two vertecies according the there values -> approximate the root
				v = (c + u * t) * ti_transf + minv
				verts[nv, 0] = v.x
				verts[nv, 1] = v.y
				verts[nv, 2] = v.z
				nv += 1

@ti.kernel
def get_verts_norms_taichi(
		ti_values: ti.types.ndarray(), coords: ti.types.ndarray(), values: ti.types.ndarray(), verts: ti.types.ndarray(), norms: ti.types.ndarray(),
		ti_sign: ti.types.ndarray(), ti_vertex_indices_start: ti.types.ndarray(), maxv: ti.types.vector(3, float), minv: ti.types.vector(3, float),
		res: ti.types.vector(3, int)
	):
	'''generates verticies and normals for the taichi implementation'''
	
	ti_transf = (maxv - minv) / res
	ti_transf = ti_transf

	zero = -res * minv / (maxv - minv)

	for i in range(coords.shape[0]):
		x = coords[i, 0]
		y = coords[i, 1]
		z = coords[i, 2]

		v1 = ti_values[x, y, z]
		s = ti_sign[x, y, z]
		nv = ti_vertex_indices_start[x, y, z]
		c = ti.Vector([x, y, z])
		for L in ti.static(range(3)):
			u = __ti_neighbour_coords[L]
			x2 = x + u.x
			y2 = y + u.y
			z2 = z + u.z
			if ti_sign[x2, y2, z2] != s: # there should be a vertex between (x, y, z) and (x, y, z) + u
				v2 = ti_values[x2, y2, z2]
				t = 0.5
				if v2 != v1 and not ti.math.isinf(v1) and not ti.math.isinf(v2):
					t = v1 / (v1 - v2)

				# interpolate between the two vertecies according the there values -> approximate the root
				v = (c + u * t) * ti_transf + minv
				verts[nv, 0] = v.x
				verts[nv, 1] = v.y
				verts[nv, 2] = v.z

				# approximation of the gradient at (x, y, z)
				g0 = ti.Vector([
					values[x + 1, y, z] - v1,
					values[x, y + 1, z] - v1,
					values[x, y, z + 1] - v1,
				])

				# apploximation of the gradient at (x2, y2, z2)
				g1 = g0
				if x2 != res[0] and y2 != res[1] and z2 != res[2]:
					g1 = ti.Vector([
						values[x2 + 1, y2, z2] - v2,
						values[x2, y2 + 1, z2] - v2,
						values[x2, y2, z2 + 1] - v2,
					])

				# interpolate gradient and normalize
				n = g0 * (1 - t) + g1 * t
				n = n / ti.math.length(n)
				norms[nv, 0] = n.x
				norms[nv, 1] = n.y
				norms[nv, 2] = n.z

				nv += 1

@ti.kernel
def get_tris_taichi(
		coords: ti.types.ndarray(), ti_tris: ti.types.ndarray(), ti_hindex: ti.types.ndarray(),
		ti_triangle_index_start: ti.types.ndarray(), ti_vertex_indices_start: ti.types.ndarray(), res: ti.types.vector(3, int)
	):
	'''generates triangles for the taichi implementation'''
	for i in range(coords.shape[0]):
		x = coords[i, 0]
		y = coords[i, 1]
		z = coords[i, 2]
		if x < res[0] - 1 and y < res[1] - 1 and z < res[2] - 1:
			h = int(ti_hindex[x, y, z])
			if h < 0:
				h = h + 256

			tind = ti_triangle_index_start[x, y, z]

			for t in range(ti_hi2tc[h]):
				cx = x + ti_Ttable[h, 4 * t + 0]
				cy = y + ti_Ttable[h, 4 * t + 1]
				cz = z + ti_Ttable[h, 4 * t + 2]
				credh = hindex2redh(ti_hindex[cx, cy, cz])
				ti_tris[tind] = ti_vertex_indices_start[cx, cy, cz] + ti_rh_ei2vo[credh, ti_Ttable[h, 4 * t + 3]]
				tind += 1


@ti.kernel
def get_hindex(hindex: ti.types.ndarray(), coords_hindex: ti.types.ndarray(), sign: ti.types.ndarray()):
	''' auxilary kernel for the taichi implementation'''
	for i, j, k in ti.ndrange(*hindex.shape):
		h = (sign[i, j, k]     << 0) | (sign[i, j + 1, k]     << 2) | (sign[i, j, k + 1]     << 4) | (sign[i, j + 1, k + 1]     << 6) | \
			(sign[i + 1, j, k] << 1) | (sign[i + 1, j + 1, k] << 3) | (sign[i + 1, j, k + 1] << 5) | (sign[i + 1, j + 1, k + 1] << 7)
		hindex[i, j, k] = h
		coords_hindex[i, j, k] = ((h >> 1) & 0b1000) | (h & 0b0111)



class MarchingCubes:
	'''
	Wrapper of a Vertex Array
	MarchingCubes.update_surface(epxr, minv, maxv, res) generates a surface according to the desired expression.
	MarchingCubes.save_to_obj(filename) saves the generated mesh to an obj file.
	'''

	def __init__(self, vArray: VertexArray):
		self.vArray = vArray


	def __update_vArray(self):
		self.vArray.__del__()
		self.vArray.init()

	def __calculate_verts(self, coordslist, num_of_verts, sign, values):
		'''generate verticies for the native implementation'''
		verts = np.zeros((num_of_verts, 3))
		vert_index = 0
		for cindex, c in enumerate(coordslist):
			x, y, z = c
			s = sign[x, y, z]
			v1 = values[x, y, z]
			# vertex_indices_start[cindex] = -1 # len(verts)
			for i, u in enumerate(neighbour_coords):
				if sign[x + u[0], y + u[1], z + u[2]] == s:
					continue

				v2 = values[x + u[0], y + u[1], z + u[2]]
				if v2 != v1 and not math.isinf(v1) and not math.isinf(v2):
					t = v1 / (v2 - v1)
				else:
					t = -0.5

				verts[vert_index] = (c - u * t) * (self.maxv - self.minv) / self.res + self.minv
				vert_index += 1
		return verts

	def __calculate_verts_norms(self, coordslist, num_of_verts, sign, values):
		'''generate verticies and normals for the native implementation'''
		verts = np.zeros((num_of_verts, 3))
		norms = np.zeros((num_of_verts, 3))

		vert_index = 0
		for cindex, c in enumerate(coordslist):
			x, y, z = c
			s = sign[x, y, z]
			v1 = values[x, y, z]
			# vertex_indices_start[cindex] = -1 # len(verts)
			for i, u in enumerate(neighbour_coords):
				x2 = x + u[0]
				y2 = y + u[1]
				z2 = z + u[2]

				if sign[x2, y2, z2] == s:
					continue

				v2 = values[x2, y2, z2]
				if v2 != v1 and not math.isinf(v1) and not math.isinf(v2):
					t = v1 / (v2 - v1)
				else:
					t = -0.5

				verts[vert_index] = (c - u * t) * (self.maxv - self.minv) / self.res + self.minv

				g0 = np.array([
					2 * (values[x + 1, y, z] - v1),
					2 * (values[x, y + 1, z] - v1),
					2 * (values[x, y, z + 1] - v1),
				])

				if x2 == self.res[0] or y2 == self.res[1] or z2 == self.res[2]:
					g1 = g0
				else:
					g1 = np.array([
						values[x2 + 1, y2, z2] - v2,
						values[x2, y2 + 1, z2] - v2,
						values[x2, y2, z2 + 1] - v2,
					])

				n = g0 * (1 - t) + g1 * t
				norms[vert_index] = -n / math.sqrt(n.dot(n))

				vert_index += 1

		return verts, norms

	def __calculate_tris(self, coordslist, hindex, red_hindex, vertex_indices_start):
		'''generating triangles for the native implementation'''
		tris = []
		for cindex, c in enumerate(coordslist):
			x, y, z = c
			if x == self.res[0] - 1 or y == self.res[1] - 1 or z == self.res[2] - 1:
				continue
			h = hindex[x, y, z]
			# h = h if h >= 0 else h + 256 # technically we dont needx that here

			for triangle in Ttable[h]:
				cx, cy, cz = c + triangle[0]
				credh = red_hindex[cx, cy, cz]
				tris.append(vertex_indices_start[cx, cy, cz] + rh_ei2vo[credh, triangle[1]])

		return tris

	def __update_surface_taichi(self, expression, minv, maxv, res, normals=True):

		# lazy fix for boundry problems... (just move the boundry)
		maxv = maxv + (maxv - minv) / res
		res += 1

		# create points (corners of all cells)
		y, x, z = np.meshgrid(
			np.linspace(minv[1], maxv[1], res[1] + 1, dtype=np.float32),
			np.linspace(minv[0], maxv[0], res[0] + 1, dtype=np.float32),
			np.linspace(minv[2], maxv[2], res[2] + 1, dtype=np.float32),
			copy=False # faster with it
		)

		try:
			# calculate values
			values = evaluate(expression)
		except Exception as e:
			print('Input has error at {}!'.format(e))
			return

		# calculate the signs of the values at each point
		sign = np.sign(values, dtype=np.float32).astype(np.int8)
		sign[sign==0] = 1
		sign = (sign + 1) // 2

		# hindex: per cell 8 bit value. Indicates the sign of each corner of each cell. Used for indexing into the triangulation table.
		hindex = np.empty((sign.shape[0] - 1, sign.shape[1] - 1, sign.shape[2] - 1), dtype=np.int8)
		# calculates "reduced hindex". A 4 bit subvalue of hindex. Considers only the "base" corner and all ajdecent corner to the base.
		coords_hindex = np.empty(hindex.shape, dtype=np.int8)

		get_hindex(hindex, coords_hindex, sign)

		# search cells where there should be triangles
		coords = np.argwhere(np.logical_and(hindex != 0, hindex != -1)).astype(np.int16)

		## Vertex Generation

		red_hindex2vertex_count = np.array([0, 3, 1, 2, 1, 2, 2, 1, 1, 2, 2, 1, 2, 1, 3, 0])
		# vertex count corrisponding to each cell base
		vertex_count = red_hindex2vertex_count[coords_hindex]
		# smallest index of the verties corrisponding to the base of the cells
		vertex_indices_start = np.cumsum(vertex_count.flatten()).reshape(vertex_count.shape) - vertex_count

		verts = np.empty((vertex_indices_start[-1, -1, -1] + vertex_count[-1, -1, -1], 3))

		if not normals:
			get_verts_taichi(values, coords, verts, sign, vertex_indices_start, ti.Vector(maxv), ti.Vector(minv), ti.Vector(res))
		else:
			norms = np.empty_like(verts)
			get_verts_norms_taichi(values, coords, values, verts, norms, sign, vertex_indices_start, ti.Vector(maxv), ti.Vector(minv), ti.Vector(res))

		## Triangle Generation

		triangle_count = hi2tc[hindex]
		triangle_index_start = np.cumsum(triangle_count.flatten()).reshape(triangle_count.shape) - triangle_count
		total_tri_count = triangle_index_start[-1, -1, -1] + triangle_count[-1, -1, -1]

		tris = np.zeros(total_tri_count, dtype=int)
		get_tris_taichi(coords, tris, hindex, triangle_index_start, vertex_indices_start, ti.Vector(res))

		if not normals:
			norms = generateNormals(verts, tris)
			# yeah have to normalize them manually afterwards, increadable...
			norms /= sqrt(norms[:, 0]**2 + norms[:, 1]**2 + norms[:, 2]**2)[:, np.newaxis]


		self.vArray.attributes = [verts, norms]
		self.vArray.index = [tris]

	def __update_surface_native(self, expression, minv, maxv, res, normals=True):
		''' native python implementation of marching cubes. Use taichi implementation if availiable'''

		z, y, x = np.meshgrid(
			np.linspace(minv[0], maxv[0], res[0] + 1),
			np.linspace(minv[1], maxv[1], res[1] + 1),
			np.linspace(minv[2], maxv[2], res[2] + 1),
			copy=False, # faster with it
			dtype=np.float32
		)

		try:
			if type(expression) == str:
				values = eval(expression)
			else:
				values = expression(x, y, z)
		except Exception as e:
			print(e)
			return


		# converting from float32 to int8 is a bit faster than from float64 to int8 (probably due to memory?)
		sign = np.sign(values, dtype=np.float32).astype(np.int8)
		sign[sign == 0] = 1
		sign = (sign + 1) // 2

		hindex = (sign[:-1, :-1, :-1] << 0) | (sign[:-1, 1:, :-1] << 2) | (sign[:-1, :-1, 1:] << 4) | (sign[:-1, 1:, 1:] << 6) | \
				 (sign[ 1:, :-1, :-1] << 1) | (sign[ 1:, 1:, :-1] << 3) | (sign[ 1:, :-1, 1:] << 5) | (sign[ 1:, 1:, 1:] << 7)

		coords = np.argwhere(np.logical_and(hindex != 0, hindex != -1)).astype(np.int16) # where there are sign differences

		# reduced hindex is the hindex but we only take the 0th, 1st, 2nd, 3rd and 5th LS bits that corrispond to the vertex's adjacent vertices
		red_hindex2vertex_count = np.array([0, 3, 1, 2, 1, 2, 2, 1, 1, 2, 2, 1, 2, 1, 3, 0])

		coords_hindex = ((hindex >> 1) & 0b1000) | (hindex & 0b0111)
		vertex_count = red_hindex2vertex_count[coords_hindex]
		vertex_indices_start = np.cumsum(vertex_count.flatten()).reshape(vertex_count.shape) - vertex_count

		coordslist = coords.tolist()

		tris = self.__calculate_tris(coordslist, hindex, coords_hindex, vertex_indices_start)
		self.vArray.index = [tris]

		num_of_verts = vertex_indices_start[-1, -1, -1] + vertex_count[-1, -1, -1]
		if not normals:
			verts = self.__calculate_verts(coordslist, num_of_verts, sign, values)
			norms = generateNormals(verts, tris)
			for i, n in enumerate(norms): # yeah have to normalize them manually, increadable...
				norms[i] = n / math.sqrt(n.dot(n))
		else:
			verts, norms = self.__calculate_verts_norms(coordslist, num_of_verts, sign, values)

		self.vArray.attributes = [verts, norms]


		self.__update_vArray()
	
	def update_surface(self, expression, minv, maxv, res, normals=True, use_taichi=True):
		'''
		Updates the surface according to the expression.
		Parameters:
		- expr: expression as a string. Under the hood, it uses numexpr to evaulate the expression.
		  If numexpr is not installed, it uses the build in eval. The variables are x, y, and z lowercase
		- minv, maxv: The boundry box coordinates, necessarily in order (i.e. minv[i] < maxv[i] for all i)
		- res: 3-d vector with the resolution in each axis (i.e. if res[0] = 10 then there will be 10 cells along the x axis)
		- normals (opt, default: true): approximates the normals at each point from the evaluated values of the expression. Default: true.
		- use_taichi (opt, default: true): uses taichi kernels to speed up the calculation
		'''

		if type(minv) != np.ndarray:
			minv = np.array(minv)
		if type(maxv) != np.ndarray:
			maxv = np.array(maxv)
		if type(res) != np.ndarray:
			res = np.array(res)

		self.expression = expression
		self.minv = minv
		self.maxv = maxv
		self.res = res

		if use_taichi:
			self.__update_surface_taichi(expression, minv, maxv, res, normals=normals)
		else:
			self.__update_surface_native(expression, minv, maxv, res, normals=normals)

		self.__update_vArray()


	def save_to_obj(self, filename):
		if self.vArray.attributes:
			save_obj(filename, self.vArray.attributes[0], self.vArray.attributes[1], self.vArray.index[0])



class RealFunction2D:
	'''
	Wrapper for the Vertex Array class
	RealFunction2D.update_surface generates a 2D surface according by displacing a grid of points
	on the x-y plane according to the expression
	'''

	def __init__(self, vArray: VertexArray):
		self.vArray = vArray

	def __update_vArray(self):
		self.vArray.__del__()
		self.vArray.init()

	def __calculate_verts(self, x, y, z):

		verts = np.stack((x, z, y), axis=-1).reshape((x.shape[0] * x.shape[1], 3))

		return verts

	def __calculate_verts_norms(self, x, y, z):

		verts = np.stack((x, z, y), axis=-1).reshape((x.shape[0] * x.shape[1], 3))

		# dA = (self.maxv - self.minv) / self.res
		dx, dy = np.gradient(z, 2)

		dx *= 2 * self.res[0] / (self.maxv[0] - self.minv[0])
		dy *= 2 * self.res[1] / (self.maxv[1] - self.minv[1])

		# tmp = 1 / np.sqrt(dA[0]**2 + dx**2)
		# gx_x = tmp * dA[0]
		# gx_z = tmp * dx

		# tmp = 1 / np.sqrt(dA[1]**2 + dy**2)
		# gy_y = tmp * dA[1]
		# gy_z = tmp * dy

		# norms = np.stack((-gx_z * gy_y, gx_x * gy_y, -gx_x * gy_z), axis=-1).reshape(verts.shape)
		norms = np.stack((-dx, np.ones(dx.shape), -dy), axis=-1)
		norms_length = sqrt(dx**2 + dy**2 + 1)
		norms /= norms_length[:, :, np.newaxis]

		norms = norms.reshape(verts.shape)

		return verts, norms

	def __calculate_tris(self, x, y):

		it = np.arange(x.shape[0] * x.shape[1]).reshape(x.shape)

		tris = np.stack((it[:-1, :-1], it[1:, :-1], it[:-1, 1:], it[1:, :-1], it[:-1, 1:], it[1:, 1:]), axis=-1).flatten()

		return tris


	def update_surface(self, expression, minv, maxv, res, normals=True):
		'''
		Updates the surface according to the expression.
		Parameters:
		- expr: expression as a string. Under the hood, it uses numexpr to evaulate the expression.
		  If numexpr is not installed, it uses the build in eval. The variables are x, y, and z lowercase
		- minv, maxv: The boundry square coordinates, necessarily in order (i.e. minv[i] < maxv[i] for all i)
		- res: 3-d vector with the resolution in each axis (i.e. if res[0] = 10 then there will be 10 cells along the x axis)
		- normals (opt, default: true): approximates the normals at each point from the evaluated values of the expression. Default: true.
		- use_taichi (opt, default: true): uses taichi kernels to speed up the calculation
		'''

		expression = expression.lower()
		if type(minv) != np.ndarray:
			minv = np.array(minv)
		if type(maxv) != np.ndarray:
			maxv = np.array(maxv)
		if type(res) != np.ndarray:
			res = np.array(res)

		self.expression = expression
		self.minv = minv
		self.maxv = maxv
		self.res = res

		# create grid of points
		y, x = np.meshgrid(
			np.linspace(minv[0], maxv[0], res[0] + 1),
			np.linspace(minv[1], maxv[1], res[1] + 1),
			copy=False # faster with it
		)

		# find displacement for each point
		z = eval(expression)

		# create triangles
		tris = self.__calculate_tris(x, y)
		self.vArray.index = [tris]

		if not normals:
			verts = self.__calculate_verts(x, y, z)
			norms = generateNormals(verts, tris)
			for i, n in enumerate(norms):
				norms[i] = n / math.sqrt(n.dot(n))
		else:
			verts, norms = self.__calculate_verts_norms(x, y, z)


		self.vArray.attributes = [verts, norms]

		self.__update_vArray()


	def save_to_obj(self, filename):
		if self.vArray.attributes:
			save_obj(filename, self.vArray.attributes[0], self.vArray.attributes[1], self.vArray.index[0])
