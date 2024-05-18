# THIS IS JUST A COPIED EXAMPLE FROM THE BUNDLE DOCUMENTATION, JUST TO BE STUDIED
# Demo ImGuizmo (only the 3D gizmo)
# See equivalent python program: demos_cpp/demos_imguizmo/demo_guizmo_stl.main.cpp
from typing import List, Tuple
from dataclasses import dataclass
import numpy as np
import math
import munch  # type: ignore
from numpy.typing import NDArray

from imgui_bundle import imgui, imguizmo, ImVec2, immapp
from imgui_bundle.demos_python.demo_utils.api_demos import GuiFunction

try:
    import glm  # pip install PyGLM
except ModuleNotFoundError:
    print(
        "\nThis demo require PyGLM, please install it with this command:\n\n\tpip install PyGLM\n"
    )
    exit(1)


Matrix16 = NDArray[np.float64]
Matrix6 = NDArray[np.float64]
Matrix3 = NDArray[np.float64]


gizmo = imguizmo.im_guizmo
statics = None;

useWindow = True
gizmoCount = 1
camDistance = 8.0
mCurrentGizmoOperation = gizmo.OPERATION.translate

# fmt: off
gObjectMatrix: List[Matrix6] = [
    np.array([
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    ], np.float32),
    np.array([
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        2.0, 0.0, 0.0, 1.0
    ], np.float32),
    np.array([
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        2.0, 0.0, 2.0, 1.0
    ], np.float32),
    np.array([
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 2.0, 1.0
    ], np.float32),
]
# fmt: on

identityMatrix = np.eye(4, dtype=np.float32)

# Change from the original version: returns a tuple (changed, newCameraView)
@dataclass
class EditTransformResult:
    changed: bool
    objectMatrix: Matrix16
    cameraView: Matrix16


def EditTransform(
    cameraView: Matrix16,
    cameraProjection: Matrix16,
    objectMatrix: Matrix16,
    editTransformDecomposition: bool,
) -> EditTransformResult:
    global mCurrentGizmoOperation
    global statics
    
    if statics is None:
        statics = munch.Munch()
        statics.mCurrentGizmoMode = gizmo.MODE.local
        statics.useSnap = False
        statics.snap = np.array([1.0, 1.0, 1.0], np.float32)
        statics.bounds = np.array([-0.5, -0.5, -0.5, 0.5, 0.5, 0.5], np.float32)
        statics.boundsSnap = np.array([0.1, 0.1, 0.1], np.float32)
        statics.boundSizing = False
        statics.boundSizingSnap = False
        statics.gizmoWindowFlags = 0

    r = EditTransformResult(
        changed=False, objectMatrix=objectMatrix, cameraView=cameraView
    )

    if editTransformDecomposition:
        if imgui.is_key_pressed(imgui.Key.t):
            mCurrentGizmoOperation = gizmo.OPERATION.translate
        if imgui.is_key_pressed(imgui.Key.e):
            mCurrentGizmoOperation = gizmo.OPERATION.rotate
        if imgui.is_key_pressed(imgui.Key.s):
            mCurrentGizmoOperation = gizmo.OPERATION.scale
        if imgui.radio_button(
            "Translate", mCurrentGizmoOperation == gizmo.OPERATION.translate
        ):
            mCurrentGizmoOperation = gizmo.OPERATION.translate
        imgui.same_line()
        if imgui.radio_button(
            "Rotate", mCurrentGizmoOperation == gizmo.OPERATION.rotate
        ):
            mCurrentGizmoOperation = gizmo.OPERATION.rotate
        imgui.same_line()
        if imgui.radio_button("Scale", mCurrentGizmoOperation == gizmo.OPERATION.scale):
            mCurrentGizmoOperation = gizmo.OPERATION.scale


        matrixComponents = gizmo.decompose_matrix_to_components(objectMatrix)
        edited = False
        
        edit_one , value = imgui.drag_float3("Translation", matrixComponents.translation, 0.01, -30, 30, "%.001f", 1);
        if edit_one:
            matrix3 = np.array(value, np.float32)
            matrixComponents.translation = matrix3
        edited |= edit_one
        
        edit_one , value = imgui.drag_float3("Rotation", matrixComponents.rotation, 0.01, -30, 30, "%.001f", 1);
        if edit_one:
            matrix3 = np.array(value, np.float32)
            matrixComponents.rotation = matrix3
        edited |= edit_one
        
        edit_one , value = imgui.drag_float3("Scale", matrixComponents.scale, 0.01, -30, 30, "%.001f", 1);
        if edit_one:
            matrix3 = np.array(value, np.float32)
            matrixComponents.scale = matrix3
        edited |= edit_one


        if edited:
            r.changed = True
            r.objectMatrix = gizmo.recompose_matrix_from_components(matrixComponents)


    io = imgui.get_io()
    viewManipulateRight = io.display_size.x
    viewManipulateTop = 0.0

    imgui.set_next_window_size(ImVec2(800, 400), imgui.Cond_.appearing.value)
    imgui.set_next_window_pos(ImVec2(400, 20), imgui.Cond_.appearing.value)

    imgui.begin("Gizmo")
    gizmo.set_drawlist()
    
    windowWidth = imgui.get_window_width()
    windowHeight = imgui.get_window_height()
    gizmo.set_rect(
        imgui.get_window_pos().x,
        imgui.get_window_pos().y,
        windowWidth,
        windowHeight,
    )
    viewManipulateRight = imgui.get_window_pos().x + windowWidth
    viewManipulateTop = imgui.get_window_pos().y
    window = imgui.internal.get_current_window()
    if imgui.is_window_hovered() and imgui.is_mouse_hovering_rect(
        window.inner_rect.min, window.inner_rect.max
    ):
        statics.gizmoWindowFlags = imgui.WindowFlags_.no_move
    else:
        statics.gizmoWindowFlags = 0


    gizmo.draw_cubes(cameraView, cameraProjection, gObjectMatrix[:gizmoCount])

    manip_result = gizmo.manipulate(
        cameraView,
        cameraProjection,
        mCurrentGizmoOperation,
        statics.mCurrentGizmoMode,
        objectMatrix
    )
    if manip_result:
        r.changed = True
        r.objectMatrix = manip_result.value

    view_manip_result = gizmo.view_manipulate(
        cameraView,
        camDistance,
        ImVec2(viewManipulateRight - 128, viewManipulateTop),
        ImVec2(128, 128),
        0x10101010,
    )
    if view_manip_result:
        r.changed = True
        r.cameraView = view_manip_result.value

    imgui.end()


    return r

