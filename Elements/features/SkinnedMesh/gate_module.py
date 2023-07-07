
import warnings
warnings.filterwarnings('ignore')

import numpy as np
from numpy import e,pi
from clifford.g3c import *
from clifford.tools.g3c import *
from pyassimp import *
import pyassimp
import meshplot as mp
from numba import jit,njit

class vertex_weight:
    # =================================================
    # Creating a class that contains the vertices and 
    # and the respective weights that are affected by the
    # bones. 
    # =================================================
  def __init__(self,v_length):
    self.id = np.full([2*v_length,4],-1)
    self.weight = np.zeros([2*v_length,4])

  def add(self,v,b,w):
    position = 0
    for i in range(4):
        if self.weight[v][position]>0 :
            position +=1
    if position <= 4:
        self.weight[v][position]=w
        self.id[v][position]=b

  def populate(self,b):
    for boneID in range(len(b)):
      for i in range(len(b[boneID].weights)):
        self.add(b[boneID].weights[i].vertexid, boneID ,b[boneID].weights[i].weight)



def get_bone_names(b):
    return [str(b[i]) for i in range(len(b))]
        
def vertex_apply_M(v,M):
    return np.dot(M,np.append(v,[1.0]))[0:3]

def eulerAnglesToRotationMatrix(theta) :  
    R_x = np.array([[1,         0,                  0                   ],
                    [0,         math.cos(theta[0]), -math.sin(theta[0]) ],
                    [0,         math.sin(theta[0]), math.cos(theta[0])  ]
                    ])                    
    R_y = np.array([[math.cos(theta[1]),    0,      math.sin(theta[1])  ],
                    [0,                     1,      0                   ],
                    [-math.sin(theta[1]),   0,      math.cos(theta[1])  ]
                    ])             
    R_z = np.array([[math.cos(theta[2]),    -math.sin(theta[2]),    0],
                    [math.sin(theta[2]),    math.cos(theta[2]),     0],
                    [0,                     0,                      1]
                    ])                  
    R = np.dot(R_z, np.dot( R_y, R_x ))
    return R

def B(x):
    return b[x].offsetmatrix
#     if x == 0:
#         return b[x].offsetmatrix
#     else :
#         return np.dot(B(x-1),b[x].offsetmatrix)
  
def draw_original_wireframe():
    p.add_lines(v[f[:,0]], v[f[:,1]], shading={"line_color": "magenta"});
    p.add_lines(v[f[:,2]], v[f[:,1]], shading={"line_color": "magenta"});
    p.add_lines(v[f[:,2]], v[f[:,0]], shading={"line_color": "magenta"});


def initialize_M(b):
  M = np.zeros([len(b),4,4])
  for i in range(len(b)):
    M[i] = np.identity(4)
  return M

def get_bone_names(b):
    return [str(b[i]) for i in range(len(b))]

def read_tree(scene,mesh_id,M,transform):
  b = scene.meshes[mesh_id].bones
  MM = np.zeros([len(b),4,4])
  G = np.linalg.inv(scene.rootnode.transformation)
  bone_names = get_bone_names(b)
  read_tree_names(MM,M,scene.rootnode,G,bone_names,transform)
  return MM

def read_tree_names(MM,M,node,parentmatrix,bone_names, transform = False):
    p = np.dot(parentmatrix,node.transformation)
    if transform == True :
        if node.name in bone_names:
            index = bone_names.index(node.name)
            p = np.dot(p,M[index])
            MM[index] = p
        for child in node.children:
            read_tree_names(MM,M,child,p,bone_names,True)            
    else:
        if node.name in bone_names:
            index = bone_names.index(node.name)
            MM[index] = p
        for child in node.children:
            read_tree_names(MM,M,child,p,bone_names,False)        
    

def draw_vertices_affected_by_boneID_on_new(boneID):
    vertices_ids_affected_by_boneID = [b[boneID].weights[i].vertexid for i in range(len(b[boneID].weights))]
    weights_affected_by_boneID = [b[boneID].weights[i].weight for i in range(len(b[boneID].weights))]
    IDs = vertices_ids_affected_by_boneID
    print("red points are the ones affected by :", b[boneID])
#     p.add_points(v[IDs], shading={"point_size": 0.7,"point_color": "red"}); 
    p.add_points(newv[IDs], shading={"point_size": 1,"point_color": "red"}); 





def draw_vertices_affected_by_boneID(boneID):
    vertices_ids_affected_by_boneID = [b[boneID].weights[i].vertexid for i in range(len(b[boneID].weights))]
    IDs = vertices_ids_affected_by_boneID
    print("red points are the ones affected by :", b[boneID])
    p.add_points(v[IDs], shading={"point_size": 0.7,"point_color": "red"}); 



##### ALL BELOW ARE NEEDED FOR GA WAY



from clifford.g3c import *
from clifford.tools.g3c import *
from clifford import Cl, conformalize

G3, blades_g3 = Cl(3)
G3c, blades_g3c, stuff = conformalize(G3)

