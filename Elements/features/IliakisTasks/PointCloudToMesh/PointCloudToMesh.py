import open3d as o3d
import numpy as np

def generateTrianglesFromCustomList(point_list):
    # Create a point cloud from the vertices
    point_cloud = o3d.geometry.PointCloud()    
    
    point_list = [row[:3] for row in point_list]
    point_cloud.points = o3d.utility.Vector3dVector(point_list)
    
    # Estimate normals for the point cloud
    point_cloud.estimate_normals()
    
    # Generate a mesh using Delaunay triangulation
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
        point_cloud,
        o3d.utility.DoubleVector([100, 100 * 2])
    )
    
    mesh.compute_vertex_normals()
    # print(np.asarray(mesh.triangles))
    # print(np.asarray(mesh.vertices))
    return np.asarray(mesh.vertices), mesh.vertex_normals, np.asarray(mesh.triangles)

def generateBunnyExample():
    bunny = o3d.data.BunnyMesh()
    mesh  = o3d.io.read_triangle_mesh(bunny.path)
    mesh.compute_vertex_normals()
    
    #o3d.visualization.draw_geometries_with_vertex_selection([mesh])
    return np.asarray(mesh.vertices), mesh.vertex_normals, np.asarray(mesh.triangles)

    
vertexCube = np.array([
    [-0.5, -0.5, 0.5, 1.0],
    [-0.5, 0.5, 0.5, 1.0],
    [0.5, 0.5, 0.5, 1.0],
    [0.5, -0.5, 0.5, 1.0], 
    [-0.5, -0.5, -0.5, 1.0], 
    [-0.5, 0.5, -0.5, 1.0], 
    [0.5, 0.5, -0.5, 1.0], 
    [0.5, -0.5, -0.5, 1.0]
],dtype=np.float32) 
generateTrianglesFromCustomList(vertexCube)
generateBunnyExample()