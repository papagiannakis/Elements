from typing import List, Tuple
from dataclasses import dataclass
import numpy as np
import math
import munch 
import glm
from numpy.typing import NDArray

from imgui_bundle import imgui, imguizmo, ImVec2

Matrix16 = NDArray[np.float64]
Matrix6 = NDArray[np.float64]
Matrix3 = NDArray[np.float64]

class EditTransformResult:
    changed: bool
    objectMatrix: Matrix16
    cameraView: Matrix16
    
class Guizmos:
    def __init__(self, imguiContext = None):
        self.gizmo = imguizmo.im_guizmo
        
        if imguiContext is None:
            print("ImGuizmo: You didn't provide an imgui context");
            exit(1);
        
        self.gizmo.set_im_gui_context(imguiContext);
        self.camDistance = 8.0
        self.mCurrentGizmoOperation = self.gizmo.OPERATION.translate

    
    def __del__(self):
        pass
    
    def drawGizmo(self, posX, posY, width, height):        
        self.gizmo.set_rect(
            posX,
            posY,
            width,
            height,
        )
        
        
        
        
