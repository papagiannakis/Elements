


def frange(start, stop, step):
    i = 0.0
    while start + i * step < stop:
        yield start + i * step
        i += 1.0

def get_highest_coords(vectors):
    highest_coords = [float('-inf')] * 3
    for vector in vectors:
        for i in range(3):
            if vector[i] > highest_coords[i]:
                highest_coords[i] = vector[i]
    highest_coords.append(1)
    return highest_coords

def get_lowest_coords(vectors):
    num_coords = len(vectors[0])
    lowest_coords = [float('inf')] * num_coords
    for vector in vectors:
        for i in range(num_coords):
            if vector[i] < lowest_coords[i]:
                lowest_coords[i] = vector[i]
    lowest_coords.append(1)
    return lowest_coords

def translate_z(vectors, z):
    translated_vectors = []
    for vector in vectors:
        translated_vector = [vector[0], vector[1], vector[2]+z, vector[3]]
        translated_vectors.append(translated_vector)
    return translated_vectors

def point_scalar_mult(p1,s):
    return [p1[0]*s,p1[1]*s,p1[2]*s,1.]

def point_add(p1,p2):
    return [p1[0]+p2[0],p1[1]+p2[1],p1[2]+p2[2],1.]

def get_intersection_point(p1,p2,plane):
    p1_dist = abs(p1[1]-plane)
    p2_dist = abs(plane-p2[1])
    total = p1_dist +p2_dist
    point = point_add((point_scalar_mult(p1,(p2_dist/total))),(point_scalar_mult(p2,(p1_dist/total))))
    return point

def on_different_sides(p1,p2,plane):
    if(0 > ((p1[1] - plane) * (p2[1] - plane))):
        return True
    else:
        return False
    
def intersect(vertices,indices,plane):
    contour = []
    for i in range(0, len(indices)-2, 3):
        triangle_indices = [indices[i],indices[i+1],indices[i+2]]
        triangle = [vertices[triangle_indices[0]],vertices[triangle_indices[1]],vertices[triangle_indices[2]]]
        line = []
        if(on_different_sides(triangle[0],triangle[1],plane)):
            line.append(get_intersection_point(triangle[0],triangle[1],plane))
        if(on_different_sides(triangle[1],triangle[2],plane)):
            line.append(get_intersection_point(triangle[1],triangle[2],plane))
        if(on_different_sides(triangle[2],triangle[0],plane)):
            line.append(get_intersection_point(triangle[2],triangle[0],plane))
        if(len(line) == 2):
            contour.extend(line)
    return contour
    

def create_contours(vertices,indices,step=.1):
    contours = []
    lower = get_lowest_coords(vertices)
    upper = get_highest_coords(vertices)
    for x in frange(lower[1], upper[1], step):
        contours.extend(intersect(vertices,indices,x))
    return contours
