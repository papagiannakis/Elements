import numpy as np
import imgui
import Elements.pyECSS.math_utilities as util
from Elements.pyGLV.GUI.Viewer import RenderWindow, RenderDecorator
from Elements.pyECSS.Component import BasicTransform
from Elements.pyECSS.Entity import Entity
from imgui.integrations.sdl2 import SDL2Renderer
import OpenGL.GL as gl
from Elements.pyECSS.Event import Event
from Elements.pyECSS.System import System

class ImGUIDecorator(RenderDecorator):
    """
    ImGUI decorator

    :param RenderDecorator: [description]
    :type RenderDecorator: [type]
    """
    def __init__(self, wrapee: RenderWindow, imguiContext = None):
        super().__init__(wrapee)
        if imguiContext is None:
            self._imguiContext = imgui.create_context()
        else:
            self._imguiContext = imguiContext
        self._imguiRenderer = None
        #setup a simple Event: change to wireframe mode via the GUI
        self._updateWireframe = None
        self._updateCamera = None
        # extra UI elements
        self._wireframeMode = False
        self._changed = False
        self._checkbox = False
        self._colorEditor = wrapee._colorEditor

    def init(self):
        """
        Calls Decoratee init() and also sets up events
        """
        self.wrapeeWindow.init()
        if self._imguiContext is None:
            print("Window could not be created! ImGUI Error: ")
            exit(1)
        else:
            # print("Yay! ImGUI context created successfully")
            pass

        if self.wrapeeWindow.BACKEND_NAME == "SDL2":
            self._imguiRenderer = SDL2Renderer(self.wrapeeWindow._gWindow)
        elif self.wrapeeWindow.BACKEND_NAME == "GLFW":
            # Lazy import: keeps `glfw` an opt-in dependency -- this module is imported by nearly
            # every example, so importing imgui.integrations.glfw (and thus glfw itself) at
            # module level here would break every ImGui example in any environment without glfw
            # installed, not just the ones that actually use it.
            from imgui.integrations.glfw import GlfwRenderer
            self._imguiRenderer = GlfwRenderer(self.wrapeeWindow._gWindow, attach_callbacks=True)

        #
        # Setting up events that this class is publishing (if the EventManager is present in the decorated wrappee)
        #
        #self._updateWireframe = Elements.pyECSS.Event.Event(name="OnUpdateWireframe", id=201, value=None)
        self._updateWireframe = Event(name="OnUpdateWireframe", id=201, value=None)
        if self._wrapeeWindow.eventManager is not None:
            self._wrapeeWindow.eventManager._events[self._updateWireframe.name] = self._updateWireframe
            self._wrapeeWindow.eventManager._publishers[self._updateWireframe.name] = self


        #self._updateCamera = Elements.pyECSS.Event.Event(name="OnUpdateCamera", id=300, value=None)
        self._updateCamera = Event(name="OnUpdateCamera", id=300, value=None)
        if self._wrapeeWindow.eventManager is not None:
            self._wrapeeWindow.eventManager._events[self._updateCamera.name] = self._updateCamera
            self._wrapeeWindow.eventManager._publishers[self._updateCamera.name] = self

        # print(f'{self.getClassName()}: init()')


    def display(self):
        """
        ImGUI decorator display: calls wrapee (RenderWindow::display) as well as extra ImGUI widgets
        """
        self.wrapeeWindow.display()
        gl.glClearColor(*self._colorEditor, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        #render the ImGUI widgets
        self.extra()
        #draw scenegraph tree widget
        self.scenegraphVisualiser()
        #print(f'{self.getClassName()}: display()')

    def display_post(self):
        # this is important to draw the ImGUI in full mode and not wireframe!
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        # render imgui (after 3D scene and just before the SDL double buffer swap window)
        imgui.render()
        self._imguiRenderer.render(imgui.get_draw_data())


        # call the SDL window window swapping in the end of the scene as final render action
        self.wrapeeWindow.display_post()

    def _draw_wireframe_checkbox(self):
        """Wireframe toggle checkbox, kept in sync with the OnUpdateWireframe Event."""
        self._changed, self._checkbox = imgui.checkbox("Wireframe", self._wireframeMode)
        if self._changed:
            self._wireframeMode = self._checkbox
            self._updateWireframe.value = self._wireframeMode
            if self._wrapeeWindow.eventManager is not None:
                self.wrapeeWindow.eventManager.notify(self, self._updateWireframe)

    def _draw_background_color_picker(self):
        """Background color picker, backing Viewer.py's SDL2Window/GLFWWindow.display() clear color."""
        self._changed, self._colorEditor = imgui.color_edit3("Background Color", *self._colorEditor)

    def extra(self):
        """sample ImGUI widgets to be rendered on a RenderWindow
        """
        imgui.set_next_window_size(300.0, 200.0)

        #start new ImGUI frame context
        imgui.new_frame()
        #demo ImGUI window with all widgets
        # imgui.show_test_window()
        #new custom imgui window
        imgui.begin("Elements ImGUI window", True)
        #labels inside the window
        imgui.text(f"PyImgui + {self._wrapeeWindow.BACKEND_NAME} integration successful!")
        imgui.text(self._wrapeeWindow._gVersionLabel)

        # populate window with extra UI elements
        imgui.separator()
        imgui.new_line()
        #
        # wireframe Event updates the GL state
        self._draw_wireframe_checkbox()
        #
        # simple slider for background color
        self._draw_background_color_picker()
        imgui.separator()
        #
        # simple FPS counter
        imgui.text(f"FPS: {imgui.get_io().framerate:.2f}")
        #end imgui frame context
        imgui.end()

        #print(f'{self.getClassName()}: extra()')

    def scenegraphVisualiser(self):
        """display the ECSS in an ImGUI tree node structure
        Typically this is a custom widget to be extended in an ImGUIDecorator subclass
        """
        pass


    #def accept(self, system: Elements.pyECSS.System, event = None):
    def accept(self, system: System, event = None):
        system.apply2ImGUIDecorator(self, event)

class ImGUIecssDecorator(ImGUIDecorator):
    """custom ImGUI decorator for this example

    :param ImGUIDecorator: [description]
    :type ImGUIDecorator: [type]
    """
    def __init__(self, wrapee: RenderWindow, imguiContext = None):
        super().__init__(wrapee, imguiContext)
        self.selected = None; # Selected should be a component

        # TRS Variables
        self.tra = {}
        self.tra["x"] = 0; self.tra["y"] = 0; self.tra["z"] = 0

        self.rot = {}
        self.rot["x"] = 0; self.rot["y"] = 0; self.rot["z"] = 0

        self.sc = {}
        self.sc["x"] = 0; self.sc["y"] = 0; self.sc["z"] = 0


    def scenegraphVisualiser(self):
        """display the ECSS in an ImGUI tree node structure
        Typically this is a custom widget to be extended in an ImGUIDecorator subclass
        """
        sceneRoot = self.wrapeeWindow.scene.world.root.name
        if sceneRoot is None:
            sceneRoot = "ECSS Root Entity"

        twoColumn = False

        if twoColumn:
            # 2 Column Version
            imgui.begin("Scenegraph")
            imgui.columns(2,"Properties")
            if imgui.tree_node(sceneRoot, imgui.TREE_NODE_OPEN_ON_ARROW):
                self.drawNode(self.wrapeeWindow.scene.world.root)
                imgui.tree_pop()
            imgui.next_column()
            imgui.text("Properties")
            imgui.separator()
        else:
            imgui.begin("Scenegraph")
            imgui.columns(1,"Properties")
            # below is a recursive call to build-up the whole scenegraph as ImGUI tree
            # if imgui.tree_node(sceneRoot, imgui.TREE_NODE_OPEN_ON_ARROW):
                # self.drawNode(self.wrapeeWindow.scene.world.root)
                # imgui.tree_pop()
            # imgui.next_column()
            imgui.text("Properties")
            imgui.separator()


        # smallerTRSgui = True
        #TRS sample
        # if(isinstance(self.selected, BasicTransform)):

        if imgui.tree_node("Translation", imgui.TREE_NODE_OPEN_ON_ARROW):
            # changed, value = imgui.slider_float("X", self.translation["x"], -3, 3, "%.01f", 1);
            # self.translation["x"] = value;
            # changed, value = imgui.slider_float("Y", self.translation["y"], -3, 3, "%.01f", 1);
            # self.translation["y"] = value;
            # changed, value = imgui.slider_float("Z", self.translation["z"], -3, 3, "%.01f", 1);
            # self.translation["z"] = value;
            changed, value = imgui.drag_float3("X,Y,Z",self.tra["x"],self.tra["y"],self.tra["z"], 0.01, -30, 30, "%.001f", 1);
            self.tra["x"],self.tra["y"],self.tra["z"] = value[0],value[1], value[2]
            imgui.tree_pop();
        if imgui.tree_node("Rotation", imgui.TREE_NODE_OPEN_ON_ARROW):
            # changed, value = imgui.slider_float("X", self.rotation["x"], -90, 90, "%.1f", 1);
            # self.rotation["x"] = value;
            # changed, value = imgui.slider_float("Y", self.rotation["y"], -90, 90, "%.1f", 1);
            # self.rotation["y"] = value;
            # changed, value = imgui.slider_float("Z", self.rotation["z"], -90, 90, "%.1f", 1);
            # self.rotation["z"] = value;
            changed, value = imgui.drag_float3("X,Y,Z",self.rot["x"],self.rot["y"],self.rot["z"], 1, -180, 180, "%.1f", 1);
            self.rot["x"],self.rot["y"],self.rot["z"] = value[0],value[1], value[2]
            imgui.tree_pop();
        if imgui.tree_node("Scale", imgui.TREE_NODE_OPEN_ON_ARROW):
            # changed, value = imgui.slider_float("X", self.scale["x"], 0, 3, "%.01f", 1);
            # self.scale["x"] = value;
            # changed, value = imgui.slider_float("Y", self.scale["y"], 0, 3, "%.01f", 1);
            # self.scale["y"] = value;
            # changed, value = imgui.slider_float("Z", self.scale["z"], 0, 3, "%.01f", 1);
            # self.scale["z"] = value;
            changed, value = imgui.drag_float3("X,Y,Z",self.sc["x"],self.sc["y"],self.sc["z"], 0.01, 0, 4, "%.01f", 1);
            self.sc["x"],self.sc["y"],self.sc["z"] = value[0],value[1], value[2]
            imgui.tree_pop();


        if twoColumn:
            pass
        else:
            imgui.separator()
            if imgui.tree_node(sceneRoot, imgui.TREE_NODE_OPEN_ON_ARROW):
                self.drawNode(self.wrapeeWindow.scene.world.root)
                imgui.tree_pop()

        imgui.end()

    def drawNode(self, component):
        #create a local iterator of Entity's children
        if component._children is not None:
            debugIterator = iter(component._children)
            #call print() on all children (Concrete Components or Entities) while there are more children to traverse
            done_traversing = False
            while not done_traversing:
                try:
                    comp = next(debugIterator)
                    imgui.indent(10)
                except StopIteration:
                    done_traversing = True
                else:
                    # using ## creates unique labels, without showing anything after ##
                    # see: https://github.com/ocornut/imgui/blob/master/docs/FAQ.md#q-how-can-i-have-multiple-widgets-with-the-same-label
                    if imgui.tree_node(comp.name + "##" + str(comp.id), imgui.TREE_NODE_OPEN_ON_ARROW):
                        imgui.text(comp.name)
                        _, selected = imgui.selectable(comp.__str__(), True)
                        if selected:

                            if comp != self.selected: # First time selecting it. Set trs values to GUI;
                                self.selected = comp
                                if isinstance(comp, BasicTransform):
                                    [x, y, z] = comp.translation
                                    self.tra["x"] = x
                                    self.tra["y"] = y
                                    self.tra["z"] = z
                                    [x, y, z] = comp.scale
                                    self.sc["x"] = x
                                    self.sc["y"] = y
                                    self.sc["z"] = z
                                    [x, y, z] = comp.rotationEulerAngles
                                    self.rot["x"] = x
                                    self.rot["y"] = y
                                    self.rot["z"] = z
                                # elif isinstance(comp, GameObjectEntity):
                                    # self.color = comp.color.copy();
                            else:                       # Set GUI values to trs;
                                if isinstance(comp, BasicTransform):
                                    transMat = util.translate(self.tra["x"], self.tra["y"], self.tra["z"])
                                    rotMatX = util.rotate((1, 0, 0), self.rot["x"])
                                    rotMatY = util.rotate((0, 1, 0), self.rot["y"])
                                    rotMatZ = util.rotate((0, 0, 1), self.rot["z"])
                                    scaleMat = util.scale(self.sc["x"], self.sc["y"], self.sc["z"])

                                    comp.trs = util.identity() @ transMat @ rotMatX @ rotMatY @ rotMatZ @ scaleMat
                                    # comp.trs = scaleMat @ rotMatZ @ rotMatY @ rotMatX @ transMat;
                                elif hasattr(comp, "drawSelfGui"):
                                    comp.drawSelfGui(imgui)

                        imgui.tree_pop()

                    self.drawNode(comp) # recursive call of this method to traverse hierarchy
                    imgui.unindent(10) # Corrent placement of unindent


class ImGUIecssDecorator2(ImGUIDecorator):
    """custom ImGUI decorator for this example

    :param ImGUIDecorator: [description]
    :type ImGUIDecorator: [type]
    """
    def __init__(self, wrapee: RenderWindow, imguiContext = None):
        super().__init__(wrapee, imguiContext)
        self.selected = None # Selected should be a component
        self.selected_node = None

         # TRS Variables
        self.tra = {}
        self.tra["x"] = 0; self.tra["y"] = 0; self.tra["z"] = 0

        self.rot = {}
        self.rot["x"] = 0; self.rot["y"] = 0; self.rot["z"] = 0

        self.sc = {}
        self.sc["x"] = 0; self.sc["y"] = 0; self.sc["z"] = 0

    def hierarchyVisualizer(self, sceneRoot):
        imgui.begin("Scenegraph")
        imgui.columns(1,"Hierarchy")
        self.drawNodes(sceneRoot, True)  # True for onHierarchyFlag
        imgui.end()

    def inspectorVisualizer(self):
        imgui.begin("ECSS Inspector")
        imgui.columns(1,"Components")

        if self.selected_node is not None:
            imgui.text("Components for Entity: " + self.selected_node.name)
            imgui.separator()
            self.drawNodes(self.selected_node, False)   # false for onHierarchyFlag
        else:
            pass #imgui.text("Components")

        imgui.end()


    def scenegraphVisualiser(self):
        """display the ECSS in an ImGUI tree node structure
        Typically this is a custom widget to be extended in an ImGUIDecorator subclass
        """
        #sceneRoot = self.wrapeeWindow.scene.world.root.name
        #if sceneRoot is None:
         #   sceneRoot = "ECSS Root Entity"

        self.hierarchyVisualizer(self.wrapeeWindow.scene.world.root)
        self.inspectorVisualizer()

    def drawNodes(self, component, onHierarchyFlag=True):
        DEFAULT_FLAGS = imgui.TREE_NODE_BULLET
        SELECTED_FLAGS = imgui.TREE_NODE_BULLET | imgui.TREE_NODE_SELECTED

        #create a local iterator of Entity's children
        ret = False
        if component._children is not None:
            debugIterator = iter(component._children)
            #call print() on all children (Concrete Components or Entities) while there are more children to traverse
            done_traversing = False
            while not done_traversing:
                try:
                    comp = next(debugIterator)
                except StopIteration:
                    done_traversing = True
                else:
                    if (onHierarchyFlag == True and isinstance(comp, Entity)) or (not onHierarchyFlag and not isinstance(comp, Entity)):
                        clicked = False
                        flags = SELECTED_FLAGS if self.selected_node == comp else DEFAULT_FLAGS
                        if imgui.tree_node(comp.name + "##" + str(comp.id), flags):
                            if isinstance(comp, BasicTransform):
                                if comp != self.selected: # First time selecting it. Set trs values to GUI;
                                    self.selected = comp
                                    self.tra["x"], self.tra["y"], self.tra["z"] = comp.translation
                                    self.rot["x"], self.rot["y"], self.rot["z"] = comp.rotationEulerAngles
                                    self.sc["x"], self.sc["y"], self.sc["z"] = comp.scale

                                imgui.text("Translation")
                                changedT, valueT = imgui.drag_float3("Xt,Yt,Zt",self.tra["x"],self.tra["y"],self.tra["z"], 0.01, -30, 30, "%.001f", 1)
                                if changedT:
                                    self.tra["x"],self.tra["y"],self.tra["z"] = valueT

                                imgui.text("Rotation")
                                changedR, valueR = imgui.drag_float3("Xr,Yr,Zr",self.rot["x"],self.rot["y"],self.rot["z"], 1, -180, 180, "%.1f", 1)
                                if changedR:
                                    self.rot["x"],self.rot["y"],self.rot["z"] = valueR

                                imgui.text("Scale")
                                changedS, valueS = imgui.drag_float3("Xs,Ys,Zs",self.sc["x"],self.sc["y"],self.sc["z"], 0.01, 0, 4, "%.01f", 1)
                                if changedS:
                                    self.sc["x"],self.sc["y"],self.sc["z"] = valueS

                                if changedT or changedR or changedS:
                                    transMat = util.translate(self.tra["x"], self.tra["y"], self.tra["z"])
                                    rotMatX = util.rotate((1, 0, 0), self.rot["x"])
                                    rotMatY = util.rotate((0, 1, 0), self.rot["y"])
                                    rotMatZ = util.rotate((0, 0, 1), self.rot["z"])
                                    scaleMat = util.scale(self.sc["x"], self.sc["y"], self.sc["z"])
                                    comp.trs = util.identity() @ transMat @ rotMatX @ rotMatY @ rotMatZ @ scaleMat

                            clicked = self.drawNodes(comp, onHierarchyFlag) # recursive call of this method to traverse hierarchy


                            if not isinstance(comp, Entity):
                                _, selected = imgui.selectable(comp.__str__(), True)
                                if hasattr(comp, "drawSelfGui"):
                                    comp.drawSelfGui(imgui)
                            imgui.tree_pop()

                        if isinstance(comp, Entity) and not clicked and imgui.is_item_clicked():
                            self.selected_node = comp
                            ret = True
        return ret
