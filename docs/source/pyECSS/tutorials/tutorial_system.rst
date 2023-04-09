Create a system
==================

In the previous tutorial, we created a component that holds data regarding the physical properties of an object (mass and drag).

In this tutorial we will implement a system that visits the entity, reads this data and performs various tasks. In particular we will implement
a gravity system that when applied overrides the mass of the object to zero.

Below you can see the GravitySystem we created

.. code-block:: python

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

Pay attention to the following points:

#. We inherit the System class.
#. No need to implement any abstract methods
#. We implemented the method :code:`applyGravityEffect()` that we ll invoke it each time we visit an entity that has a rigidBody component. This is applied from the visitor pattern. This method makes the mass of the body zero and prints an ack message.


Finally, we need to **link the system with the corresponding component**. We are doing this in the :code:`accept()` method of the rigidBody. As you see when the component gets accepted it calls the :code:`applyGravityEffect()` method from the GravitySystem.

.. code-block:: python

    class RigidBody(Component):

    #...
        
    def accept(self, system: System, event = None):
        system.applyGravityEffect(self)
    
    #...

We can test our system with the code below. We create a new GravitySystem and make our rigidBody to accept it.

.. code-block:: python

    gravitySystem = GravitySystem("gravityUpdate", "GravitySystem", "002")
    rigidBody.accept(gravitySystem)

.. note:: 
    
    Usually if our entities are held in another structure (e.g scenegraph) we will have a method that traverses the graph and applies the systems to the nodes. By doing this each node will call the corresponding functions from the systems.