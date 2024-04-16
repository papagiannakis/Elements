from typing import List, Tuple
from dataclasses import dataclass
import numpy as np
import math
import munch 
import glm
from numpy.typing import NDArray
from Elements.pyECSS.Component import Component
from Elements.pyECSS.Component import BasicTransform

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
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
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

    def setView(self, _view):
        self._view = _view;
        
    def __del__(self):
        pass
    
    def drawGizmo(self, comp):  
       # self.setOperation();
        global cameraView, firstFrame, objectMatrix

        if firstFrame:
            firstFrame = False;
            radians = glm.radians(fov)
            cameraProjection = glm.perspective(radians, imgui.get_window_width() / imgui.get_window_height(), 0.1, 100.0)
            self._projection =np.array(cameraProjection)
        
        self.gizmo.set_rect(
            imgui.get_window_pos().x,
            imgui.get_window_pos().y,
            imgui.get_window_width(),
            imgui.get_window_height(),
        )

        self.gizmo.set_drawlist()

        r = EditTransformResult(changed = False, objectMatrix = objectMatrix, cameraView = self._view)
        
        viewManipulateRight = imgui.get_window_pos().x + imgui.get_window_width();
        viewManipulateTop = imgui.get_window_pos().y
        window = imgui.internal.get_current_window()
        if imgui.is_window_hovered() and imgui.is_mouse_hovering_rect(
            window.inner_rect.min, window.inner_rect.max
        ):
            self.statics.gizmoWindowFlags = imgui.WindowFlags_.no_move
        else:
            self.statics.gizmoWindowFlags = 0


        if comp is not None and isinstance(comp, BasicTransform):
            # print(np.array(comp.l2world, np.float32));
            # print(objectMatrix);
            manip_result = self.gizmo.manipulate(
                self._view,
                self._projection,
                self.currentGizmoOperation,
                self.statics.mCurrentGizmoMode,
                objectMatrix
            )

            if manip_result:
                r.changed = True
                r.objectMatrix = manip_result.value
        
        view_manip_result = self.gizmo.view_manipulate(
            self._view,
            50.0,
            ImVec2(viewManipulateRight - 128, viewManipulateTop),
            ImVec2(128, 128),
            0x10101010,
        )

        if view_manip_result:
            r.changed = True
            r.cameraView = view_manip_result.value

        if r.changed:
            objectMatrix = r.objectMatrix
            self._view = np.array(r.cameraView, np.float32);

        return r.changed;

    def decompose_look_at(self):
        r = self._view[:3,:3]
        target = self._view[:3,3]
        eye = target + r[:,2];
        direction = -((target - eye) / np.linalg.norm(target - eye));
        eye = target + direction;
        up = r[:,1]
        
        eye[:] *= 4;

        return eye, up, target;

            
        
        
        
