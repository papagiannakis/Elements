"""
Examples using ECS

This is code examples that create entities, components and systems
    
Elements.pyECSS (Entity Component Systems in a Scenegraph) package
@Copyright 2021-2022 Dr. George Papagiannakis
"""

from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import Component
from Elements.pyECSS.System import System

class RigidBody(Component):
    gravity = 10

    def __init__(self, name=None, type=None, id=None):

        super().__init__(name, type, id)
        
        self.mass = 100
        self.drag = 5

    def show(self):
        print('This is the gravity component. Gravity: ' + str(self.gravity) + ', Drag: ' + str(self.drag) + ', Mass: ' + str(self.mass))
        print("----------------------------")


    #We have to override update() but there is no implementation in this example
    def update(self, **kwargs):
        pass
    
    #The accept method is important to call the applyGravityEffect()
    def accept(self, system: System):
        system.applyGravityEffect(self)

    #We have to override init() but there is no implementation in this example
    def init(self):
        pass

class GravitySystem(System):
    
    def __init__(self, name=None, type=None, id=None):
        super().__init__(name, type, id)
        
    def applyGravityEffect(self, rigidBody: RigidBody):
        
        #check if the visitor visits a node that it should not
        if (isinstance(rigidBody,RigidBody)) == False:
            return #in Python due to duck typing we need to check this!
        print(self.getClassName(), ": applyGravityEffect called")
        
        rigidBody.mass = 0

        print('New mass is: ' + str(rigidBody.mass))


if __name__ == "__main__":
    #We create an Entity and a new component
    gameObject = Entity("root")
    rigidBody = RigidBody("gravity", "RigidBody", "1")

    print("Rigidbody init values")
    rigidBody.show()

    rigidBody.mass = 10
    rigidBody.drag = 2

    print("Rigidbody updated values")
    rigidBody.show()

    #We attach the component to the entity
    gameObject.add(rigidBody)

    #We create a system that manages the rigidbody components
    gravitySystem = GravitySystem("gravityUpdate", "GravitySystem", "002")

    #The component accepts the system
    rigidBody.accept(gravitySystem)

    print("Rigidbody after system application values")
    rigidBody.show()