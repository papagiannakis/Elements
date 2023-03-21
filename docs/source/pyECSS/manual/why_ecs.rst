Why ECS?
============

The basics
------------------------------
An Entity-Component-System (ECS) is a software architecture pattern used in game development, but can also be applied to other domains.
It is a way to organize the logic and data of a game or simulation by separating entities into individual components,
and then using systems to process those components.

Entity
------------------------------
An entity is a basic object in a game or simulation that represents a specific object or concept in the system.
It is essentially a container that holds a collection of components, which are the building blocks of the entity's
functionality and behavior.

An entity in an ECS is usually defined by a unique identifier or a name, and it can represent any object or concept in the game
or simulation. For example, an entity in a game might represent a player character, a non-playable character, an item, a weapon,
or any other object in the game.

Entities in an ECS **are typically not given any behavior or logic of their own.**
Instead, they are composed of a collection of components, which define the entity's behavior and functionality.
By separating the behavior and functionality of an entity into individual components, **the ECS architecture allows for greater
flexibility** in designing and modifying game objects and behaviors.

Code showing the creation of two entities

.. code-block:: python
    
    gameObject = Entity("root") 
    gameObject2 = Entity("gameObject2", "Group", 10)

    #OR you can add them directly to your scene
    myObject = scene.world.createEntity(Entity("Object"));

Component
------------------------------
A component is a modular piece of data that represents a specific aspect of an entity's behavior or appearance.
Components in an ECS are designed to be self-contained, reusable, and interchangeable, allowing for greater flexibility
in designing and modifying game objects and behaviors.

In general components contain **only the data** necessary to represent a single aspect of an entity's behavior or appearance.
For example, a physics component might contain information about an entity's position, velocity, and acceleration,
while a graphics component might contain information about an entity's visual appearance, such as its sprite or texture.

Code to add components into entities

.. code-block:: python
    
    transformComponent = BasicTransform(name="trans", trs=util.identity());    
    scene.world.addComponent(myObject, transformComponent);

The basic transform component. It holds data regarding the translation, rotation and scale matrix. The accept method is called from the
systems when they visit BasicTransform component. It defines what each system will perform upon visiting the component.

.. code-block:: python
    
    class BasicTransform(Component):
    def trs(self):
        """ Get Component's transform: translation, rotation ,scale """
        return self._trs
    @trs.setter

    def accept(self, system: pyECSS.System, event = None):
        system.apply2BasicTransform(self) #from TransformSystem
        system.applyCamera2BasicTransform(self) #from CameraSystem


System
------------------------------
Systems are responsible for **processing and updating the data** contained in the components of one or more entities in order
to simulate the behavior of the game or simulation. A system in an ECS is designed to be modular, self-contained, 
and focused on a specific aspect of the game or simulation. Systems are designed to perform specific tasks such as physics simulation, input handling, or artificial intelligence.

For example, a physics system might operate on all entities that have position and velocity components, and update their positions
based on their velocities. A rendering system might operate on all entities that have graphics components, and draw them on the screen.

The code below initiates a new TransformSystem System to visit all scenegraph components.

.. code-block:: python
        transUpdate = TransformSystem("transUpdate", "TransformSystem", "001")
        trans5.accept(transUpdate)

        class TransformSystem(System):


This is a simple Transform system that calculates the TRS matrix when visits a transform component. The method apply2BasicTransform
is applied upon visiting the component.

.. code-block:: python

    class TransformSystem(System):

        def apply2BasicTransform(self, basicTransform: pyECSS.Component.BasicTransform):

            #check if the visitor visits a node that it should not
            if (isinstance(basicTransform,pyECSS.Component.BasicTransform)) == False:
                return #in Python due to duck typing we need to check this!
        
            # getLocal2World returns result to be set in BasicTransform::update(**kwargs) below
            l2worldTRS = self.getLocal2World(basicTransform)
            #update l2world of basicTransform
            basicTransform.update(l2world=l2worldTRS) 
