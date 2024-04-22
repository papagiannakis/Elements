from typing import List, Tuple
from dataclasses import dataclass
import numpy as np
import math
import munch 
import glm
from numpy.typing import NDArray
from Elements.pyECSS.Component import Component
from Elements.pyECSS.Component import BasicTransform
import Elements.pyECSS.math_utilities as util

from imgui_bundle import imgui, imguizmo, ImVec2 # type: ignore

Matrix16 = NDArray[np.float64]
Matrix6 = NDArray[np.float64]
Matrix3 = NDArray[np.float64]

lastUsing = 0


# Camera projection
isPerspective = True
fov = 60.0
viewWidth = 10.0  # for orthographic
camYAngle = 165.0 / 180.0 * 3.14159
camXAngle = 32.0 / 180.0 * 3.14159

objectMatrix = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ], np.float32)

idMatrix =  np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ], np.float32)

firstFrame = True


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
        self._projection = None;  

    def setView(self, _view):
        self._view = _view;
        
    def __del__(self):
        pass
    
    def drawTransformGizmo(self, comp):  
        global cameraView, objectMatrix
        trs_changed = False;

        if comp is not None and isinstance(comp, BasicTransform):
            pos = np.array(glm.transpose(comp.trs), np.float32) @ idMatrix
            tmp = pos[3][0];
            pos[3][0] = pos[3][2];
            pos[3][2] = tmp;

            manip_result = self.gizmo.manipulate(
                self._view,
                self._projection,
                self.currentGizmoOperation,
                self.statics.mCurrentGizmoMode,
                # pos
                objectMatrix
            )

            if manip_result:
                # objectMatrix = np.array(glm.transpose(manip_result.value), np.float32);
                # print(np.array(glm.transpose(comp.trs), np.float32))
                objectMatrix = manip_result.value;
                trs_changed = True
            
        return trs_changed, objectMatrix;

    def drawCameraGizmo(self):
        global firstFrame
        changed = False;

        self.gizmo.set_rect(
            imgui.get_window_pos().x,
            imgui.get_window_pos().y,
            imgui.get_window_width(),
            imgui.get_window_height(),
        )

        self.gizmo.set_drawlist()

        if firstFrame:
            firstFrame = False;
            self._projection = util.perspective(25, 1200/800, 0.01, 100.0); 

        viewManipulateRight = imgui.get_window_pos().x + imgui.get_window_width();
        viewManipulateTop = imgui.get_window_pos().y
        

        view_manip_result = self.gizmo.view_manipulate(
            self._view,
            50.0,
            ImVec2(viewManipulateRight - 128, viewManipulateTop),
            ImVec2(128, 128),
            0x10101010,
        )

        if view_manip_result:
            changed = True
            cameraView = view_manip_result.value
            self._view = np.array(cameraView, np.float32);

        return changed;

    def decompose_look_at(self):
        r = self._view[:3,:3]
        target = self._view[:3,3]
        eye = target + r[:,2];
        direction = -((target - eye) / np.linalg.norm(target - eye));
        eye = target + direction;
        up = r[:,1]
        
        eye[:] *= 4;

        return eye, up, target;

            
        
        
        
