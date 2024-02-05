import Elements.pyECSS
import Elements.pyECSS.System

import Elements.extensions.GA.quaternion as quat
from pyassimp import load
from Elements.extensions.SkinnedMesh.gate_module import *

import Elements.pyECSS.Component
from Elements.pyECSS.Component import Component
from Elements.pyECSS.Component import CompNullIterator
import Elements.pyECSS.math_utilities as util
import numpy as np
import math

WW = None
WW_9 = None
figure = None

class Keyframe(Component):

    def __init__(self, name=None, type=None, id=None, array_MM=None):
        super().__init__(name, type, id)

        self._parent = self
        if not array_MM:
            self._array_MM = [] 
        else:
            self._array_MM = array_MM
    
    @property
    def array_MM(self):
        return self._array_MM
    
    @array_MM.setter
    def array_MM(self, value):
        self._array_MM = value 

    def update(self):
        pass
   
    def accept(self, system: Elements.pyECSS.System, event = None):
        #system.apply2Keyframe(self)
        pass
    
    def init(self):
        pass
    
    def print(self):
        """
        prints out name, type, id, parent of this Component
        """
        print(f"\n {self.getClassName()} name: {self._name}, type: {self._type}, id: {self._id}, parent: {self._parent._name}, array_MM: \n{self._array_MM}")
        print(f" ______________________________________________________________")
    
    def __str__(self):
        return f"\n {self.getClassName()} name: {self._name}, type: {self._type}, id: {self._id}, parent: {self._parent._name}, array_MM: \n{self._array_MM}"

    def __iter__(self) ->CompNullIterator:
        """ A component does not have children to iterate, thus a NULL iterator
        """
        return CompNullIterator(self) 
    