# ep, en, up, down, homo, E0, ninf, no = (g3c.stuff["ep"], g3c.stuff["en"],
#                                         g3c.stuff["up"], g3c.stuff["down"], g3c.stuff["homo"],
#                                         g3c.stuff["E0"], g3c.stuff["einf"], -g3c.stuff["eo"])
# # Define a few useful terms
# E = ninf^(no)
# I5 = e12345
# I3 = e123    

    
def matrix_to_motor(M):
    "The matrix has to represent rotation and translation only, no scaling of x,y or z."
    T,R = matrix_to_t_r(M)
    return T*R

def matrix_to_t_r(M):
    "The matrix has to represent rotation and translation only, no scaling of x,y or z."
    phi,axis,trans = matrix_to_angle_axis_translation(M)
    if phi == 0 or math.isnan(axis[0]) or math.isnan(axis[1]) or math.isnan(axis[2]): 
        R = 1
    else:
        # axis from euc to cga and normalization
        axis = axis[0]*e1+axis[1]*e2+axis[2]*e3
        axis = axis/norm(axis)
        I3 = e1*e2*e3 
        R = e**(-(axis*I3)*(phi/2))   # rotor

    # update trans from euclidean vector to  cga
    t = trans[0]*e1+trans[1]*e2+trans[2]*e3
    T = e**(-1/2*t*einf)          # translator
    return T,R

def down_vertex(mv):
    down = fast_down(mv)
    return np.array([down[e1], down[e2], down[e3]])

def read_tree_ga(scene,mesh_id,tt,rr,dd,transform):
  b = scene.meshes[mesh_id].bones
  bone_names = get_bone_names(b)
  rotors = [1 for i in range(len(b))]
  read_tree_names_ga(rotors,tt,rr,dd,scene.rootnode,1,bone_names,transform)
  return rotors

def LERP(source,end, alpha):
    return (1-alpha)*source+alpha*end

def read_tree_names_ga(rotors,tt,rr,dd,node,parentrotor,bone_names,transform = False):
    """
    This is the rotor version of read_tree_names function.
    It reads the bone hierarch and stores the final transformation 
    for each bone in the rotors list. If transform is set to True,
    it also takes into consideration the tt,rr and dd lists 
    that contain transformation, rotation and dilation multivectors
    for each bone. 
    """
    t,r = matrix_to_t_r(node.transformation)
    if transform == True :
        # p = parentrotor*t*r
        if node.name in bone_names:
            index = bone_names.index(node.name)
            p = parentrotor*t*tt[index]*r*rr[index]*dd[index]
            rotors[index] = p
            for child in node.children:
                read_tree_names_ga(rotors,tt,rr,dd,child,p,bone_names,True)
        else:
            p = parentrotor*t*r
            for child in node.children:
                read_tree_names_ga(rotors,tt,rr,dd,child,p,bone_names,True)            
    else:
        p = parentrotor*t*r
        if node.name in bone_names:
            index = bone_names.index(node.name)
            rotors[index] = p
        for child in node.children:
            read_tree_names_ga(rotors,tt,rr,dd,child,p,bone_names,False)        
            
def vector_to_translator(v):
    # example: v = [1,1,1]
    t = v[0]*e1 + v[1]*e2 + v[2]*e3 
    return 1-(1/2*t*einf)


def scale_to_dilator(scale_factor):
    # example: scale = 0.7
    return 1 + ((1-scale_factor)/(1+scale_factor))*(einf^eo)

def axis_angle_to_rotor(axis,angle):
    # example: angle = 2*pi/3 
    # example: axis = [1,1,1]
    u = axis[0]*e1+axis[1]*e2+axis[2]*e3
    u = u/norm(u) 
    I3 = e1*e2*e3 # I3, 
    return e**(-(u*I3)*(angle/2)) 

def print_original():
    newv = np.zeros([(len(v)),3])
    for i in range(len(v)):
        for j in range(4):
            if vw.id[i][j] >=0:
                rotor =  (MMM[vw.id[i][j]])*BBB[vw.id[i][j]] 
    #             rotor =  (rotors[vw.id[i][j]])*BBB[vw.id[i][j]] 
                temp = up_cga_point_to_euc_point(rotor*cgav[i]*~rotor)
                newv[i] = newv[i] + vw.weight[i][j]*temp
    # p = mp.plot(newv, f,newv[:, 1],shading={"scale": 2.5,"wireframe":True},return_plot=True)

    p.add_lines(newv[f[:,0]], newv[f[:,1]], shading={"line_color": "magenta"});
    p.add_lines(newv[f[:,2]], newv[f[:,1]], shading={"line_color": "magenta"});
    p.add_lines(newv[f[:,2]], newv[f[:,0]], shading={"line_color": "magenta"});

