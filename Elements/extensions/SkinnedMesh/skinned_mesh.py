# import time

from re import M
from Elements.features.SkinnedMesh.gate_module import *
from Elements.features.SkinnedMesh.System_skinning import System_skinning
import pathlib



class Skinned_mesh :
    """
    A concrete Sinned_mesh class

    Accepts a dedicated animation file to initiate the visualization of the model, using its vertex attributes
    """
    
    def __init__(self, mesh_id, filename=None, file_type=None, animation=False):
        """ Initialize the generic Skinned_mesh component with the name of the animation file and its type (e.g. .dae), 
        these will be passed to pyassimp load function in order to load the desired model
        then we initialize its vertex attributes, the bones and colors so we can generate the model. 

        """
        
        if (filename is None):
            self._filename = self.getClassName()
        else:
            self._filename = filename
        
        if (file_type is None):
            self._file_type = self.getClassName()
        else:
            self._file_type = file_type
        
        if (isinstance(self._filename, pathlib.Path )):
            self._filename = str(self._filename)

        self.model = load(self._filename,self._file_type)
        # print("1:",self.model)
        # print("2:",self.model.animations[0].channels[0].positionkeys[0].value)
        if(self.model==None): 
          return None  
      
        self.frame_cntr = 0
        self.forward = True
        self.mesh_id = mesh_id
        self.mesh = self.model.meshes[self.mesh_id]   
        self.f = self.mesh.faces
        self.changedframes = False
        if(len(self.f)==0):
            return None
        
        self.b = self.mesh.bones
        
        # if(len(self.b)==0):
        #     return None 
        
        color_list = []
        for i in range(len(self.mesh.vertices)):
            p = np.array([1.0, 0.0, 0.0])
            color_list.append(p)
        color_array = np.array(color_list)
        self.mesh.colors = color_array
        self.model.meshes[self.mesh_id] = self.mesh
        self.colors = color_array
        print(animation)
        if not (animation):
            print("in")
            
            self.oldv = self.mesh.vertices
            self.v = self.oldv.copy()
            print(self.v[0])
            for i in range(len(self.v)):
                
                for j in range(len(self.v[i])):
                    self.v[i][j] += 5.0
                
        else:
            temp = System_skinning()
            self.oldv = self.mesh.vertices
            newv = temp.generate_mesh(self.mesh.vertices, self.b, self.model, self.mesh_id)
            self.v = newv  
        self.interpolation = []
        self.frames = 50.0
        for i in range(len(self.v)):
            self.interpolation.append([(self.v[i][0]-self.oldv[i][0])/self.frames, (self.v[i][1]-self.oldv[i][1])/self.frames, (self.v[i][2]-self.oldv[i][2])/self.frames])
            # for i in range(int(self.frames/2)):
            #     for i in range(len(self.oldv)):
            #         self.oldv[i][0] = self.oldv[i][0] + self.interpolation[i][0]
            #         self.oldv[i][1] = self.oldv[i][1] + self.interpolation[i][1]
            #         self.oldv[i][2] = self.oldv[i][2] + self.interpolation[i][2]
                
              
        if(len(self.v)==0):
            return None   
    
    def updateFrames(self, frames):
        if(self.frames == frames):
            return
        self.interpolation = []
        self.frames = frames
        for i in range(len(self.v)):
            self.interpolation.append([(self.v[i][0]-self.oldv[i][0])/self.frames, (self.v[i][1]-self.oldv[i][1])/self.frames, (self.v[i][2]-self.oldv[i][2])/self.frames])
        self.changedframes = True
        
     
    def applystep(self, currvertpos):
        if(self.changedframes):
            self.changedframes = False
            self.frame_cntr = 0
            currvertpos = np.array(self.oldv)
            return currvertpos
        if(self.frame_cntr <= 0):
            self.forward = True
        elif(self.frame_cntr >= int(self.frames)):
            self.forward = False
        if(self.forward):
            for i in range(len(currvertpos)):
                if (self.frame_cntr < int(self.frames)):
                    currvertpos[i][0] = currvertpos[i][0] + self.interpolation[i][0]
                    currvertpos[i][1] = currvertpos[i][1] + self.interpolation[i][1]
                    currvertpos[i][2] = currvertpos[i][2] + self.interpolation[i][2]
            self.frame_cntr += 1    
        else :
            for i in range(len(currvertpos)):
                if (self.frame_cntr > 0):
                    currvertpos[i][0] = currvertpos[i][0] - self.interpolation[i][0]
                    currvertpos[i][1] = currvertpos[i][1] - self.interpolation[i][1]
                    currvertpos[i][2] = currvertpos[i][2] - self.interpolation[i][2]
            self.frame_cntr -= 1    
        return currvertpos
            
       
    def coloringvert(self):
        z_list = []
        y_list = []
        all_list = []
        for i in range(len(self.v)):
            if (self.v[i][2] in z_list): continue
            else:
                z_list.append(self.v[i][2])
                
            if (self.v[i][1] in y_list): continue
            else:
                y_list.append(self.v[i][1])
        
        z_list.sort()
        y_list.sort()
        step_z = 1/len(z_list)
        step_y = 1/len(y_list)
        
        green_z = 1
        red_z = 0
        blue_z = 0
        
        green_y = 0
        red_y = 0
        blue_y = 1
        
        green_x = 1
        red_x = 0
        blue_x = 0
        
        colordict_z = {}
        colordict_y = {}
        for i in range(len(z_list)):       
            colordict_z[z_list[i]] = [red_z,green_z,0.0]
            green_z -= step_z
            red_z += step_z
            
        for i in range(len(y_list)):       
            colordict_y[y_list[i]] = [red_y,green_y,blue_y]
            green_y += step_y
            red_y += step_y
            blue_y -= step_y
        
        # z_el = len(z_list)
        # y_el = len(y_list)
        # if (z_el >= y_el): m = z_el
        # else : m = y_el
        # for i in range(len(m)):
        #     if(z_list[i] == y_list[i]):
        #         all_list.append(z_list[i]) 
            
        for i in range(len(self.v)):
            # [sum(x) for x in zip(list1, list2)]
            # combinedcolor = (colordict_z[self.v[i][2]]+colordict_y[self.v[i][1]])
            combinedcolor = [sum(x) for x in zip(colordict_z[self.v[i][2]],colordict_y[self.v[i][1]])]
            combinedcolor[:] = [x / 2 for x in combinedcolor]
            self.colors[i] = np.array(combinedcolor)
            
    
    
    