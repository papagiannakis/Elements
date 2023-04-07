import numpy as np
import Elements.pyECSS.utilities as util

def generateUniqueVertices(vertices,indices,color=None):
    """
    Generates vertices, indices and color of given non-unique vertices
    Arguments:
        vertices: Vertex Array
        indices: Index/Triangle Array
        color: Color Array
    Returns:
        newvertices:Generated Unique Vertex Array
        newindices:Generated Unique Index/Triangle Array
        newcolor:Generated Unique Color Array
    """
    newindices = np.empty(0,dtype=np.uint32) 
    newvertices = np.empty(0)
    newcolor = np.empty(0)

    for i in range(len(indices)):
        newvertices = np.r_[newvertices,vertices[indices[i]]]
        newindices = np.append(newindices,i)
        if color is not None:
            newcolor = np.r_[newcolor,color[indices[i]]]
    
    newvertices = newvertices.reshape((int(len(newvertices)/4) ,4))
    if color is not None:
        newcolor = newcolor.reshape((int(len(newcolor)/4) ,4))
    
    return newvertices,newindices,newcolor

def generateSimpleVertices(vertices,indices,color=None):
    """
    Generates vertices, indices and color of given unique vertices
    Arguments:
        vertices: Vertex Array
        indices: Index/Triangle Array
        color: Color Array
    Returns:
        newvertices:Generated Non-Unique Vertex Array
        newindices:Generated Non-Unique Index/Triangle Array
        newcolor:Generated NonUnique Color Array
    """
    newindices = np.empty(0,dtype=np.uint32)
    newvertices = np.empty(0)
    newcolor = np.empty(0)

    verticesSet = {}
    colorSet = {}
    newindices = np.empty(0,dtype=np.uint32) 

    count = 0
    for i in range(len(indices)):
        val = tuple(vertices[indices[i]])
        clr = tuple(color[indices[i]])
        flag = False
        valid = -1
        total = __getdictSize(verticesSet)
        for key in range(total):
            tmp = verticesSet.get(key)
            if tmp is not None:
                if val == tmp:
                    valid = key
                    flag = True
                    break

        if flag==False:
            verticesSet[count] = val
            if color is not None:
                colorSet[count] = clr
            valid = count
            count = count+1
        newindices = np.append(newindices,valid)

    total = __getdictSize(verticesSet)

    for key in range(total):
        newvertices = np.r_[newvertices,list(verticesSet.get(key))]
        if color is not None:
            newcolor = np.r_[newcolor,list(colorSet.get(key))]

    newvertices = newvertices.reshape((int(len(newvertices)/4) ,4))
    if color is not None:
        newcolor = newcolor.reshape((int(len(newcolor)/4) ,4))

    return newvertices,newindices,newcolor

def __getdictSize(d,c=0):
    """
    Counts The nubber of key-value pairs in a dictionary
    Arguments:
        d: Python Dictionary
        c: Index/Triangle Array
    Returns:
        c: Counted key-pair values
    """
    for key in d:
        if isinstance(d[key],dict):
            c = __getdictSize(d[key],c+1)
        else:
            c +=1
    return c

def __hasUniqueVertices(vertices):
    """
    Checks if a Vertex Array has unique Vertices
    Arguments:
        vertices: Vertex Array
    Returns:
        c: True if there is at least one vertex that appears more than one time, False otherwise
    """
    v = set()
    for i in range(len(vertices)):
        for vertex in v:
            if (vertex == tuple(vertices[i])):
                return True
        v.add(tuple(vertices[i]))
    return False

def generateNormals(vertices, indices):
    """
    Calculates and returns normals for given vertices
    Arguments:
        vertices: Vertex Array
        indices: Index/Triangle Array
    Returns:
        normals: Normals for the given vertices
    """
    vs,_ = vertices.shape
    normals = np.empty(0)
    n = [0.0,0.0,0.0]
    for i in range(len(vertices)):
        normals = np.r_[normals,n]
    normals = normals.reshape((int(len(normals)/3) ,3))

    for index in range(int(len(indices)/3)):
        in1 = indices[3*index]
        in2 = indices[3*index+1]
        in3 = indices[3*index+2]
        p0 = util.vec(vertices[in1][0],vertices[in1][1],vertices[in1][2])
        p1 = util.vec(vertices[in2][0],vertices[in2][1],vertices[in2][2])
        p2 = util.vec(vertices[in3][0],vertices[in3][1],vertices[in3][2])
        v1 = util.vec(p2[0]-p0[0],p2[1]-p0[1],p2[2]-p0[2])
        v2 = util.vec(p1[0]-p0[0],p1[1]-p0[1],p1[2]-p0[2])
        cross_product = np.cross(v2,v1)
        normals[in1] += cross_product
        normals[in2] += cross_product
        normals[in3] += cross_product
    
    return normals

def generateSmoothNormalsMesh(vertices, indices, color=None):
    """
    Generates Normals for smooth shading
    If given vertices Are Unique then generate simple vertices/indices/color First
    Arguments:
        vertices: Vertex Array
        indices: Index/Triangle array
        color:Color Array
    Returns:
        vertices: Vertex Array for Smooth shading
        indices: Index/Triangle array for Smooth shading
        color:Color Array for Smooth shading
        normals: Normals for Smooth shading
    """
    if __hasUniqueVertices(vertices)==True:
        newvertices,newindices,newcolor = generateSimpleVertices(vertices,indices,color)
        return newvertices,newindices,newcolor,generateNormals(newvertices,newindices)
    return vertices, indices, color, generateNormals(vertices,indices)

def generateFlatNormalsMesh(vertices,indices,color=None):
    """
    Generates Normals for Flat shading
    If given vertices Are not Unique then generate Unique vertices/indices/color First
    Arguments:
        vertices: Vertex Array
        indices: Index/Triangle array
        color:Color Array
    Returns:
        vertices: Vertex Array for Flat shading
        indices: Index/Triangle array for Flat shading
        color:Color Array for Flat shading
        normals: Normals for Flat shading
    """
    if __hasUniqueVertices(vertices)==False:
        newvertices,newindices,newcolor = generateUniqueVertices(vertices,indices,color)
        return newvertices,newindices,newcolor,generateNormals(newvertices,newindices)

    return vertices,indices,color,generateNormals(vertices,indices)


def Convert(vertices, colors, indices, produceNormals=True):
    """
    Function used for flat shading
    """
    iVertices = []
    iColors = []
    iNormals = []
    iIndices = []
    for i in range(0, len(indices), 3):
        iVertices.append(vertices[indices[i]])
        iVertices.append(vertices[indices[i + 1]])
        iVertices.append(vertices[indices[i + 2]])
        iColors.append(colors[indices[i]])
        iColors.append(colors[indices[i + 1]])
        iColors.append(colors[indices[i + 2]])
        

        iIndices.append(i)
        iIndices.append(i + 1)
        iIndices.append(i + 2)

    if produceNormals:
        for i in range(0, len(indices), 3):
            iNormals.append(util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]))
            iNormals.append(util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]))
            iNormals.append(util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]))

    iVertices = np.array( iVertices, dtype=np.float32 )
    iColors   = np.array( iColors,   dtype=np.float32 )
    iIndices  = np.array( iIndices,  dtype=np.uint32  )

    iNormals  = np.array( iNormals,  dtype=np.float32 )

    return iVertices, iColors, iIndices, iNormals