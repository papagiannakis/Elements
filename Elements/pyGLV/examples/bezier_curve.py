#### BEZIER 3D ####

import numpy as np
import bezier

test_bezier_control_nodes = [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]

def vertecies_to_line_vertecies(coordinates):
    vertecies = []
    vertecies.append(coordinates[0])
    for coord in coordinates[1:-1]:
        vertecies.extend([coord, coord])
    vertecies.append(coordinates[-1])
    return vertecies

def separate_coordinates(coordinates):
    x_coordinates = [coord[0] for coord in coordinates]
    y_coordinates = [coord[1] for coord in coordinates]
    z_coordinates = [coord[2] for coord in coordinates]
    return [x_coordinates, y_coordinates, z_coordinates]

def combine_coordinates(coordinates):
    return [[coord[0], coord[1], coord[2]] for coord in zip(coordinates[0], coordinates[1], coordinates[2])]

def xyz_to_vertecies(coords):
    return [coord + [1.0] for coord in coords]


def generate_bezier_data(bezier_nodes, num_points, start_x, end_x):
    bezier_curve = bezier.Curve.from_nodes(separate_coordinates(bezier_nodes))
    print("created bezier curve:", bezier_curve)

    x_values = np.linspace(start_x, end_x, num_points)
    bezier_points = bezier_curve.evaluate_multi(x_values)
    print("bezier_points", bezier_points)

    xyz_values = combine_coordinates(bezier_points)

    vertexBezier = np.array(vertecies_to_line_vertecies(xyz_to_vertecies(xyz_values)), dtype=np.float32)
    print("vertexBezier", vertexBezier)

    colorBezier = np.array([[0.5, 0.0, 1.0, 1.0]] * len(vertexBezier), dtype=np.float32)

    indexBezier = np.array(range(len(vertexBezier)), np.uint32)

    return vertexBezier, colorBezier, indexBezier