import glm
import glfw
import numpy as np 
import Elements.pyECSS.math_utilities as util  
from Elements.pyGLV.GUI.Viewer import button_map
from Elements.pyGLV.GUI.windowEvents import EventTypes

class cammera:
    def __init__(self, postition:any, theta:any, phi:any): 
        self.position = postition
        self.target = glm.vec3(0)
        self.eulers = [0.0, phi, theta]
        self.forward = glm.vec3(0)
        self.right = glm.vec3(0)
        self.up = glm.vec3(0)

        self.view = glm.transpose(glm.lookAtLH(glm.vec3(self.position), glm.vec3(0.0, 0.0, 0.0), glm.vec3(0.0, 0.0, 1.0)))

        self.forward_state = 0;
        self.right_state = 0;

        self.mouse_noop_x = 0;
        self.mouse_noop_y = 0;
    
    def getView(self):
        return self.view; 

    def getPos(self): 
        return self.position;

    def spinCammera(self, dx:any, dy:any):
        self.eulers[2] -= dx;
        self.eulers[2] %= 360;
    
        # self.eulers[1] = float(np.min(float(89.0), float(np.max( -89.0, float(self.eulers[1] + dy)))))
        self.eulers[1] = glm.min(89, glm.max(-89, self.eulers[1] + dy))

    def moveCammera(self, forward_amount:any, right_amout:any): 
        forward = glm.vec3(
            self.forward.x * forward_amount,
            self.forward.y * forward_amount,
            self.forward.z * forward_amount
        )

        self.position = glm.add(self.position, forward)

        right = glm.vec3(
            self.right.x * right_amout,
            self.right.y * right_amout,
            self.right.z * right_amout
        )

        self.position = glm.add(self.position, right)


    def cammeraUpdate(self): 
        self.forward = glm.vec3( 
            glm.cos(glm.radians(self.eulers[2])) * glm.cos(glm.radians(self.eulers[1])),
            glm.sin(glm.radians(self.eulers[2])) * glm.cos(glm.radians(self.eulers[1])),
            glm.sin(glm.radians(self.eulers[1])),
        )

        self.right = glm.vec3(glm.cross(self.forward, [0,0,1]))
        self.up = glm.vec3(glm.cross(self.right, self.forward)) 
        self.target = glm.vec3(glm.add(self.position, self.forward)) 
        # self.target = glm.vec3(0.0, 0.0, 0.0)

        self.view = glm.transpose(glm.lookAtLH(self.position, self.target, self.up))
        # print(glm.rotate(glm.radians(-90), glm.vec3(1, 0, 0))) 
        # print("\n")
        self.view = glm.rotate(glm.radians(-90), glm.vec3(1, 0, 0)) * self.view

    def update(self, canvas, event): 
        sensitivity = 0.7

        self.forward_state = 0
        self.right_state = 0

        if canvas.IsKeyPressed('W'):
            self.forward_state = 0.02
        elif canvas.IsKeyPressed('S'):
            self.forward_state = -0.02

        if canvas.IsKeyPressed('A'):
            self.right_state = 0.02         
        elif canvas.IsKeyPressed('D'):
            self.right_state = -0.02

        if self.forward_state == self.right_state and self.forward_state > 0 and self.right_state > 0:
            self.forward_state = 0.015
            self.right_state = 0.015
        elif self.forward_state == self.right_state and self.forward_state < 0 and self.right_state < 0:
            self.forward_state = -0.015
            self.right_state = -0.015
        elif self.forward_state == -self.right_state and self.forward_state > 0 and self.right_state < 0:
            self.forward_state = 0.015
            self.right_state = -0.015
        elif -self.forward_state == self.right_state and self.forward_state < 0 and self.right_state > 0:
            self.forward_state = -0.015
            self.right_state = 0.015

        self.moveCammera(self.forward_state, self.right_state)

        if event and event.type == EventTypes.MOUSE_MOTION:
            if button_map[glfw.MOUSE_BUTTON_2] in event.data["buttons"]:
                x = np.floor(event.data["x"] - self.mouse_noop_x)
                y = np.floor(event.data["y"] - self.mouse_noop_y) 

                if np.abs(x) > np.abs(y):
                    x =  np.sign(x) * sensitivity 
                    self.spinCammera(-x, 0)
                else:
                    y = np.sign(y) * sensitivity
                    self.spinCammera(0, -y)            

                self.mouse_noop_x = np.floor(event.data['x']) 
                self.mouse_noop_y = np.floor(event.data['y'])

            else:
                self.mouse_noop_x = np.floor(event.data['x']) 
                self.mouse_noop_y = np.floor(event.data['y'])

        self.cammeraUpdate()