"""
generateTerrain convenience method, part of Elements.pyGLV
    
Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
@Copyright 2021-2022 Dr. George Papagiannakis
    
Convenience method for scene wireframe terrain generation

"""

import numpy as np

def generateTerrain(size=2,N=2,uniform_color = [0.4,0.4,0.4,0.5]):
    # Generate Terrain Vertices and Indices
    x = np.linspace(-size,size,2*N+1)
    points = []
    indices = []
    for j in range(2*N+1):
        for i in range(2*N+1):
            points.append([x[i],0,x[j]])
            
    
    for j in range(2*N):
        for i in range(2*N):
            # assume we have the square
            # C ---- D
            # |     /|
            # |    / |
            # |   /  |
            # |  /   |
            # | /    |
            # |/     |
            # A -----B
            indexA = i + (2*N+1)*j
            indexB = indexA +1
            indexC = indexA + (2*N+1)
            indexD = indexB + (2*N+1)
            # For primitive=GL_LINES:
            ## triangle AB, BD, DA, DC, CA
            indices.append(indexA)
            indices.append(indexB)
            indices.append(indexB)
            indices.append(indexD)
            indices.append(indexD)
            indices.append(indexA)
            indices.append(indexD)
            indices.append(indexC)
            indices.append(indexC)
            indices.append(indexA)

    #colors
    
    colorT = [uniform_color]*((2*N+1))**2 
    return np.array(points,dtype=np.float32) , np.array(indices,dtype=np.float32), np.array(colorT, dtype=np.float32)

if __name__ == "__main__":
    ps, ind, col = generateTerrain()
    print (ps, ind)
