"""
PointCloudTomesh using Delaunay triangulation
    
@author Nikos Iliakis csd4375
"""

import numpy as np
from scipy.spatial import Delaunay

def generateTrianglesFromPointCloud(point_list):
    # Perform Delaunay triangulation to create a mesh from the point cloud
    triangulation = Delaunay(point_list[:, :3])

    # Get the tetrahedra from the triangulation
    tetrahedra = point_list[triangulation.simplices]

    # Extract the surface triangles from the tetrahedra
    surface_triangles = []
    surface_triangle_indices = []  # To keep track of indices

    for i, tetra in enumerate(tetrahedra):
        for j in range(4):
            # Create triangles by omitting one vertex at a time
            triangle = np.delete(tetra, j, axis=0)
            # Check if the triangle is not already in the list
            if not any(np.all(np.sort(triangle, axis=1) == np.sort(tri, axis=1)) for tri in surface_triangles):
                surface_triangles.append(triangle)
                surface_triangle_indices.append(np.delete(triangulation.simplices[i], j, axis=0))

    # Convert the lists to NumPy arrays
    surface_triangles = np.array(surface_triangles)
    surface_triangle_indices = np.array(surface_triangle_indices)
    
    # print(surface_triangles)
    # print(surface_triangle_indices)
    
    return point_list, surface_triangle_indices

#hexagonical prism example
vertices = np.array([
    [-0.5, -0.5, 0.5, 1.0],   # Bottom left-front corner
    [0.5, -0.5, 0.5, 1.0],    # Bottom right-front corner
    [0.25, 0.25, 0.5, 1.0],   # Bottom middle-front
    [-0.5, -0.5, -0.5, 1.0],  # Bottom left-back corner
    [0.5, -0.5, -0.5, 1.0],   # Bottom right-back corner
    [0.25, 0.25, -0.5, 1.0],  # Bottom middle-back
    [0.0, 0.0, 0.75, 1.0],    # Top center
    [0.0, 0.0, -0.75, 1.0],   # Bottom center
], dtype=np.float32)
generateTrianglesFromPointCloud(vertices)