# This returns a closure function that will later be invoked to run the app
def make_closure_demo_guizmo() -> GuiFunction:
    lastUsing = 0
    cameraView = np.array(
        [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    )

    cameraProjection = np.zeros((4, 4), np.float32)  # remove me?

    # Camera projection
    isPerspective = True
    fov = 27.0
    viewWidth = 10.0  # for orthographic
    camYAngle = 165.0 / 180.0 * 3.14159
    camXAngle = 32.0 / 180.0 * 3.14159

    firstFrame = True

    def gui():
        global useWindow, camDistance, gizmoCount, mCurrentGizmoOperation
        nonlocal lastUsing, cameraView, cameraProjection, isPerspective, fov, viewWidth, camYAngle, camXAngle, firstFrame

        io = imgui.get_io()
        if isPerspective:
            radians = glm.radians(fov)  # The gui is in degree, we need radians for glm
            cameraProjection = glm.perspective(radians, io.display_size.x / io.display_size.y, 0.1, 100.0)  # type: ignore
            cameraProjection = np.array(cameraProjection)
        else:
            viewHeight = viewWidth * io.display_size.y / io.display_size.x
            cameraProjection = glm.ortho(-viewWidth, viewWidth, -viewHeight, viewHeight, 1000.0, -1000.0)  # type: ignore
            cameraProjection = np.array(cameraProjection)

        gizmo.set_orthographic(not isPerspective)
        gizmo.begin_frame()

        imgui.set_next_window_pos(ImVec2(1024, 100), imgui.Cond_.appearing)
        imgui.set_next_window_size(ImVec2(256, 256), imgui.Cond_.appearing)

        # create a window and insert the inspector
        imgui.set_next_window_pos(ImVec2(10, 10), imgui.Cond_.appearing)
        imgui.set_next_window_size(ImVec2(320, 340), imgui.Cond_.appearing)
        imgui.begin("Editor")

        _, camDistance = imgui.drag_float("Distance:", camDistance, 0.1, 1.0, 10.0, "%.3f");

        if firstFrame:
            print(cameraProjection)
            eye = glm.vec3(
                math.cos(camYAngle) * math.cos(camXAngle) * camDistance,
                math.sin(camXAngle) * camDistance,
                math.sin(camYAngle) * math.cos(camXAngle) * camDistance,
            )
            at = glm.vec3(0.0, 0.0, 0.0)
            up = glm.vec3(0.0, 1.0, 0.0)
            cameraView = glm.lookAt(eye, at, up)  # type: ignore
            cameraView = np.array(cameraView)
            firstFrame = False


        gizmo.set_id(0)

        result = EditTransform(cameraView, cameraProjection, gObjectMatrix[0], lastUsing == 0)  # type: ignore
        
        if result.changed:
            print(cameraProjection)
            gObjectMatrix[0] = result.objectMatrix

            cameraView = result.cameraView
        if gizmo.is_using():
            lastUsing = 0

        imgui.end()

    return gui

def main():
    gui = make_closure_demo_guizmo()

    immapp.run(
    gui_function=gui,
    window_title="Example Guizmos",
    window_size_auto=True
    )

if __name__ == "__main__":
    main()
