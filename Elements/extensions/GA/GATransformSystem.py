import Elements.pyECSS
from Elements.features.GA.GA_Component import GATransform
from Elements.pyECSS.System import System

class GATransformSystem(System):
    """
    System that operates on GATransform Components and calculates Local2World matrices
    that are needed in a Scenegraph DAG hierarchy
    
    :param System: [description]
    :type System: [type]
    :return: [description]
    :rtype: [type]
    """
    
    def __init__(self, name=None, type=None, id=None, cameraComponent=None):
        super().__init__(name, type, id)
        self._camera = cameraComponent #if Scene has a cameraComponent, specify also l2Camera
        
    
    def update(self):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components of an EntityNode. 
        
        """
        pass
    
    def getLocal2World(self, leafComp: Elements.pyECSS.Component, topComp=None):
        """Calculate the l2world BasicTransform matrix

        :param leafComp: [description]
        :type leafComp: Component
        :param topComp: [description], defaults to None
        :type topComp: [type], optional
        :return: the local2world matrix of the visited BasicTransform
        :rtype: numpy.array
        """
        
        # get parent Entity this BasicTransform Component belongs to
        componentEntity = leafComp.parent
        topAccessedEntity = componentEntity

        # l2worldTRS = leafComp.l2world # wrong line
        l2worldTRS = util.identity(); # # correct one   
        
        while(componentEntity is not topComp):
            # get that parent's TRS by type
            parentBasicTrans = componentEntity.getChildByType("BasicTransform")
            if(parentBasicTrans is not None and parentBasicTrans):
                # l2worldTRS = l2worldTRS @ parentBasicTrans.trs # This doesnt work for me (mostly on rot/scale);
                l2worldTRS = parentBasicTrans.trs @ l2worldTRS # This works for me ;

            topAccessedEntity = componentEntity
            componentEntity = componentEntity.parent
        else: #parent is now the root node, so check if it has a Transform component
            parentBasicTrans = topAccessedEntity.getChildByType("BasicTransform")
            if(parentBasicTrans is not None):
                # l2world = multiply current with parent's TRS 
                l2worldTRS = l2worldTRS @ parentBasicTrans.trs
                
        return l2worldTRS
        
    def apply2GATransform(self, gaTransform: Elements.features.GA.GA_Component.GATransform):
        """
        method to be subclassed for  behavioral or logic computation 
        when visits Components. 
        
        In this case calculate the l2w BasicTransform component matrix
        
        """
        
        # check if the visitor visits a node that it should not
        if (isinstance(gaTransform,Elements.features.GA.GA_Component.GATransform)) == False:
            return #in Python due to duck typing we need to check this!
        print(self.getClassName(), ": apply2GATransform called")
        
        gaTransformTRS = gaTransform.get_trs()
        gaTransform.update(trs=gaTransformTRS)
        # print("TRS = \n", gaTransformTRS)
        # # getLocal2World returns result to be set in BasicTransform::update(**kwargs) below
        # l2worldTRS = self.getLocal2World(basicTransform)
        # #update l2world of basicTransform
        # basicTransform.update(l2world=l2worldTRS) 




if __name__=="__main__":
    import numpy as np
    from Elements.features.GA.GA_Component import GATransform
    from Elements.features.GA.quaternion import Quaternion
    # a = GATransform(trs=util.scale(1,2,3))
    a = GATransform(q = Quaternion(0,1,0,1))
    q = Quaternion(0,1,0,1)
    # print(q.to_transformation_matrix())
    # q = Quaternion(0,1,0,1)
    b = GATransformSystem()
    print(a.trs)
    a.accept(b)
    print(a.trs)
    print(a.trs == q.to_transformation_matrix())
    # print (" we want to translate the point (5,3,2) by t = (2,3,14) ")    
    # print( 'translated point: ', a.translate_dual_quaternion(5,3,2,2,3,14) )

    c = GATransform(vec = np.array([1,2,3]))
    print(c.trs)
    c.accept(b)
    print(c.trs)