def matrix_to_angle_axis_translation(matrix):
    # taken from:   https://github.com/Wallacoloo/printipi/blob/master/util/rotation_matrix.py
    """Convert the rotation matrix into the axis-angle notation.
    Conversion equations
    ====================
    From Wikipedia (http://en.wikipedia.org/wiki/Rotation_matrix), the conversion is given by::
        x = Qzy-Qyz
        y = Qxz-Qzx
        z = Qyx-Qxy
        r = hypot(x,hypot(y,z))
        t = Qxx+Qyy+Qzz
        theta = atan2(r,t-1)
    @param matrix:  The 3x3 rotation matrix to update.
    @type matrix:   3x3 numpy array
    @return:    The 3D rotation axis and angle.
    @rtype:     numpy 3D rank-1 array, float
    """

    # Axes.
    axis = np.zeros(3, np.float64)
    axis[0] = matrix[2,1] - matrix[1,2]
    axis[1] = matrix[0,2] - matrix[2,0]
    axis[2] = matrix[1,0] - matrix[0,1]

    # Angle.
    r = np.hypot(axis[0], np.hypot(axis[1], axis[2]))
    t = matrix[0,0] + matrix[1,1] + matrix[2,2]
    theta = math.atan2(r, t-1)

    # Normalise the axis.
    axis = axis / r

    # Return the data.
    if abs(theta) < 1e-6 :
        axis = [1,0,0]
    
    return theta, axis, matrix[0:3,3]

def up_vertex(v):
  return up(v[0]*e1+v[1]*e2+v[2]*e3)



# AUXILIARY 

def rotation_matrix( direction, angle, point=None):
    """Return matrix to rotate about axis defined by point and direction.

    >>> R = rotation_matrix(math.pi/2, [0, 0, 1], [1, 0, 0])
    >>> numpy.allclose(numpy.dot(R, [0, 0, 0, 1]), [1, -1, 0, 1])
    True
    >>> angle = (random.random() - 0.5) * (2*math.pi)
    >>> direc = numpy.random.random(3) - 0.5
    >>> point = numpy.random.random(3) - 0.5
    >>> R0 = rotation_matrix(angle, direc, point)
    >>> R1 = rotation_matrix(angle-2*math.pi, direc, point)
    >>> is_same_transform(R0, R1)
    True
    >>> R0 = rotation_matrix(angle, direc, point)
    >>> R1 = rotation_matrix(-angle, -direc, point)
    >>> is_same_transform(R0, R1)
    True
    >>> I = numpy.identity(4, numpy.float64)
    >>> numpy.allclose(I, rotation_matrix(math.pi*2, direc))
    True
    >>> numpy.allclose(2, numpy.trace(rotation_matrix(math.pi/2,
    ...                                               direc, point)))
    True

    """
    sina = math.sin(angle)
    cosa = math.cos(angle)
    direction = unit_vector(direction[:3])
    # rotation matrix around unit vector
    R = numpy.diag([cosa, cosa, cosa])
    R += numpy.outer(direction, direction) * (1.0 - cosa)
    direction *= sina
    R += numpy.array([[0.0, -direction[2], direction[1]],
                      [direction[2], 0.0, -direction[0]],
                      [-direction[1], direction[0], 0.0]])
    M = numpy.identity(4)
    M[:3, :3] = R
    if point is not None:
        # rotation not around origin
        point = numpy.array(point[:3], dtype=numpy.float64, copy=False)
        M[:3, 3] = point - numpy.dot(R, point)
    return M


def unit_vector(data, axis=None, out=None):
    """Return ndarray normalized by length, i.e. Euclidean norm, along axis.

    >>> v0 = numpy.random.random(3)
    >>> v1 = unit_vector(v0)
    >>> numpy.allclose(v1, v0 / numpy.linalg.norm(v0))
    True
    >>> v0 = numpy.random.rand(5, 4, 3)
    >>> v1 = unit_vector(v0, axis=-1)
    >>> v2 = v0 / numpy.expand_dims(numpy.sqrt(numpy.sum(v0*v0, axis=2)), 2)
    >>> numpy.allclose(v1, v2)
    True
    >>> v1 = unit_vector(v0, axis=1)
    >>> v2 = v0 / numpy.expand_dims(numpy.sqrt(numpy.sum(v0*v0, axis=1)), 1)
    >>> numpy.allclose(v1, v2)
    True
    >>> v1 = numpy.empty((5, 4, 3))
    >>> unit_vector(v0, axis=1, out=v1)
    >>> numpy.allclose(v1, v2)
    True
    >>> list(unit_vector([]))
    []
    >>> list(unit_vector([1]))
    [1.0]

    """
    if out is None:
        data = numpy.array(data, dtype=numpy.float64, copy=True)
        if data.ndim == 1:
            data /= math.sqrt(numpy.dot(data, data))
            return data
    else:
        if out is not data:
            out[:] = numpy.array(data, copy=False)
        data = out
    length = numpy.atleast_1d(numpy.sum(data*data, axis))
    numpy.sqrt(length, length)
    if axis is not None:
        length = numpy.expand_dims(length, axis)
    data /= length
    if out is None:
        return data
    return None