class AnimationComponents(Component):

    def __init__(
                self,
                name=None,
                type=None,
                id=None, 
                keyframe=None, 
                bones=None,
                alpha=0, 
                tempo=2, 
                time_add=0, 
                animation_start = True, 
                anim_keys = 2, 
                time = [0, 100, 200], 
                flag = True, 
                inter = 'SLERP'):
        
        super().__init__(name, type, id)
        self._parent = self

        self.alpha = alpha
        self.tempo = tempo
        self.time_add = time_add
        self.anition_start = animation_start
        self.animKeys = anim_keys
        self.inter = inter
        self.time = time
        self.flag = flag

        self.MM = []

        if not keyframe:
            self._keyframe = [] 
        else:
            self._keyframe = keyframe

        if not bones:
            self._bones = [] 
        else:
            self._bones = bones

    @property
    def bones(self):
        return self._bones
    
    @bones.setter
    def bones(self, value):
        self._bones = value 

    #Animation loop
    def animation_loop(self):
        #Filling MM1 with 4x4 identity matrices
        self.MM = [np.eye(4) for _ in self.keyframe[0]]

        if (self.time_add >= self.time[1] and self.keyframe[2] is None) or (self.time_add >= self.time[2]):
            self.flag = False
        elif self.time_add <= self.time[0]:
            self.flag = True


        if self.time_add >= self.time[0] and self.time_add <= self.time[1]:
            self.animation_for_loop(self.keyframe[0],self.keyframe[1], self.time[0], self.time[1])
        elif self.time_add > self.time[1] and self.time_add <= self.time[2] and self.keyframe[2] is not None:
            self.animation_for_loop(self.keyframe[1], self.keyframe[2], self.time[1], self.time[2])
        
        
        #So we can have repeating animation
        if self.flag == True:
            if self.anition_start == True:
                self.time_add += self.tempo
            else:
                self.time_add = self.time_add
        else:
            if self.anition_start == True:
                self.time_add -= self.tempo
            else:
                self.time_add = self.time_add

        # Flattening MM1 array to pass as uniform variable
        self.MM =  np.array(self.MM, dtype=np.float32).reshape((len(self.MM), 16))

        return self.MM

    def animation_for_loop(self, k_1, k_2, t0, t1):
        self.alpha = (self.time_add - t0) / abs(t1 - t0)

        keyframe1 = Keyframe(array_MM=[k_1])
        keyframe2 = Keyframe(array_MM=[k_2])

        # print(keyframe1.array_MM[0][1])
        for i in range(len(k_1)):

            translation_1 = translation(keyframe1.array_MM[0][i])
            translation_2 = translation(keyframe2.array_MM[0][i])

            rotation_1 = rotationEulerAngles(keyframe1.array_MM[0][i])
            rotation_2 = rotationEulerAngles(keyframe2.array_MM[0][i])

            rq1 = quat.Quaternion.euler_to_quaternion(math.radians(rotation_1[0]), math.radians(rotation_1[1]), math.radians(rotation_1[2]))
            rq2 = quat.Quaternion.euler_to_quaternion(math.radians(rotation_2[0]), math.radians(rotation_2[1]), math.radians(rotation_2[2]))
            rq1 = rq1 / rq1.norm()
            rq2 = rq2 / rq2.norm()

            scale_1 = scale(keyframe1.array_MM[0][i])
            scale_2 = scale(keyframe2.array_MM[0][i])


            if(self.inter == "LERP"):
                rl = quat.quaternion_lerp(rq1, rq2, self.alpha)
            else:
                rl = quat.quaternion_slerp(rq1, rq2, self.alpha)
            
            sl = self.lerp(scale_1, scale_2, self.alpha)
            sc = util.scale(sl[0],sl[1],sl[2])
            self.MM[i][:3, :3] = sc[:3, :3] @ quat.Quaternion.to_rotation_matrix(rl)
            self.MM[i][:3, 3] = self.lerp(translation_1, translation_2, self.alpha)

    def lerp(self,a, b, t):
        return (1 - t) * a + t * b
     
    def drawSelfGui(self, imgui):
        global WW
        global WW_9

        imgui.begin("Animation", True)
        _, self.tempo = imgui.drag_float("Alpha Tempo", self.tempo, 0.01, 0, 5)
        _, self.anition_start = imgui.checkbox("Animation", self.anition_start)
        
        i = 0
        for k in self.keyframe:
            if imgui.tree_node("Keyframe " + str(i)):
                j = 0
                for mm in k:
                    if imgui.tree_node("Joint " + str(j)):

                        imgui.text("My Value: {}".format(mm))

                        tran_x, WW_9[i][j][0] = imgui.drag_float("Translate X", WW_9[i][j][0], 0.1, -10, 10)
                        tran_y, WW_9[i][j][1] = imgui.drag_float("Translate Y", WW_9[i][j][1], 0.1, -10, 10)
                        tran_z, WW_9[i][j][2] = imgui.drag_float("Translate Z", WW_9[i][j][2], 0.1, -10, 10)

                        rot_x,  WW_9[i][j][3]    = imgui.drag_float("Rotate X", WW_9[i][j][3], 0.1, -3, 3)
                        rot_y,  WW_9[i][j][4]    = imgui.drag_float("Rotate Y", WW_9[i][j][4], 0.1, -3, 3)
                        rot_z,  WW_9[i][j][5]    = imgui.drag_float("Rotate Z", WW_9[i][j][5], 0.1, -3, 3)

                        sc_x,  WW_9[i][j][6]     = imgui.drag_float("Scale X", WW_9[i][j][6], 0.01, 0.1, 1)
                        sc_y,  WW_9[i][j][7]     = imgui.drag_float("Scale Y", WW_9[i][j][7], 0.01, 0.1, 1)
                        sc_z,  WW_9[i][j][8]     = imgui.drag_float("Scale Z", WW_9[i][j][8], 0.01, 0.1, 1)

                        if tran_x or tran_y or tran_z or rot_x or rot_y or rot_z or sc_x or sc_y or sc_z:
                            temp = util.scale(WW_9[i][j][6], WW_9[i][j][7], WW_9[i][j][8]) @ eulerAnglesToRotationMatrix4(WW_9[i][j][3], WW_9[i][j][4], WW_9[i][j][5])
                            temp[0][3] = WW_9[i][j][0]
                            temp[1][3] = WW_9[i][j][1]
                            temp[2][3] = WW_9[i][j][2]

                            WW[i][j] = temp
                            self.keyframe[i] = read_tree(figure,0,WW[i],True)

                        imgui.tree_pop()
                    j += 1
                imgui.tree_pop()
            i += 1
        imgui.end()

    def update(self):
        pass
   
    def accept(self, system: Elements.pyECSS.System, event = None):
        pass
    
    def init(self):
        pass


def lerp(a, b, t):
    return (1 - t) * a + t * b


def eulerAnglesToRotationMatrix4(x, y, z) :  
    R_x = np.array([[1,            0,             0,            0],
                    [0,            math.cos(x),   -math.sin(x), 0],
                    [0,            math.sin(x),   math.cos(x),  0],
                    [0,            0,             0,            1]
                    ])                    
    R_y = np.array([[math.cos(y),  0,             math.sin(y),  0],
                    [0,            1,             0,            0],
                    [-math.sin(y), 0,             math.cos(y),  0],
                    [0,            0,             0,            1]
                    ])            
    R_z = np.array([[math.cos(z),  -math.sin(z),  0,            0],
                    [math.sin(z),  math.cos(z),   0,            0],
                    [0,            0,             1,            0],
                    [0,            0,             0,            1]
                    ])                  
    R = np.dot(R_z, np.dot( R_y, R_x ))
    return R


def translation(matrix):
    return matrix[:3,3];


