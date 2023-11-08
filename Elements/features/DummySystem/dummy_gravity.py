
from Elements.pyECSS.Component import Component, BasicTransform, RenderMesh
from Elements.pyECSS.System import System
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.Scene import Scene

class RigidBody(Component):
    gravity = 10

    def __init__(self, name=None, type=None, id=None):

        super().__init__(name, type, id)
        
        self.mass = 100
        self.drag = 5

    def show(self):
        if (isinstance(self.parent,Entity)) == False:
            print('This is a gravity component. Gravity: ' + str(self.gravity) + ', Drag: ' + str(self.drag) + ', Mass: ' + str(self.mass))
        else:
            print('This is a gravity component, attached to entity'  + self.parent.name + '. Gravity: ' + str(self.gravity) + ', Drag: ' + str(self.drag) + ', Mass: ' + str(self.mass) )
        # print("----------------------------")


    #We have to override update() but there is no implementation in this example
    def update(self, **kwargs):
        pass
    
    #The accept method is important to call the applyGravity()
    def accept(self, system: System):
        system.applyGravity(self)

    #We have to override init() but there is no implementation in this example
    def init(self):
        pass

class GravitySystem(System):
    
    def __init__(self, name=None, type=None, id=None):
        super().__init__(name, type, id)
        
    def applyGravity(self, component: RigidBody):
        
        #check if the visitor visits a node that it should not
        if (isinstance(component,RigidBody)) == False:
            print("Error: The visitor visits a node ", component.name,  " that it should not")
            return #in Python due to duck typing we need to check this!
        
        component.mass = 0

        print('Visited:', component.parent.name, '. New mass is: ', str(component.mass))


if __name__ == "__main__":
    #We create an Entity and a new component
    # gameObject = Entity("root")
    scene = Scene()
    rootEntity = scene.world.createEntity(Entity(name="RooT"))
    entity1 = scene.world.createEntity(Entity(name="Entity1"))
    scene.world.addEntityChild(rootEntity, entity1)
    rigid1 = scene.world.addComponent(entity1, RigidBody("gravity", "RigidBody", "1"))

    entity2 = scene.world.createEntity(Entity(name="Entity2"))
    scene.world.addEntityChild(rootEntity, entity2)
    rigid2 = scene.world.addComponent(entity2, RigidBody("gravity", "RigidBody", "2"))
    rigid_transform2 = scene.world.addComponent(entity2, BasicTransform())
    rigid_transform2 = scene.world.addComponent(entity2, RenderMesh())

    # scene.world.print()
    gravity = scene.world.createSystem(GravitySystem())

    print("="*20)
    print("Rigidbody init values")
    print("="*20)

    rigid1.show()
    rigid2.show()

    print("="*20)
    print("Running gravity system")
    print("="*20)
    scene.world.traverse_visit(gravity, scene.world.root)
    
    print("="*20)
    print("Rigidbody updated value")
    print("="*20)

    rigid1.show()
    rigid2.show()

