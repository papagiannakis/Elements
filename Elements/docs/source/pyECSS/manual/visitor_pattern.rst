Visitor pattern
=================

The basics
------------------------------
The Visitor pattern is a design pattern in object-oriented programming that allows you to add new operations to a set of related
objects without modifying the objects themselves. It is used when you have a complex object structure that you want to perform
various operations on, and you don't want to modify the existing code for these operations.

The Visitor pattern works by defining a separate visitor object that knows how to traverse the object structure
and perform the desired operations. The object structure itself is made up of a hierarchy of related classes,
each of which implements an accept() method that accepts a visitor object as an argument.

.. note::
   In our case, the visitor pattern is implemented into Systems.

For more information on the visitor pattern check `here <https://refactoring.guru/design-patterns/visitor>`_
Read more about game programming patterns `here <https://gameprogrammingpatterns.com/contents.html>`_

Implementation in pyECSS
------------------------------

In pyECSS we implemented the visitor pattern to traverse and apply functionality on the components using Systems.

Lets demonstrate the pattern with the TransformSystem as an example. This is a basic system that calculates the position of an object to the scene.

First, we need to create an Entity.

.. code-block:: python
    
    #Create a Cube Entity in the scene
    myCube = scene.world.createEntity(Entity("Cube"));

Next we will create the BasicTransform component. You can find the complete implementation of this component into the Component.py script 
but for now we will only focus into one method, the accept.

.. code-block:: python

    class BasicTransform(Component):

        #...

        def accept(self, system: pyECSS.System, event = None):
            system.apply2BasicTransform(self) #from TransformSystem

The BasicTransform component overrides accept method from its parent and makes the system that traverses the node to call the apply2BasicTransform
method. We will use this method later.

Lets add the component to our Entity

.. code-block:: python

    #Create a Transform component
    transformComponent = BasicTransform(name="trans", trs=util.identity());    

    #Attach it on the Cube
    scene.world.addComponent(myCube, transformComponent);


Now we can create the TransformSystem

.. code-block:: python

    class TransformSystem(System):

    #...

    def apply2BasicTransform(self, basicTransform: pyECSS.Component.BasicTransform):

    #check if the visitor visits a node that it should not
    if (isinstance(basicTransform,pyECSS.Component.BasicTransform)) == False:
        return #in Python due to duck typing we need to check this!
        
    # getLocal2World returns result to be set in BasicTransform::update(**kwargs) below
    l2worldTRS = self.getLocal2World(basicTransform)
    #update l2world of basicTransform
    basicTransform.update(l2world=l2worldTRS) 


As you see the code above calculates the transform of the object

Back to our main function, we can create the system

.. code-block:: python

    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))


Finally, to apply the transform system we add it to the main loop of our apply

.. code-block:: python

    while running:
        scene.world.traverse_visit(transUpdate, scene.world.root)


The code above will traverse all the Entities of our scene and apply the TransformSystem where applicable. This means that the transform
functionality will only be applied on Entities that have assigned the BasicTransform component.

If we take a peek to the traverse_visit function, we will see that it traverses the Entities and calls the accept method. This triggers
the systems to apply their functions on the Components.

.. code-block:: python

    while(not done_traversing):
        try:
            traversedComp = next(iterator)
        except StopIteration:
            done_traversing = True
        else:
            if (traversedComp is not None):
                traversedComp.accept(system)

