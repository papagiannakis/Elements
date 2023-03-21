Create a component
==================

In this tutorial we will use the entity we created :ref:`here <TutorialEntity>` and attach a new component reflecting rigidbody functionalities, holding
data of the object's mass and drag.

Lets create first our rigidbody component

.. code-block:: python

    class RigidBody(Component):
    gravity = 10

    def __init__(self, name=None, type=None, id=None):

        super().__init__(name, type, id)
        
        self.mass = 100
        self.drag = 5

    def show(self):
        print('This is the gravity component. Gravity: ' + str(self.gravity) + ' Drag: ' + str(self.drag) + ' Mass: ' + str(self.mass))

    def update(self, **kwargs):
        pass
        
    def accept(self, system: System, event = None):
        system.applyGravityEffect(self)
    
    def init(self):
        pass

This is a simple component holding the physical properties of our object.

Pay attention to the following points:

#. We inherit the Component class.
#. The class implements the :code:`update()` :code:`accept()` and :code:`init()` abstract methods. This is mandatory.
#. We added mass, drag and gravity (static var) as the main data of our component.
#. We implemented the :code:`show()` me method to print the data (this is optional of course).
#. The :code:`accept()` method calls the :code:`system.applyGravityEffect(self)`. This means that when the GravitySystem visits this component it will apply the gravity effect. We will mention this in the next tutorial.


The following code creates a RigidBody component. Then we call the :code:`show()` method just to see that our component works properly.

.. code-block:: python

    rigidBody = RigidBody("gravity", "RigidBody", "1")
    rigidBody.show()


The final step is to attach the component to our object.

.. code-block:: python

    gameObject.add(rigidBody)
