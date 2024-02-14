import numpy as np

# from Elements.pyECSS.Component import *
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Component import BasicTransform



class AnimationTransform(BasicTransform):
    """
    An animation Component, storying animation data
    """
    
    def __init__(self, name=None, type=None, id=None, trs = None, next_vec = None, method = "bezier"):
        super().__init__(name, type, id, trs )    
        self._current_frame = 0
        self._total_frames = 100
        self.current_frame_trs = self.trs
        self._first_vec = trs.copy()[:3,3]
        self._method = method
        print(trs[:3,3])

        if next_vec is None:
            self._next_vec = np.array([1.0, 1.0, 1.0])
        elif isinstance(next_vec, list):
            self._next_vec = np.array(next_vec)
        elif isinstance(next_vec, np.ndarray)  and np.shape(next_vec)==np.shape(np.array([0.0, 0.0, 0.0])):
            self._next_vec = next_vec
        
        self.direction_vector = self._next_vec - self._first_vec
        self.perp_vector1 = np.array([-self.direction_vector[1],self.direction_vector[0], 0])
        self.middle_vector = (self._first_vec+self._next_vec)/2 + self.perp_vector1

    @property
    def method(self):
        return self._method
    
    @method.setter
    def method(self,value):
        self._method = value

    @property
    def first_vec(self):
        return self._first_vec
    
    @first_vec.setter
    def first_vec(self, value):
        self._first_vec[0] = value [0]
        self._first_vec[1] = value [1]
        self._first_vec[2] = value [2]
    
    def Lerp(self, alpha):
        return (1-alpha)*self._first_vec + alpha*self._next_vec
    
    def bezier(self, alpha):
        return (1-alpha)**2*self._first_vec + alpha**2*self._next_vec + 2*(1-alpha)*alpha*self.middle_vector
    
    def apply_alpha(self, alpha):
        # self._vec =  self.Lerp(alpha)
        if self._method == 'bezier':
            self.current_frame_trs[:3,3] =  self.bezier(alpha)
        else:
            self.current_frame_trs[:3,3] =  self.Lerp(alpha)
        
    
    def eval_current_frame(self):
        self._current_frame = self._current_frame % self._total_frames
        self.apply_alpha(self._current_frame/self._total_frames)
    
    def update_frame(self, frame_step):
        self._current_frame += frame_step
        self.trs = self.current_frame_trs
        # print(self._current_frame)
        # if self._current_frame<100:
        self.eval_current_frame()
        # else:
        #     self._current_frame=100
    def __str__(self):
        np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)}) # print only one 3 decimals
        return f"\n {self.getClassName()} name: {self._name}, type: {self._type}, id: {self._id}, parent: {self._parent._name}"
    
    def drawSelfGui(self, imgui):
        imgui.text("WHAT WHAT WHAT")
  
          
if __name__ == "__main__":
    
    a = AnimationTransform(name="NAME", type="Anim", id="1086",trs=util.identity(),next_vec=[6,4,-3], method = 'a')
    print(a.trs)
    # print(a.current_frame_trs)
    a.update_frame(1)
    print(a.trs)
    # print(a.current_frame_trs)
    a.update_frame(1)
    print(a.trs)
    # print(a.current_frame_trs)
    # a.update_frame(10)
    # print(a.trs)
    # print(a.current_frame_trs)
    # a.update_frame(10)
    # print(a.trs)
    # print(a.current_frame_trs)
    # print(a._current_frame)
    # print(a._vec)
    # print(a.trs)
    # for i in range(20):
    #     print('='*10)
    #     a.update_frame(10)
    #     print(a.trs)
    
    # print (3.4 % 1.0)
    # print (-2.7 % 1.0)
    # b = GATransformSystem()
    # a.accept(b)
    print(a.method)
    # print(a.trs)
    
    a.method = 'b'
    print(a.method)
    