def rotationEulerAngles(matrix):
    # First get rotation matrix from trs. Divide by scale
    rotationMatrix = matrix.copy();
    sc = scale(matrix);
    rotationMatrix = rotationMatrix @ util.scale(1/sc[0], 1/sc[1], 1/sc[2])
    myR = rotationMatrix[:3,:3]
    if myR[2,0] not in [-1,1]:
        y = -np.arcsin(myR[2,0]);
        x = np.arctan2(myR[2,1]/np.cos(y), myR[2,2]/np.cos(y));
        z = np.arctan2(myR[1,0]/np.cos(y), myR[0,0]/np.cos(y));
    else:
        z = 0;
        if myR[2,0] == -1:
            y = np.pi/2;
            x = z + np.arctan2(myR[0,1], myR[0,2]);
        else:
            y = -np.pi/2;
            x = -z + np.arctan2(-myR[0,1], -myR[0,2]);
    return np.array([x,y,z])*180/np.pi;


def scale(matrix):
    m = matrix.copy()[:3,:3];
    A = m.transpose() @ m
    # if m = R @ S then A = m^T @ m = S^T @ R^T @ R @ S = S^T @ S = S^2
    sx = np.sqrt(A[0,0])
    sy = np.sqrt(A[1,1])
    sz = np.sqrt(A[2,2])
    return numpy.array([sx, sy, sz])


#need to add 2 M arrays, one for Keyframe1 and and one for Keyframe2 
def animation_initialize(file, ac, keyframe1, keyframe2, keyframe3 = None):
    global figure 
    global WW
    global WW_9
    figure = load(str(file))
    
    # print(figure.rootnode)

    mesh_id = 0

    #Vertices, Incdices/Faces, Bones from the scene we loaded with pyassimp
    mesh = figure.meshes[mesh_id]
    v = mesh.vertices
    f = mesh.faces
    b = mesh.bones

    # variables = figure.rootnode
    # for key, value in variables.items():
    #     print(f"{key}: {value}")
    print("Mesh", mesh)
    print("vertices", v)
    print("faces", f)
    print("bones", b)

    # for bone in b:
    #     print(f"Bone Name: {bone.name}")
        # print(f"Parent Index: {bone.parentindex}")
        # print(f"Offset Matrix: {bone.offsetmatrix}")
    
    #Populating vw with the bone weight and id
    vw = vertex_weight(len(v))
    vw.populate(b)

    #Homogenous coordinates for the vertices
    v2 = np.concatenate((v, np.ones((v.shape[0], 1))), axis=1)

    #Creating random colors based on height
    c = []
    min_y = min(v, key=lambda v: v[1])[1]
    max_y = max(v, key=lambda v: v[1])[1]
    for i in range(len(v)):
        color_y = (v[i][1] - min_y) / (max_y - min_y)
        c.append([0, color_y, 1-color_y , 1])

    #Flattening the faces array
    f2 = f.flatten()

    transform = True

    #Initialising M array
    M = initialize_M(b)

    WW = np.array([[np.eye(4) for _ in range(len(M))] for _ in range(3)])

    WW_9 = [[[0] * 6 + [1, 1, 1] for _ in range(len(M))] for _ in range(3)]

    #print(M)
    #Initialising first keyframe
    # M[1] = np.dot(np.diag([1,1,1,1]),M[1])
    
    keyframe1.array_MM.append(read_tree(figure,mesh_id,M,transform))
    for i in range(0,len(WW_9[0])):
        WW_9[0][i][:3] = translation(keyframe1.array_MM[0][i])
        WW_9[0][i][3:6] = (rotationEulerAngles(keyframe1.array_MM[0][i])/180)*np.pi
        WW_9[0][i][6:9] = scale(keyframe1.array_MM[0][i])

    #Initialising second keyframe
    # M[1][0:3,0:3] = eulerAnglesToRotationMatrix([0.3,0.3,0.4])
    # M[1][0:3,3] = [0.5,0.5,0.5]

    keyframe2.array_MM.append(read_tree(figure,mesh_id,M,transform))
    for i in range(0,len(WW_9[0])):
        WW_9[1][i][:3] = translation(keyframe2.array_MM[0][i])
        WW_9[1][i][3:6] = (rotationEulerAngles(keyframe2.array_MM[0][i])/180)*np.pi
        WW_9[1][i][6:9] = scale(keyframe2.array_MM[0][i])


    if keyframe3 != None:
        # M[1][0:3,0:3] = eulerAnglesToRotationMatrix([-0.5,0.3,0.4])
        # M[1][0:3,3] = [0.5,0.5,0.5]
        keyframe3.array_MM.append(read_tree(figure,mesh_id,M,transform))
        
        for i in range(0,len(WW_9[0])):
            WW_9[2][i][:3] = translation(keyframe3.array_MM[0][i])
            WW_9[2][i][3:6] = (rotationEulerAngles(keyframe3.array_MM[0][i])/180)*np.pi
            WW_9[2][i][6:9] = scale(keyframe3.array_MM[0][i])

    #Initialising BB array
    BB = [b[i].offsetmatrix for i in range(len(b))]

    # Flattening BB array to pass as uniform variable
    ac.bones.append(np.array(BB, dtype=np.float32).reshape((len(BB), 16)))
    
    return v2, c, vw.weight, vw.id, f2
