"""
SimpleCamera utility class
    
Convenience class to assemble an OpenGL camera

"""

from Elements.pyGLV.GL.Scene import Scene # for SimpleCamera
from Elements.pyECSS.Entity import Entity
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Component import BasicTransform, Camera
import imgui

def displayGUI_text(text:str):
    # imgui.set_next_window_size(100.0, 200.0)
    # imgui.new_frame()
    imgui.begin("Information", True)
    imgui.text(text)
    imgui.end()

class SimpleCamera:
    """
    This is a Simple Camera Class, used to store a Camera Entity
    """
    def __init__(self, name=None, type=None, id=None) -> Entity:
        """
        Initializes  a SimpleCamera Entity
        """
        # super().__init__(name, type, id)
        scene = Scene();
        # rootEntity = scene.world.root;

        self.mainCamera = scene.world.createEntity(Entity(name, type, id))
        # scene.world.addEntityChild(rootEntity, SimpleCamera);

        entityCam1 = scene.world.createEntity(Entity(name="entityCam1"));
        scene.world.addEntityChild(self.mainCamera, entityCam1);
        self.mainCamera.trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()));

        entityCam2 = scene.world.createEntity(Entity(name="entityCam2"));
        scene.world.addEntityChild(entityCam1, entityCam2);
        self.mainCamera.trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="trans2", trs=util.identity()));

        self.mainCamera._near = 1;
        self.mainCamera._far = 20;

        self.mainCamera._fov = 50;
        self.mainCamera._aspect = 1.0;

        self.mainCamera._left = -10;
        self.mainCamera._right = 10;
        self.mainCamera._bottom = -10;
        self.mainCamera._top = 10;


        self.mainCamera._mode = "perspective";
        self.mainCamera.camera = scene.world.addComponent(entityCam2, Camera(util.perspective(self.mainCamera._fov, self.mainCamera._aspect, self.mainCamera._near, self.mainCamera._far), "MainCamera", "Camera", "500"));        
      
  
    @property
    def camera(self):
        return self.mainCamera.camera;

    # def drawSelfGui(self, imgui):
    #     """
    #     Describes how the simple camera is drawn in the imgui ECCS Tree
    #     """
    #     if imgui.button("Orthograpic") and self._mode == "perspective":
    #         self._mode = "orthographic";
    #         self._camera.projMat = util.ortho(self._left, self._right, self._bottom, self._top, self._near, self._far);
    #     if imgui.button("Perspective") and self._mode == "orthographic":
    #         self._mode = "perspective";
    #         self._camera.projMat = util.perspective(self._fov, self._aspect, self._near, self._far)

    #     if self._mode == "orthographic":
    #         changed, value = imgui.slider_float("Left", self._left, -50, -1, "%0.1f", 1);
    #         self._left = value;
    #         changed, value = imgui.slider_float("Right", self._right, 1, 50, "%0.1f", 1);
    #         self._right = value;
    #         changed, value = imgui.slider_float("Bottom", self._bottom, -50, -1, "%0.1f", 1);
    #         self._bottom = value;
    #         changed, value = imgui.slider_float("Top", self._top, 1, 50, "%0.1f", 1);
    #         self._top = value;

    #         self._camera.projMat = util.ortho(self._left, self._right, self._bottom, self._top, self._near, self._far);
    #     elif self._mode == "perspective":
    #         changed, value = imgui.slider_float("FOV", self._fov, 1, 120, "%0.1f", 1);
    #         self._fov = value;
    #         changed, value = imgui.slider_float("Aspect", self._aspect, 0.5, 2, "%0.1f", 1);
    #         self._aspect = value;

    #         self._camera.projMat = util.perspective(self._fov, self._aspect, self._near, self._far)

if __name__ == '__main__':
  scene = Scene()
  rootEntity = scene.world.createEntity(Entity(name="Root"))
  a = SimpleCamera().mainCamera
  print(type(a))
  # scene.world.print()
  