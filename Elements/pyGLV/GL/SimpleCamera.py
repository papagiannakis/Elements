"""
SimpleCamera utility class
    
Convenience class to assemble an OpenGL camera

"""

from Elements.pyGLV.GL.Scene import Scene # for SimpleCamera
from Elements.pyECSS.Entity import Entity
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Component import BasicTransform, Camera

class SimpleCamera(Entity):
    """
    This is a Simple Camera Class, used to store a Camera Entity
    """
    def __init__(self, name=None, type=None, id=None) -> None:
        """
        Initializes  a SimpleCamera Entity
        """
        super().__init__(name, type, id)
        scene = Scene();
        rootEntity = scene.world.root;

        scene.world.addEntityChild(rootEntity, self);

        entityCam1 = scene.world.createEntity(Entity(name="entityCam1"));
        scene.world.addEntityChild(self, entityCam1);
        self.trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()));
        
        entityCam2 = scene.world.createEntity(Entity(name="entityCam2"));
        scene.world.addEntityChild(entityCam1, entityCam2);
        self.trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="trans2", trs=util.identity()));
        
        self._near = 1;
        self._far = 20;

        self._fov = 50;
        self._aspect = 1.0;

        self._left = -10;
        self._right = 10;
        self._bottom = -10;
        self._top = 10;


        self._mode = "perspective";
        self._camera = scene.world.addComponent(entityCam2, Camera(util.perspective(self._fov, self._aspect, self._near, self._far), "MainCamera", "Camera", "500"));        
        None;

    @property
    def camera(self):
        return self._camera;

    def drawSelfGui(self, imgui):
        """
        Describes how the simple camera is drawn in the imgui ECCS Tree
        """
        if imgui.button("Orthograpic") and self._mode == "perspective":
            self._mode = "orthographic";
            self._camera.projMat = util.ortho(self._left, self._right, self._bottom, self._top, self._near, self._far);
        if imgui.button("Perspective") and self._mode == "orthographic":
            self._mode = "perspective";
            self._camera.projMat = util.perspective(self._fov, self._aspect, self._near, self._far)

        if self._mode == "orthographic":
            changed, value = imgui.slider_float("Left", self._left, -50, -1, "%0.1f", 1);
            self._left = value;
            changed, value = imgui.slider_float("Right", self._right, 1, 50, "%0.1f", 1);
            self._right = value;
            changed, value = imgui.slider_float("Bottom", self._bottom, -50, -1, "%0.1f", 1);
            self._bottom = value;
            changed, value = imgui.slider_float("Top", self._top, 1, 50, "%0.1f", 1);
            self._top = value;

            self._camera.projMat = util.ortho(self._left, self._right, self._bottom, self._top, self._near, self._far);
        elif self._mode == "perspective":
            changed, value = imgui.slider_float("FOV", self._fov, 1, 120, "%0.1f", 1);
            self._fov = value;
            changed, value = imgui.slider_float("Aspect", self._aspect, 0.5, 2, "%0.1f", 1);
            self._aspect = value;

            self._camera.projMat = util.perspective(self._fov, self._aspect, self._near, self._far)

    