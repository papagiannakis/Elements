
from Elements.pyECSS.Component import Component
from Elements.pyECSS.System import System
from Elements.pyECSS.Entity import Entity
import Elements.pyECSS.math_utilities as util
import numpy as np

class Rotate(Component):

    def __init__(self, name=None, type=None, id=None, angles = None, speed = None):

        super().__init__(name, type, id)
        if angles is None:
          self._angles = np.array([0,0.1,0])
        else:
          if isinstance(angles, list):
            self._angles = np.array(angles)
          else:
            self._angles = angles

        if speed is None:
          self._speed = 1
        else:
          self._speed = speed

    @property
    def angles (self):
        return self._angles

    @angles.setter
    def angles(self, angles):
        self._angles = angles

    @property
    def speed (self):
        return self._speed

    @speed.setter
    def speed(self, speed):
        self._speed = speed

    def show(self):
        if (isinstance(self.parent,Entity)) == False:
            print('This is a rotation component. Euler Angles: ' + str(self._angles) + ', Speed: ' + str(self._speed) )
        else:
            print('This is a rotation component, attached to entity'  + self.parent.name + ': Euler Angles: ' + str(self._angles) + ', Speed: ' + str(self._speed)  )
        # print("----------------------------")


    #We have to override update() but there is no implementation in this example
    def update(self, **kwargs):
        pass

    #The accept method is important to call the applyRotation2BasicTransform()
    def accept(self, system: System):
        system.applyRotation2BasicTransform(self)

    #We have to override init() but there is no implementation in this example
    def init(self):
        pass

class RotateSystem(System):

    def __init__(self, name=None, type=None, id=None):
        super().__init__(name, type, id)

    def applyRotation2BasicTransform(self, component: Rotate):

        #check if the visitor visits a node that it should not
        if (isinstance(component, Rotate)) == False:
            return #in Python due to duck typing we need to check this!
        print(self.getClassName(), ": applyRotation2BasicTransform is called on component: ", component.name)

        rot = util.eulerAnglesToRotationMatrix(component._speed * component._angles)
        transformComponent = component.parent.getChildByType("BasicTransform")
        transformComponent.trs = rot @ transformComponent.trs
        print("rot", rot)
        print("transformComponent:", transformComponent.name)
        print('Visited:', component.parent.name, ': New trs is: \n', transformComponent.trs)
