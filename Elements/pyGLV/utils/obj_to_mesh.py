#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import sys
import numpy as np

def obj_to_mesh(obj_file, color = [1.0 ,1.0 , 0.0, 1.0]):
    try:
        with open(obj_file, 'r') as in_file:
            filedata = in_file.readlines()

            vertices = [l.split(' ') for l in filedata if l[0:2] == 'v ']
            vertices = [[float(x[1]), float(x[2]), float(x[3]), 1.0] for x in vertices]
            vertices = np.array(vertices)

            triangles = [l.split(' ') for l in filedata if l[0:2] == 'f ']
            indices = []
            for t in triangles:
                indices.append(int(t[1].split('//')[0])-1)
                indices.append(int(t[2].split('//')[0])-1)
                indices.append(int(t[3].split('//')[0])-1)
            
            colors = [color for _ in range(len(vertices))]
            colors = np.array(colors)

        return vertices, indices, colors


    except FileNotFoundError as err:
        print("Input File %s not found" % obj_file)

