import math
import Elements.pyECSS.math_utilities as utilities
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Component
from Elements.pyECSS.System import System

#-------Tool Action--------------
class ToolCollider(Component):
    currentCollisions = 0
    collisionsToPerform = 1

    def __init__(self, name=None, type=None, collisions = 1):

        super().__init__(name, type,None)
        self.collisionsToPerform = collisions

    def show(self):
        print("currentCollisions: " + str(self.currentCollisions) + ", collisionsToPerform: " + str(self.collisionsToPerform))


    #We have to override update() but there is no implementation in this example
    def update(self, **kwargs):
        pass

    #The accept method is important to call the applyGravityEffect()
    def accept(self, system: System):
        system.applyCollision(self)

    #We have to override init() but there is no implementation in this example
    def init(self):
        pass

class ToolAction(System):

    def __init__(self, name=None, type=None, id=None):
        super().__init__(name, type, id)

    def applyCollision(self, toolCollider: ToolCollider):

        #check if the visitor visits a node that it should not
        if (isinstance(toolCollider,ToolCollider)) == False:
            return #in Python due to duck typing we need to check this!
        toolCollider.currentCollisions+=1

        toolCollider.show()

        if(toolCollider.currentCollisions >= toolCollider.collisionsToPerform):
            print("Collider: " + toolCollider.name + " PERFORMED")

#--------Insert Action----------

class InsertCollider(Component):

    def __init__(self, name=None, type=None, _insertAngle = 1, _interactableObject = None):

        super().__init__(name, type,None)
        self.insertAngle = _insertAngle
        self.currentAngle = 0
        self.interactableObject = _interactableObject

    def setInsertAngle(self, newInsertAngle):
        self.insertAngle = newInsertAngle

    def setCurrentAngle(self, newCurrentAngle):
        self.currentAngle = newCurrentAngle

    #We have to override update() but there is no implementation in this example
    def update(self, **kwargs):
        pass

    def accept(self, system: System):
        if (isinstance(system, InsertAction)):
            system.applyInsertion(self)


    #We have to override init() but there is no implementation in this example
    def init(self):
        pass

class InsertAction(System):

    def __init__(self, name=None, type=None, id=None, OnPerform = None):
        self.actionPerfomed = False
        self.OnPerform = OnPerform
        super().__init__(name, type, id)

    def applyInsertion(self, insertCollider: InsertCollider):

        if(self.actionPerfomed == True):
            return
        
        if (isinstance(insertCollider,InsertCollider)) == False:
            return 

        distanceOK = False
        angleOK = True

        if(CalculateTransformDistance(insertCollider.interactableObject,insertCollider.parent)<0.3):
            distanceOK = True
        else:
            distanceOK = False
              
        if(distanceOK and angleOK):
            self.actionPerfomed = True

            #Invoke the perform function
            if(self.OnPerform is not None):
                self.OnPerform()
            print("INSERT ACTION PERFORMED")
            

#--------Remove Action----------

class RemoveComponent(Component):

    def __init__(self, name=None, type=None, _removeDistance = 1):

        super().__init__(name, type,None)
        self.removeDistance = _removeDistance
        self.removableObject = None


    #We have to override update() but there is no implementation in this example
    def update(self, **kwargs):
        pass

    def accept(self, system: System):
        if (isinstance(system, RemoveAction)):
            system.applyRemoval(self)


    #We have to override init() but there is no implementation in this example
    def init(self):
        pass

class RemoveAction(System):

    def __init__(self, name=None, type=None, id=None,OnPerform = None):
        self.actionPerfomed = False
        self.actionInitialized = False
        self.OnPerform = OnPerform
        super().__init__(name, type, id)
    
    def applyRemoval(self, removeObject: RemoveComponent):

        if(self.actionPerfomed == True):
            return
        
        if (isinstance(removeObject,RemoveComponent)) == False:
            return 

        if(self.actionInitialized is False):
            #Calculate init position
            trs = removeObject.parent.getChildByType(BasicTransform.getClassName()).trs
            pos = [trs[0,3],trs[1,3],trs[2,3]]
            self.initPosition = pos

            self.actionInitialized = True
        
        distanceOK = False

        trs2 = removeObject.parent.getChildByType(BasicTransform.getClassName()).trs
        currentpos = [trs2[0,3],trs2[1,3],trs2[2,3]]
        distance =  math.sqrt((self.initPosition[0]-currentpos[0])**2 + (self.initPosition[1]-currentpos[1])**2 + (self.initPosition[2]-currentpos[2])**2)

        if(distance > 0.3):
            distanceOK = True
        else:
            distanceOK = False

        if(distanceOK):
            self.actionPerfomed = True
            #Invoke the perform function
            if(self.OnPerform is not None):
                self.OnPerform()
            print("REMOVE ACTION PERFORMED")



def CalculateTransformDistance(entity1:Entity, entity2:Entity) -> float:

        trs1 = entity1.getChildByType(BasicTransform.getClassName()).trs
        v1 = [trs1[0,3],trs1[1,3],trs1[2,3]]

        trs2 = entity2.getChildByType(BasicTransform.getClassName()).trs
        v2 = [trs2[0,3],trs2[1,3],trs2[2,3]]

        # Check if the vectors have the same dimensionality
        if len(v1) != 3 or len(v2) != 3:
            raise ValueError("Both input vectors must have three dimensions.")
    
        # Calculate the distance between the two vectors using the distance formula
        d = math.sqrt((v2[0]-v1[0])**2 + (v2[1]-v1[1])**2 + (v2[2]-v1[2])**2)

        return d

#-----------------------------

#-----USAGE-------------

#gameObject = Entity("root")

#collider1 = Entity("collider1")
#collider2 = Entity("collider2")

#----TOOL ACTION------
#toolCollider = ToolCollider("toolCollider", "ToolCollider", 3)
#gameObject.add(toolCollider)
#toolAction = ToolAction("toolAction", "ToolAction", "002")
#toolCollider.accept(toolAction)
#toolCollider.accept(toolAction)
#toolCollider.accept(toolAction)

#------INSERT ACTION------
#gameObject2 = Entity("insertObject")
#insertCollider = InsertCollider("insertCollider", "InsertCollider", 45)
#gameObject2.add(insertCollider)
#insertAction = InsertAction("insertAction", "InsertAction", "003")

#wrong try
#insertCollider.setCurrentAngle(60)
#insertCollider.accept(insertAction)

#correct try
#insertCollider.setCurrentAngle(10)
#insertCollider.accept(insertAction)