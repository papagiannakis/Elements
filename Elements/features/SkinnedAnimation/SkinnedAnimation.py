import Elements.pyECSS
import Elements.pyECSS.System

import Elements.features.GA.quaternion as quat
from pyassimp import load
from Elements.features.SkinnedMesh.gate_module import *

import Elements.pyECSS.Component
from Elements.pyECSS.Component import Component
from Elements.pyECSS.Component import CompNullIterator
import numpy as np
import math

theta_x = 0.0 
theta_y = 0.0 
theta_z = 0.0 

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

    @property #translation vector
    def translate(self):
        tempMatrix = self.array_MM.copy();
        translateMatrix = [];
        for i in range(len(tempMatrix)):
            for j in range(len(tempMatrix[i])):
                translateMatrix.append(tempMatrix[i][j][:3,3])
        return translateMatrix

    @property #rotation vector
    def rotate(self):
        # First get rotation matrix from trs. Divide by scale
        tempMatrix = self.array_MM.copy();
        rotateMatrix = [];
        for i in range(len(tempMatrix)):
            for j in range(len(tempMatrix[i])):
                rotateMatrix.append(quat.Quaternion.from_rotation_matrix(tempMatrix[i][j]))
        return rotateMatrix


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

    def __init__(self, name=None, type=None, id=None, keyframe=None, bones=None, MM=None, alpha=0, tempo=2, time_add=0, animation_start = True, anim_keys = 2, time = [0, 100, 200], flag = True, inter = 'SLERP'):
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
        MM1Data =  np.array(self.MM, dtype=np.float32).reshape((len(self.MM), 16))

        return MM1Data
    
    def animation_for_loop(self, k_1, k_2, t0, t1):
        self.alpha = (self.time_add - t0) / abs(t1 - t0)

        keyframe1 = Keyframe(array_MM=[k_1])
        keyframe2 = Keyframe(array_MM=[k_2])

        for i in range(len(k_1)):
            if(self.inter == "LERP"):
                self.MM[i][:3, :3] = quat.Quaternion.to_rotation_matrix(quat.quaternion_lerp(keyframe1.rotate[i], keyframe2.rotate[i], self.alpha))
                self.MM[i][:3, 3] = self.lerp(keyframe1.translate[i], keyframe2.translate[i], self.alpha)
            else:
                #SLERP
                self.MM[i][:3, :3] = quat.Quaternion.to_rotation_matrix(quat.quaternion_slerp(keyframe1.rotate[i], keyframe2.rotate[i], self.alpha))
                #LERP
                self.MM[i][:3, 3] = self.lerp(keyframe1.translate[i], keyframe2.translate[i], self.alpha)

    def lerp(self,a, b, t):
        return (1 - t) * a + t * b
     
    def drawSelfGui(self, imgui):
        global theta_x
        global theta_y
        global theta_z
        
        imgui.begin("Animation", True)
        # _, self.tempo = imgui.drag_float("Alpha Tempo", self.tempo, 1, 0, self.time[-1])
        _, self.tempo = imgui.drag_float("Alpha Tempo", self.tempo, 0.01, 0, 5)
        _, self.anition_start = imgui.checkbox("Animation", self.anition_start)
        
        i = 0
        for k in self.keyframe:
            if imgui.tree_node("Keyframe " + str(i)):
                j = 0
                for mm in k:
                    if imgui.tree_node("Joint " + str(j)):

                        imgui.text("My Value: {}".format(mm))
                        _, mm[0][3] = imgui.drag_float("Translate X", mm[0][3], 0.5, mm[0][3] - 10, mm[0][3] + 10)
                        _, mm[1][3] = imgui.drag_float("Translate Y", mm[1][3], 0.5, mm[1][3] - 10, mm[1][3] + 10)
                        _, mm[2][3] = imgui.drag_float("Translate Z", mm[2][3], 0.5, mm[2][3] - 10, mm[2][3] + 10)

                        changed_x, theta_x    = imgui.drag_float("Rotate X", theta_x, 0.1, 0, 2 * math.pi)
                        changed_y, theta_y    = imgui.drag_float("Rotate Y", theta_y, 0.1, 0, 2 * math.pi)
                        changed_z, theta_z    = imgui.drag_float("Rotate Z", theta_z, 0.1, 0, 2 * math.pi)

                        if changed_x:
                            mm[1][1] = mm[1][1] * math.cos(theta_x)
                            mm[1][2] = -mm[1][2] * math.sin(theta_x)
                            mm[2][1] = mm[1][2] * math.sin(theta_x)
                            mm[2][2] = mm[2][2] * math.cos(theta_x)
                        if changed_y:
                            mm[0][0] = mm[0][0] * math.cos(theta_y)
                            mm[0][2] = mm[0][2] * math.sin(theta_y)
                            mm[2][0] = -mm[2][0] * math.sin(theta_y)
                            mm[2][2] = mm[2][2] * math.cos(theta_y)
                        if changed_z:
                            mm[0][0] = mm[0][0] * math.cos(theta_z)
                            mm[0][1] = -mm[0][1] * math.sin(theta_z)
                            mm[1][0] = mm[1][0] * math.sin(theta_z)
                            mm[1][1] = mm[1][1] * math.cos(theta_z)

                        _, mm[0][0]     = imgui.drag_float("Scale X", mm[0][0], 0.5, mm[0][0] - 0.2, mm[0][0] + 1)
                        _, mm[1][1]     = imgui.drag_float("Scale Y", mm[1][1], 0.5, mm[1][1] - 0.2, mm[1][1] + 1)
                        _, mm[2][2]     = imgui.drag_float("Scale Z", mm[2][2], 0.5, mm[2][2] - 0.2, mm[2][2] + 1)
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

#need to add 2 M arrays, one for Keyframe1 and and one for Keyframe2 
def animation_initialize(file, ac, keyframe1, keyframe2, keyframe3 = None):
    figure = load(str(file))
    mesh_id = 3

    #Vertices, Incdices/Faces, Bones from the scene we loaded with pyassimp
    mesh = figure.meshes[mesh_id]
    v = mesh.vertices
    f = mesh.faces
    b = mesh.bones

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

    #Initialising first keyframe
    M[1] = np.dot(np.diag([1,1,1,1]),M[1])
    keyframe1.array_MM.append(read_tree(figure,mesh_id,M,transform))

    #Initialising second keyframe
    M[1][0:3,0:3] = eulerAnglesToRotationMatrix([0.3,0.3,0.4])
    M[1][0:3,3] = [0.5,0.5,0.5]
    keyframe2.array_MM.append(read_tree(figure,mesh_id,M,transform))

    if keyframe3 != None:
        M[1][0:3,0:3] = eulerAnglesToRotationMatrix([-0.5,0.3,0.4])
        M[1][0:3,3] = [0.5,0.5,0.5]
        keyframe3.array_MM.append(read_tree(figure,mesh_id,M,transform))
    #Initialising BB array
    BB = [b[i].offsetmatrix for i in range(len(b))]

    # Flattening BB array to pass as uniform variable
    ac.bones.append(np.array(BB, dtype=np.float32).reshape((len(BB), 16)))
    
    return v2, c, vw.weight, vw.id, f2
