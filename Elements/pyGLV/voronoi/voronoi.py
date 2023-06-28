import numpy as np
from scipy.spatial import Voronoi
import random

def random_points_in_square(n, side_length):
    points = []
    for i in range(n):
        x = random.uniform(0, side_length)
        y = random.uniform(0, side_length)
        points.append((x, y))
    return points


def add_third_coordinate(points):
    return [(x, y, 0, 1) for x, y in points]


### Voronoi Diagram
# Creates a Voronoi Diagram with n random points.
def voronoi_diagram(points, colors=None):
    ### Generate Random Points
    point_list = random_points_in_square(points,1)

    # This is a hack to make sure that the voronoi diagram is bounded.
    point_list.append([.5,5])
    point_list.append([.5,-5])
    point_list.append([5,.5])
    point_list.append([-5,.5])

    ### Voronoi Diagram
    vor = Voronoi(point_list)
    vertices = add_third_coordinate(vor.vertices)
    voronoi = []

    ### Go through each region and add the edges to the list.
    # Each region is a list of indices of vertices that make up the region.
    # These vertices are split into triangles.
    for region in vor.regions:
        for i in range(len(region)):
            pair = (region[i], region[(i+1) % len(region)])
            if pair[0] != -1 and pair[1] != -1:
                voronoi.append(vertices[pair[0]])
                voronoi.append(vertices[pair[1]])

    colors = np.array([(1.,1.,1.,1.)] * len(voronoi))
    voronoi = np.array(voronoi)
    indices = np.array(range(len(voronoi)))

    ### Mesh for colored faces. Pick relevant regions. Those are the regions that are not unbounded.
    # All regions that are unbounded have a -1 in them and have no outer edge.
    relevant_regions =[]
    for region in vor.regions:
        if not (-1 in region) and len(region) != 0:
            relevant_regions.append(region)
    #use same vertices.
    mesh_vertices = []
    mesh_indices = []
    mesh_color = []

    for region in relevant_regions:
        color = list(np.random.choice(range(256), size=4))
        color[0] = color[0]/256.
        color[1] = color[1]/256.
        color[2] = color[2]/256.
        color[3] = 1.
        for i in range(1,len(region)-1):
            tri = (region[0], region[(i)], region[(i+1)])
            mesh_vertices.append(vertices[tri[0]])
            mesh_vertices.append(vertices[tri[1]])
            mesh_vertices.append(vertices[tri[2]])
            mesh_color.append(color)
            mesh_color.append(color)
            mesh_color.append(color)
        
    mesh_indices = np.array(range(len(mesh_vertices)))

# For point rendering
    point_list = np.array(add_third_coordinate(point_list[:-4]))
    for i in range(len(point_list)):
        point_list[i][2] = 0.01
    point_colors = np.array([(0.,0.,0.,1.)] * len(point_list))
    point_indices = np.array(range(len(point_list)))

    return mesh_vertices, mesh_indices, mesh_color, point_list, point_indices, point_colors
