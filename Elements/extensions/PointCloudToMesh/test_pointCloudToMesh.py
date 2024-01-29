import unittest
import numpy as np

from Elements.features.PointCloudToMesh.PointCloudToMesh import generateTrianglesFromCustomList, generateBunnyExample

class TestPointCloudToMesh(unittest.TestCase):

    def test_generateTrianglesFromCustomList(self):
        # Create a sample input (vertices) for the function
        num_points = 100

        # Generate random values for θ and ϕ
        theta = np.random.uniform(0, 2 * np.pi, num_points)
        phi = np.random.uniform(0, np.pi, num_points)

        # Initialize an empty list to store the points
        points_on_sphere = []

        # Convert spherical coordinates to Cartesian coordinates and append to the list
        for i in range(num_points):
            x = np.sin(phi[i]) * np.cos(theta[i])
            y = np.sin(phi[i]) * np.sin(theta[i])
            z = np.cos(phi[i])
            points_on_sphere.append([x, y, z])


        # Now, points_on_sphere contains the list of points in the desired format
        vertices = np.array(points_on_sphere, dtype=np.float32) 

        mesh_vertices, mesh_normals, mesh_indices = generateTrianglesFromCustomList(vertices)

        self.assertEqual(len(mesh_vertices), num_points)
        self.assertEqual(len(mesh_normals),  num_points)
        self.assertTrue(len(mesh_indices) >  0)

    def test_generateBunnyExample(self):
        bunny_vertices, bunny_normals, bunny_indices = generateBunnyExample()

        self.assertTrue(len(bunny_vertices) > 0)
        self.assertTrue(len(bunny_normals) > 0)
        self.assertTrue(len(bunny_indices) > 0)