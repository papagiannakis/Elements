Introduction
========================

This is the core package of the Elements project. The ECSS library contains the base classes to develop an ECS application based on a scenegraph.

Below you can find a brief explanation of the core classes in this package:

Entity
-----------
The Entity class is the building block of our ECS system. You will see that the class contains basic functions to add or remove entities from our playground.


Component
-----------
The Component class contains the data for our systems to run. Each Component is attached to an entity containing the data to define a specific behavior.

An important method in this class is the accept(). This method should be implemented from all the components as it is the method that will be called from a 
corresponding system when traversing the scenegraph. 

System
------------
Systems are the behaviors of the ECS architecture. They traverse the scenegraph and apply the desired behavior.

We propose to study the examples in order to identify the differences of each of the above classes.


ECSSManager
-------------
This class contains the singleton of our app with the main references and basic functions. This means that you will use this singleton to get the reference of the scene and to access the lists holding the entities components and systems.

It also implements basic functionalities like the creations or deletion of entities, components and systems.

Event
------------

Event manager for our ECSS package. You can use it to trigger events from various scripts. This methodology is widely used in game development.

Utilities
------------

implements helper functions that make our life easier. This is a collection of methods (mathematics, calculations etc) that are used through our apps so we collected them into one place.

You can read more about the ECS architecture in the manual section.