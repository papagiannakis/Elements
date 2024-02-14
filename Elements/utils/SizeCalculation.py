import numpy as np
import open3d as o3d


# load chair and table models
# chair_mesh = o3d.io.read_triangle_mesh("chair/models/model_normalized.obj")
# table_mesh = o3d.io.read_triangle_mesh("table/models/model_normalized.obj")
# chair_mesh.compute_vertex_normals()
# table_mesh.compute_vertex_normals()


def calc_size(path):
    mesh = o3d.io.read_triangle_mesh(path)
    print(mesh)
    mesh.compute_vertex_normals()
    # get the axis-aligned bounding box of the box
    aabb = mesh.get_axis_aligned_bounding_box()

    # calculate the width, height, and depth of the bounding box
    width = np.abs(aabb.max_bound[0] - aabb.min_bound[0])
    height = np.abs(aabb.max_bound[1] - aabb.min_bound[1])
    depth = np.abs(aabb.max_bound[2] - aabb.min_bound[2])

    return width, height, depth


def calc_size_from_vert(vertices, triangles):

    newtriangleformat = np.reshape(triangles, (-1, 3))
    newvertformat = vertices[:, :3]
    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(newvertformat)
    mesh.triangles = o3d.utility.Vector3iVector(newtriangleformat)
    mesh.compute_vertex_normals()
    # get the axis-aligned bounding box of the box
    aabb = mesh.get_axis_aligned_bounding_box()

    # calculate the width, height, and depth of the bounding box
    width = np.abs(aabb.max_bound[0] - aabb.min_bound[0])
    height = np.abs(aabb.max_bound[1] - aabb.min_bound[1])
    depth = np.abs(aabb.max_bound[2] - aabb.min_bound[2])

    return width, height, depth
