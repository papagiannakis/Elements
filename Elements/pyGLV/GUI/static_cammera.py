
import glm
import glfw
import numpy as np 
import Elements.pyECSS.math_utilities as util  
from Elements.pyGLV.GUI.Viewer import button_map

class cammera: 
    def __init__(self, eye, target, up):
        self._eye = eye 
        self._target = target 
        self._up = up 

        self.camt = {};
        self.camt["x"] = 0; self.camt["y"] = 0; self.camt["z"] = 0; 

        self.camr = {};
        self.camr["x"] = 0; self.camr["y"] = 0; self.camr["z"] = 0; 

        self.cams = {};
        self.cams["x"] = 0; self.cams["y"] = 0; self.cams["z"] = 0; 

        self._updateCamera = None
        self.createViewMatrix(self._eye, self._target, self._up) 

        self._mouse_noop_x_state = 0
        self._mouse_noop_y_state = 0
        # test_example = true 

    def resetAll(self):
        self.camt["x"] = 0.0
        self.camt["y"] = 0.0
        self.camt["z"] = 0.0
        self.camr["x"] = 0.0
        self.camr["y"] = 0.0
        self.camr["z"] = 0.0
        self.cams["x"]= 1.0
        self.cams["y"]= 1.0
        self.cams["z"]= 1.0
        
    def createViewMatrix(self, eye, lookAt, up): 
        self._eye = util.vec(tuple(eye)) 
        self._target = util.vec(tuple(lookAt)) 
        
        #self._up = tuple(upVector)
        #directionVector = util.normalise(lookAt - eye) 
        #rightVector = util.normalise(np.cross(directionVector, upVector))
        #upVector = util.normalise(np.cross(rightVector, directionVector)) 
        #self.wrapeeWindow._updateCamera = util.lookat(eye, lookAt, upVector) 

        self._updateCamera = glm.transpose(glm.lookAtLH(self._eye, self._target, up))   
        
    def updateCamera(self, moveX, moveY, moveZ, rotateX, rotateY):   
        cameraspeed = 0.1
        teye = np.array(self._eye)
        ttarget = np.array(self._target)
        tup = np.array(self._up)

        forwardDir = util.normalise(ttarget - teye)
        rightDir = util.normalise(np.cross(forwardDir, tup))

        if rotateX:
            rotMatY = util.rotate(tup, self.camr["x"] * cameraspeed*15)
            transMatY = util.translate(ttarget) @ rotMatY @ util.translate(-ttarget)
            teye = transMatY @ np.append(teye, [1])
            teye = teye[:-1] / teye[-1]
        elif rotateY:
            rotMatX = util.rotate(rightDir, -self.camr["y"] * cameraspeed*15)
            transMatX = util.translate(ttarget) @ rotMatX @ util.translate(-ttarget)
            teye = transMatX @ np.append(teye, [1])
            teye = teye[:-1] / teye[-1]
        elif moveX or moveY:
            panX = -cameraspeed * self.camt["x"] * rightDir
            panY = -self.camt["y"] * cameraspeed * tup
            teye += panX + panY
            ttarget += panX + panY
        elif moveZ:
            zoom =  np.sign(self.camt["z"]) * cameraspeed * forwardDir
            teye += zoom
            ttarget += zoom
        self.createViewMatrix(teye, ttarget, tup)

    def cameraHandling(self, xx, yy, x=0, y=0, z=0):
        # keystatus = sdl2.SDL_GetKeyboardState(None)
        self.resetAll()

        if abs(xx) > abs(yy):
            self.camr["x"] = np.sign(xx) #event.wheel.x/height*180
            self.updateCamera(False, False,False, True, False)
        else:
            self.camr["y"] = np.sign(yy) #event.wheel.y/width*180
            self.updateCamera(False, False,False, False, True)  

    def update(self, canvas):
        width = canvas._windowWidth
        height = canvas._windowHeight  

        x, y = canvas.GetMousePos()
        if button_map[glfw.MOUSE_BUTTON_2] in canvas._pointer_buttons:
                _x = np.floor(x - self.mouse_noop_x_state) 
                _y = np.floor(y - self.mouse_noop_y_state) 
                self.cameraHandling(_x, _y, height, width) 
        else:
            self.mouse_noop_x_state = np.floor(x)
            self.mouse_noop_y_state = np.floor(y)