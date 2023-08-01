import numpy as np

from Elements.pyECSS.Component import *
from Elements.features.GA.dual_quaternion import DualQuaternion
from Elements.features.GA.quaternion import Quaternion
from clifford.g3c import *  # import GA for 3D space
from Elements.features.GA.GAutils import t_q_to_TR, extract_t_q_from_TR
import Elements.pyECSS.math_utilities as util

class GATransform(BasicTransform):
    """A BasicTransform Decorator that wraps the component (BasicTransform) 
        and adds Geometric Algebra layered functionality 

    :param ComponentDecorator: [description]
    :type ComponentDecorator: [type]
    """
    
    def __init__(self,name=None, type=None, id=None, trs=None, q=None, dq=None, vec=None, rot=None):
        """
        The GATransform can be initiated using a translation matrix (trs), 
        or a quaternion (q), or a quaternion (q) and translation vector(vec),
        or a dual quaternion(dq), or a CGA rotor.
        """
        super().__init__(name, type, id)
        self._trs = trs
        self._id = id
        self._q = q
        self._dq = dq
        self._vec = vec
        self._rot = rot
        self._l2world = util.identity()
        self._l2cam = util.identity()
        self._parent = self
        self._children = []
        # print("New component has been initialized")

    def get_trs(self):    
        """ Returns the Component's TRS transformation matrix, depending on the 
         constructor input, without updating current TRS matrix """
        if self._trs is not None:
            TRS = self._trs
        elif  self._q is not None and self._vec is not None:
            buf = self._q.to_transformation_matrix()
            for i in range(3):
                buf[i,3] = self._vec[i]  
            TRS = buf
        elif  self._q is not None:
            TRS = self._q.to_transformation_matrix()
        elif  self._dq is not None:
            q_rot = self._dq.q_rot
            q_dual = self._dq.q_dual
            TRS = DualQuaternion(q_rot, q_dual).to_matrix
        elif self._vec is not None:
            TRS = util.translate(self._vec)  
        elif self._rot is not None:
            t,q = extract_t_q_from_TR(self._rot)
            quat = Quaternion(q[0],q[1],q[2],q[3])
            self._t, self._q = t, quat
            buf = quat.to_transformation_matrix()
            for i in range(3):
                buf[i,3] = t[i]  
            TRS = buf
        else: 
            print("missing input for TRS, defaulting to identity")
            TRS = util.identity()
        # self._trs = TRS
        return TRS
        
    @property #l2world
    def l2world(self):
        """ Get Component's local to world transformation """
        return self._l2world
    @l2world.setter
    def l2world(self, value):
        """ Set Component's local to world transformation """
        self._l2world = value
    
    @property #trs
    def trs(self):
        """ Get Component's transform: translation, rotation ,scale """
        return self._trs
    @trs.setter
    def trs(self, value):
        """ Set Component's transform: translation, rotation ,scale """
        self._trs = value

    def update(self, **kwargs):
        """ Local 2 world transformation calculation
        Traverses upwards whole scenegraph and multiply all transformations along this path
        
        Arguments could be "l2world=" or "trs=" or "l2cam=" to set respective matrices 
        """
        
        # print(self.getClassName(), ": update() called")
        arg1 = "l2world"
        arg2 = "trs"
        arg3 = "l2cam"
        if arg1 in kwargs:
            # print("Setting: ", arg1," with: \n", kwargs[arg1])
            self._l2world = kwargs[arg1]
        if arg2 in kwargs:
            # print("Setting: ", arg2," with: \n", kwargs[arg2])
            self._trs = kwargs[arg2]
        if arg3 in kwargs:
            # print("Setting: ", arg3," with: \n", kwargs[arg3])
            self._l2cam = kwargs[arg3]        


if __name__ == "__main__":
    
    from Elements.features.GA.GA_Component import GATransform
    from Elements.features.GA.GATransformSystem import GATransformSystem

    t = [1,2,3]
    q = [1,2,3,4] # x,y,z,w
    TR = t_q_to_TR(t,q)

    a = GATransform(rot=TR)
    mysystem = GATransformSystem()
    a.accept(mysystem)
    print(a.trs)

    quat = Quaternion(1,2,3,4)
    b = GATransform(q = quat, vec = t)
    b.accept(mysystem)
    print(b.trs)

    

    