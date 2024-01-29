"""
point Cloud To Mesh py

generateTrianglesFromCustomList can transform custom point clouds to meshes

@author Nikos Iliakis csd4375
"""
import open3d as o3d
import numpy as np
import Elements.pyECSS.math_utilities as util

'''
This function takes a list of points (point cloud) and using the point_cloud_ball_pivoting algorithm it generates
the triangles (or indices) of the given point cloud, using open3d library
If its a sphere set isItASphere to true to ensure normals are point outwards
'''
def generateTrianglesFromCustomList(point_list, isItASphere = False):
    # Create a point cloud from the vertices
    point_cloud = o3d.geometry.PointCloud()    
    
    point_list = [row[:3] for row in point_list]
    # print(point_list)
    point_cloud.points = o3d.utility.Vector3dVector(point_list)
    
    # Estimate normals for the point cloud
    point_cloud.estimate_normals()
    
    # Generate a mesh using point_cloud_poisson
    # mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(point_cloud, depth=9, width=0, scale=1.1, linear_fit=False)
    # bbox = point_cloud.get_axis_aligned_bounding_box()
    # mesh = mesh.crop(bbox)


    # Generate a mesh using point_cloud_ball_pivoting
    distances = point_cloud.compute_nearest_neighbor_distance()
    avg_dist = np.mean(distances)
    radius = 3 * avg_dist
    
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
        point_cloud,
        o3d.utility.DoubleVector([radius, radius * 2])
    )
    
    mesh = mesh.remove_duplicated_vertices()
    mesh = mesh.remove_duplicated_triangles()
    mesh = mesh.remove_degenerate_triangles()
    mesh = mesh.remove_non_manifold_edges()
    
    center = np.mean(mesh.vertices, axis=0)
    mesh.compute_vertex_normals()

    if(isItASphere == True):
        # Ensuring normals point outwards by checking with the direction from the center of the sphere
        for i in range(len(mesh.vertex_normals)):
            direction = mesh.vertices[i] - center
            dot_product = np.dot(mesh.vertex_normals[i], direction)
            if dot_product < 0:
                mesh.vertex_normals[i] *= -1
            
    return mesh.vertices, mesh.vertex_normals, mesh.triangles


# This is just an example of an already made point Cloud To mesh classic bunny
def generateBunnyExample():
    bunny = o3d.data.BunnyMesh()
    mesh  = o3d.io.read_triangle_mesh(bunny.path)
    mesh.compute_vertex_normals()
    
    #o3d.visualization.draw_geometries_with_vertex_selection([mesh])
    return np.asarray(mesh.vertices), mesh.vertex_normals, np.asarray(mesh.triangles)

    
# vertexCube = np.array([
#     [-0.5, -0.5, 0.5, 1.0],
#     [-0.5, 0.5, 0.5, 1.0],
#     [0.5, 0.5, 0.5, 1.0],
#     [0.5, -0.5, 0.5, 1.0], 
#     [-0.5, -0.5, -0.5, 1.0], 
#     [-0.5, 0.5, -0.5, 1.0], 
#     [0.5, 0.5, -0.5, 1.0], 
#     [0.5, -0.5, -0.5, 1.0]
# ],dtype=np.float32) 

# generateTrianglesFromCustomList(vertexCube)
# generateBunnyExample()