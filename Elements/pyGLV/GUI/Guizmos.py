import numpy as np
import glm
from numpy.typing import NDArray
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

def makeMatrixCompatible():
    """
    Manipulates the object matrix to make to compatible with the manipulate function of the gizmo
    """
    global objectMatrix

    tmp = objectMatrix[3][0];
    objectMatrix[3][0] = objectMatrix[3][2];
    objectMatrix[3][2] = tmp;

    tmp = objectMatrix[0][0];
    objectMatrix[0][0] = objectMatrix[2][2];
    objectMatrix[2][2] = tmp;

    tmp = objectMatrix[1][0];
    objectMatrix[1][0] = objectMatrix[1][2];
    objectMatrix[1][2] = tmp;

    tmp = objectMatrix[0][1];
    objectMatrix[0][1] = objectMatrix[2][1];
    objectMatrix[2][1] = tmp;

    tmp = objectMatrix[0][2];
    objectMatrix[0][2] = objectMatrix[2][0];
    objectMatrix[2][0] = tmp;

class Gizmos:
    def __init__(self, imguiContext = None):
        self.gizmo = imguizmo.im_guizmo
        
        if imguiContext is None:
            print("ImGuizmo: You didn't provide an imgui context");
            exit(1);
        
        self.gizmo.set_im_gui_context(imguiContext);
        self.gizmo.allow_axis_flip(False);
        self.currentGizmoOperation = imguizmo.im_guizmo.OPERATION.translate;
        self.currentGizmoMode = self.gizmo.MODE.local;

        self._view = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]], np.float32)
        self._projection = None;  
        self._gizmoView = self._view;
    
        self._cameraSystem = None;
        self._transformEnabled = True;
        self._cameraEnabled = True;

    def setView(self, _view):
        """
        Sets the virw matrix to the given paramter

        :param _view: The new view matrix that is to be given to the gizmo module
        :type _view: NpArray
        """
        self._view = _view;
        if firstFrame:
            self._gizmoView = self._view;
        
    def __del__(self):
        pass


    def drawTransformGizmo(self, comp):  
        """
        Draws the transformation gizmos according to the current operation and the component given as a parameter

        :param comp: The component that the gizmo will be drawn according to. Must be of BasicTransform instance.
        :type comp: Component
        """
        global objectMatrix

        trs_changed = False;

        if self._transformEnabled:
            if comp is not None and isinstance(comp, BasicTransform):
                objectMatrix = [];
                if self._cameraSystem is not None:
                    objectMatrix = np.array(glm.transpose(comp._l2cam), np.float32) @ idMatrix
                else:
                    objectMatrix = np.array(glm.transpose(comp.trs), np.float32) @ idMatrix
                makeMatrixCompatible()

                manip_result = self.gizmo.manipulate(
                    self._gizmoView,
                    self._projection,
                    self.currentGizmoOperation,
                    self.currentGizmoMode,
                    objectMatrix
                )

                if manip_result.edited:
                    objectMatrix = manip_result.value;
                    trs_changed = True

        return trs_changed, objectMatrix;

    def drawCameraGizmo(self):
        """
        Draws the camera gizmo by setting the rectangle for all the gizmos and setting up the drawlist
        """
        global firstFrame
        changed = False;
        self.gizmo.set_orthographic(False);
        
        io = imgui.get_io()

        self.gizmo.set_rect(
            imgui.get_window_pos().x,
            imgui.get_window_pos().y,
            imgui.get_window_width(),
            imgui.get_window_height(),
        )

        self.gizmo.set_drawlist()

        self._projection = util.perspective(25, io.display_size.x / io.display_size.y, 0.01, 100.0); 

        viewManipulateRight = imgui.get_window_pos().x + imgui.get_window_width();
        viewManipulateTop = imgui.get_window_pos().y
        
        if self._cameraEnabled:
            view_manip_result = self.gizmo.view_manipulate(
                self._view,
                10.0,
                ImVec2(viewManipulateRight - 128, viewManipulateTop),
                ImVec2(128, 128),
                0x10101010
            )

            if view_manip_result.edited:
                changed = True
                cameraView = view_manip_result.value
                self._gizmoView = cameraView;
                self._view = np.array(cameraView, np.float32);

        return changed;

    def decompose_look_at(self):
        """
        Decomposes the returned matrix from the camera gizmo to get the eye vector
        """
        r = self._view[:3,:3]
        target = self._view[:3,3] 
        eye = target + r[:,2];
        direction = -((target - eye) / np.linalg.norm(target - eye));
        eye = target + direction;
        up = r[:,1]
        
        eye[:] *= 4;

        return eye;