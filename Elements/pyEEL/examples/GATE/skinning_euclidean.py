# python package created by Manos Kamarianakis

# =================================================
# Used to load the model and the animation via pyassimp from a .dae file
# and to create the skeleton and the animation data structures
# to be used in the animation loop.
# =================================================


import warnings
warnings.filterwarnings('ignore')

import numpy as np
from numpy import e,pi

from pyassimp import *
import pyassimp
import meshplot as mp
# from numba import jit,njit

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
    # =================================================
    # Get the names of the bones
    # =================================================
    """
    b: bones
    """
    return [str(b[i]) for i in range(len(b))]
        
def vertex_apply_M(v,M):
    # =================================================
    # Apply the transformation matrix M to the vertices v
    # =================================================
    return np.dot(M,np.append(v,[1.0]))[0:3]

def eulerAnglesToRotationMatrix(theta) :  
    # =================================================
    # Convert the Euler angles to a rotation matrix
    # =================================================
    R_x = np.array([[1,         0,                  0               ],
                    [0,         np.cos(theta[0]), -np.sin(theta[0]) ],
                    [0,         np.sin(theta[0]), np.cos(theta[0])  ]
                    ])                    
    R_y = np.array([[np.cos(theta[1]),    0,      np.sin(theta[1])  ],
                    [0,                     1,      0               ],
                    [-np.sin(theta[1]),   0,      np.cos(theta[1])  ]
                    ])             
    R_z = np.array([[np.cos(theta[2]),    -np.sin(theta[2]),    0],
                    [np.sin(theta[2]),    np.cos(theta[2]),     0],
                    [0,                     0,                  1]
                    ])                  
    return R_z @ R_y @ R_x 

  
def draw_original_wireframe():
    p.add_lines(v[f[:,0]], v[f[:,1]], shading={"line_color": "magenta"});
    p.add_lines(v[f[:,2]], v[f[:,1]], shading={"line_color": "magenta"});
    p.add_lines(v[f[:,2]], v[f[:,0]], shading={"line_color": "magenta"});


def initialize_M(b):
    # =================================================
    # Initialize the transformation matrices
    # =================================================
    M = np.zeros([len(b),4,4])
    for i in range(len(b)):
        M[i] = np.identity(4)
    return M

def get_bone_names(b):
    # =================================================
    # Get the names of the bones
    # =================================================
    return [str(b[i]) for i in range(len(b))]

def read_tree(scene,mesh_id,M,transform):
  b = scene.meshes[mesh_id].bones
  MM = np.zeros([len(b),4,4])
  G = np.linalg.inv(scene.rootnode.transformation)
  bone_names = get_bone_names(b)
  read_tree_names(MM,M,scene.rootnode,G,bone_names,transform)
  return MM

def read_tree_names(MM,M,node,parentmatrix,bone_names, transform = False):
    # =================================================
    # Read the tree and get the transformation matrices
    # =================================================
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
    # =================================================
    # Draw the vertices affected by the boneID
    # =================================================
    vertices_ids_affected_by_boneID = [b[boneID].weights[i].vertexid for i in range(len(b[boneID].weights))]
    weights_affected_by_boneID = [b[boneID].weights[i].weight for i in range(len(b[boneID].weights))]
    IDs = vertices_ids_affected_by_boneID
    print("red points are the ones affected by :", b[boneID])
#     p.add_points(v[IDs], shading={"point_size": 0.7,"point_color": "red"}); 
    p.add_points(newv[IDs], shading={"point_size": 1,"point_color": "red"}); 





def draw_vertices_affected_by_boneID(boneID):
    # =================================================
    # Draw the vertices affected by the boneID
    # =================================================
    vertices_ids_affected_by_boneID = [b[boneID].weights[i].vertexid for i in range(len(b[boneID].weights))]
    IDs = vertices_ids_affected_by_boneID
    print("red points are the ones affected by :", b[boneID])
    p.add_points(v[IDs], shading={"point_size": 0.7,"point_color": "red"}); 

