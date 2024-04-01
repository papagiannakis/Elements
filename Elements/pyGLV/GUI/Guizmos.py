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

lastUsing = 0


# Camera projection
isPerspective = True
fov = 27.0
viewWidth = 10.0  # for orthographic
camYAngle = 165.0 / 180.0 * 3.14159
camXAngle = 32.0 / 180.0 * 3.14159

objectMatrix = np.array([
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)

firstFrame = True


@dataclass
class EditTransformResult:
    changed: bool
    objectMatrix: Matrix16
    cameraView: Matrix16
    
class Gizmos:
    def __init__(self, imguiContext = None):
        self.gizmo = imguizmo.im_guizmo
        
        if imguiContext is None:
            print("ImGuizmo: You didn't provide an imgui context");
            exit(1);
        
        self.gizmo.set_im_gui_context(imguiContext);
        self.camDistance = 8.0
        self.currentGizmoOperation = imguizmo.im_guizmo.OPERATION.translate

        self.statics = munch.Munch();
        self.statics.mCurrentGizmoMode = self.gizmo.MODE.local
        self.statics.useSnap = False
        self.statics.snap = np.array([1.0, 1.0, 1.0], np.float32)
        self.statics.bounds = np.array([-0.5, -0.5, -0.5, 0.5, 0.5, 0.5], np.float32)
        self.statics.boundsSnap = np.array([0.1, 0.1, 0.1], np.float32)
        self.statics.boundSizing = False
        self.statics.boundSizingSnap = False
        self.statics.gizmoWindowFlags = 0

        self._view = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]], np.float32)
        self._projection = np.zeros((4, 4), np.float32)
    
    def __del__(self):
        pass
    
    def drawGizmo(self, posX, posY, width, height):  
       # self.setOperation();
        global cameraView

        r = EditTransformResult(changed = False, objectMatrix = objectMatrix, cameraView = self._view)
        
        self.gizmo.set_rect(
            posX,
            posY,
            width,
            height,
        )

        self.gizmo.set_drawlist()
    
        viewManipulateRight = posX + width
        viewManipulateTop = posY
        window = imgui.internal.get_current_window()
        if imgui.is_window_hovered() and imgui.is_mouse_hovering_rect(
            window.inner_rect.min, window.inner_rect.max
        ):
            self.statics.gizmoWindowFlags = imgui.WindowFlags_.no_move
        else:
            self.statics.gizmoWindowFlags = 0

        # manip_result = self.gizmo.manipulate(
        #     cameraView,
        #     cameraProjection,
        #     self.currentGizmoOperation,
        #     self.statics.mCurrentGizmoMode,
        #     objectMatrix,
        #     None,
        #     self.statics.snap if self.statics.useSnap else None,
        #     self.statics.bounds if self.statics.boundSizing else None,
        #     self.statics.boundsSnap if self.statics.boundSizingSnap else None,
        # )

        # if manip_result:
        #     r.changed = True
        #     r.objectMatrix = manip_result.value
        
        view_manip_result = self.gizmo.view_manipulate(
            self._view,
            8.0,
            ImVec2(viewManipulateRight - 128, viewManipulateTop),
            ImVec2(128, 128),
            0x10101010,
        )

        if view_manip_result:
            r.changed = True
            r.cameraView = view_manip_result.value

        if r.changed:
            #gObjectMatrix[0] = result.objectMatrix
            self._view = np.array(r.cameraView, np.float32);

        return r.changed;

    def decompose_view_matrix(self):
            eye = self._view[:3, 3]
            target = eye - self._view[:3, 2];
            up = np.cross(self._view[:3, 0], (-self._view[:3, 2]));

            return eye, up, target;


            
        
        
        
