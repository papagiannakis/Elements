#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A tolerant Wavefront .obj reader: positions and faces only, which is what the unlit/Phong shaders
in this project need (normals come from Elements.utils.normals, uv coordinates are not read).

"Tolerant" is the whole point, because .obj files in the wild vary a lot:

  * face indices may be written v, v/vt, v//vn or v/vt/vn -- only the first number is the position
  * faces may be quads or larger n-gons, which are fan-triangulated into (v0,v1,v2), (v0,v2,v3), ...
  * indices may be negative, meaning "counting back from the vertices so far"
  * fields may be separated by any run of spaces or tabs
  * comments, blank lines and the many other record types (vt, vn, g, s, usemtl, ...) are skipped

"""

import numpy as np


def obj_to_mesh(obj_file, color = [1.0 ,1.0 , 0.0, 1.0]):
    """(vertices, indices, colors) for one .obj file.

    vertices are homogeneous (x, y, z, 1), indices are triangles, and colors is `color` repeated
    once per vertex, since a plain .obj carries no per-vertex colour.
    """
    vertices = []
    indices = []

    with open(obj_file, 'r') as in_file:
        for line in in_file:
            parts = line.split()
            if not parts or parts[0].startswith('#'):
                continue

            if parts[0] == 'v':
                try:
                    vertices.append([float(parts[1]), float(parts[2]), float(parts[3]), 1.0])
                except (ValueError, IndexError):
                    continue    # a malformed vertex line: skip it rather than lose the whole file

            elif parts[0] == 'f':
                try:
                    # only the position index matters here; '1', '1/2', '1//3' and '1/2/3' all start
                    # with it. Negative indices count back from the vertices read so far, positive
                    # ones are 1-based from the start of the file.
                    face = []
                    for field in parts[1:]:
                        i = int(field.split('/')[0])
                        face.append(len(vertices) + i if i < 0 else i - 1)
                except (ValueError, IndexError):
                    continue

                # fan-triangulate: a quad becomes 2 triangles, an n-gon becomes n-2. Reading only
                # the first 3 fields instead would drop everything past the first triangle.
                for k in range(1, len(face) - 1):
                    indices.extend((face[0], face[k], face[k + 1]))

    return (
        np.array(vertices, dtype=np.float32),
        np.array(indices, dtype=np.uint32),
        np.array([color] * len(vertices), dtype=np.float32),
    )
