
import imgui
import Elements.pyECSS.math_utilities as util
from Elements.pyGLV.GUI.Viewer import RenderWindow, RenderDecorator, SDL2Window
from Elements.pyECSS.Component import BasicTransform
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
        # self._eye = (2.5, 2.5, 2.5)
        # self._target = (0.0, 0.0, 0.0) 
        # self._up = (0.0, 1.0, 0.0)

        # # TRS Variables 
        # self.translation = {};
        # self.translation["x"] = 0; self.translation["y"] = 0; self.translation["z"] = 0; 

        # self.rotation = {};
        # self.rotation["x"] = 0; self.rotation["y"] = 0; self.rotation["z"] = 0; 

        # self.scale = {};
        # self.scale["x"] = 0; self.scale["y"] = 0; self.scale["z"] = 0; 

        # #this is not used anywhere
        # self.color = [255, 50, 50];

        # self.lctrl = False
        
        # self.traverseCamera()
       
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
        
        # GPTODO here is the issue: SDL2Decorator takes an SDLWindow as wrappee wheras
        # ImGUIDEcorator takes and SDL2Decorator and decorates it!
        if isinstance(self.wrapeeWindow, SDL2Window):   
            self._imguiRenderer = SDL2Renderer(self.wrapeeWindow._gWindow)
            
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
        
    # def traverseCamera(self):
    #     self.cam = None
    #     found = False
    #     if self.wrapeeWindow.scene is not None:
    #         rootComp = self.wrapeeWindow.scene.world.root
    #         if rootComp._children is not None:
    #             Iterator = iter(rootComp._children)
    #             done_traversing = False
    #             while not found and not done_traversing:
    #                 try:
    #                     comp = next(Iterator)
    #                 except StopIteration:
    #                     done_traversing = True
    #                 else:
    #                     if "Camera" in comp.name: # just put the "Camera" string in the Entity that holds the camera
    #                         self.cam = comp
    #                         found = True
                        
    # def updateCamera(self, moveX, moveY, moveZ, rotateX, rotateY):  
    #     if self.cam != None:
    #         #for examples 7-11 and pyJANVRED implementations
    #         cameraspeed = 5
    #         scaleMat = util.scale(self.scale["x"], self.scale["y"], self.scale["z"])
    #         combinedMat = scaleMat
    #         if rotateX or rotateY: 
    #             rotMatX = util.rotate((1, 0, 0), -self.rotation["y"] * cameraspeed)
    #             rotMatY = util.rotate((0, 1, 0), self.rotation["x"] * cameraspeed)
    #             rotMatZ = util.rotate((0, 0, 1), self.rotation["z"] * cameraspeed)
    #             combinedMat = rotMatX @ rotMatY @ rotMatZ @ combinedMat  
    #         if moveX or moveY or moveZ:
    #             transMat = util.translate(self.translation["x"], self.translation["y"], -self.translation["z"])
    #             combinedMat = transMat @ combinedMat
    #         self.cam.trans1.trs = self.cam.trans1.trs @ combinedMat
    #     else:
    #         #for examples 4-5-6-8-9-10 implementations
    #         cameraspeed = 0.2
    #         teye = np.array(self._eye)
    #         ttarget = np.array(self._target)
    #         tup = np.array(self._up)

    #         forwardDir = util.normalise(ttarget - teye)
    #         rightDir = util.normalise(np.cross(tup, forwardDir))

    #         eyeUpd = np.array([0.0, 0.0, 0.0])
    #         targetUpd = np.array([0.0, 0.0, 0.0])   

    #         if rotateX:
    #             eyeUpd = rightDir * self.rotation["x"] * cameraspeed
    #         elif rotateY:
    #             s,c = util.sincos(1)
    #             rotDir = util.normalise(util.vec(s, c, 0.0)) * tup
    #             eyeUpd = rotDir * self.rotation["y"] * cameraspeed
                
    #         if moveX:
    #             eyeUpd = -cameraspeed * self.translation["x"] * rightDir
    #             targetUpd =  eyeUpd
    #         if moveY:
    #             eyeUpd = -self.translation["y"] * cameraspeed * tup
    #             targetUpd = eyeUpd
    #         if moveZ: 
    #             eyeUpd =  np.sign(self.translation["z"]) * cameraspeed * forwardDir

    #         teye += eyeUpd
    #         ttarget += targetUpd
    #         if (rotateX or rotateY):
    #             newForwardDir = util.normalise(ttarget - teye)
    #             tup = util.normalise(np.cross(newForwardDir, rightDir)) 

    #         self._eye = tuple(teye)
    #         self._target = tuple(ttarget)
    #         self._up = tuple(tup)

    #         self._updateCamera.value = util.lookat(util.vec(self._eye), util.vec(self._target), util.vec(self._up))
    #         if self._wrapeeWindow.eventManager is not None:
    #             self.wrapeeWindow.eventManager.notify(self, self._updateCamera)
        
 
    # def on_mouse_motion(self, event, x, y, dx, dy):
    #     """Called when the mouse is moved.

    #         event: sdl2.events.SDL_Event, 
    #         x: horiz coord relative to window, y: vert coord relative to window,
    #         dx: relative horizontal motion, dy: relative vertical motion
    #     """
    #     pass

    # def on_mouse_press(self, event, x, y, button, dclick):
    #     """Called when mouse buttons are pressed.

    #         event: sdl2.events.SDL_Event, 
    #         x: horiz coord relative to window, y: vert coord relative to window,
    #         dx: relative horizontal motion, dy: relative vertical motion
    #         button: RIGHT - MIDDLE - LEFT
    #         dclick: True - False if button was double click
    #     """
    #     pass

    # def resetAll(self):
    #     self.translation["x"] = 0.0
    #     self.translation["y"] = 0.0
    #     self.translation["z"] = 0.0
    #     self.rotation["x"] = 0.0
    #     self.rotation["y"] = 0.0
    #     self.rotation["z"] = 0.0
    #     self.scale["x"]= 1.0
    #     self.scale["y"]= 1.0
    #     self.scale["z"]= 1.0

    # def cameraHandling(self, x, y, height, width):
    #     keystatus = sdl2.SDL_GetKeyboardState(None)
    #     self.resetAll()

    #     if keystatus[sdl2.SDL_SCANCODE_LSHIFT]:
    #         if abs(x) > abs(y):
    #             self.translation["x"] = x/width*60 #np.sign(event.wheel.x)
    #             self.updateCamera(True, False, False, False, False)
    #         else:
    #             self.translation["y"] =  y/height*60 #np.sign(event.wheel.y)
    #             self.updateCamera(False, True, False, False, False)
    #     elif keystatus[sdl2.SDL_SCANCODE_LCTRL] or self.lctrl:
    #         self.translation["z"] =  y/height*60 #-np.sign(event.wheel.y) 
    #         self.updateCamera(False, False, True, False, False)
    #     else:
    #         if abs(x) > abs(y):
    #             self.rotation["x"] = np.sign(x) #event.wheel.x/height*180
    #             self.updateCamera(False, False,False, True, False)
    #         else:
    #             self.rotation["y"] = np.sign(y) #event.wheel.y/width*180
    #             self.updateCamera(False, False,False, False, True)

    # def event_input_process(self):
    #     """
    #     process SDL2 basic events and input
    #     """
    #     running = True
    #     events = sdl2.ext.get_events()
    #     width = self.wrapeeWindow._windowWidth
    #     height = self.wrapeeWindow._windowHeight
        
    #     #if not imgui.is_window_focused():
    #     for event in events:
            
    #         if event.type == sdl2.SDL_MOUSEWHEEL:
    #             x = event.wheel.x
    #             y = event.wheel.y
    #             self.cameraHandling(x,y,height,width)
    #             continue   

    #         if event.type == sdl2.SDL_MOUSEBUTTONUP:
    #             pass

    #         # on_mouse_press
    #         buttons = event.motion.state
    #         if buttons & sdl2.SDL_BUTTON_RMASK:
    #             x = -event.motion.xrel  
    #             y = event.motion.yrel 
    #             self.cameraHandling(x, y, height, width)
                
    #             continue               

    #         #keyboard events
    #         if event.type == sdl2.SDL_KEYDOWN:
    #             if event.key.keysym.sym == sdl2.SDLK_UP or event.key.keysym.sym == sdl2.SDLK_w :
    #                 pass
    #             if event.key.keysym.sym == sdl2.SDLK_DOWN or event.key.keysym.sym == sdl2.SDLK_s :
    #                 pass
    #             if event.key.keysym.sym == sdl2.SDLK_LEFT or event.key.keysym.sym == sdl2.SDLK_a :
    #                 pass
    #             if event.key.keysym.sym == sdl2.SDLK_RIGHT or event.key.keysym.sym == sdl2.SDLK_d :
    #                 pass
    #             if event.key.keysym.sym == sdl2.SDLK_LCTRL:
    #                 self.lctrl=True
    #             if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
    #                 running = False

    #         if event.type == sdl2.SDL_KEYUP and event.key.keysym.sym == sdl2.SDLK_LCTRL:
    #             self.lctrl = False

    #         if event.type == sdl2.SDL_QUIT:
    #             running = False

    #         if  event.type == sdl2.SDL_WINDOWEVENT:
    #             window = self.wrapeeWindow
    #             if event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
    #                 print("Window Resized to ", event.window.data1, " X " , event.window.data2)
    #                 window._windowWidth = event.window.data1
    #                 window._windowHeight = event.window.data2
    #                 # new width and height: event.window.data1 and event.window.data2
    #                 gl.glViewport(0, 0, event.window.data1, event.window.data2)
            
    #         #imgui event
    #         self._imguiRenderer.process_event(event)
    #     #imgui input
    #     self._imguiRenderer.process_inputs()
    #     return running  
        
    def display_post(self):
        # this is important to draw the ImGUI in full mode and not wireframe!
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
        
        # render imgui (after 3D scene and just before the SDL double buffer swap window)
        imgui.render()
        self._imguiRenderer.render(imgui.get_draw_data())


        # call the SDL window window swapping in the end of the scene as final render action
        self.wrapeeWindow.display_post()
        
        
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
        imgui.text("PyImgui + PySDL2 integration successful!")
        imgui.text(self._wrapeeWindow._gVersionLabel)
        
        # populate window with extra UI elements
        imgui.separator()
        imgui.new_line()
        #
        # wireframe Event updates the GL state
        self._changed, self._checkbox = imgui.checkbox("Wireframe", self._wireframeMode)
        if self._changed:
            if self._checkbox is True:
                self._wireframeMode = True
                self._updateWireframe.value = self._wireframeMode
                if self._wrapeeWindow.eventManager is not None:
                    self.wrapeeWindow.eventManager.notify(self, self._updateWireframe) 
                print(f"wireframe: {self._wireframeMode}")
            if self._checkbox is False:
                self._wireframeMode = False
                self._updateWireframe.value = self._wireframeMode
                if self._wrapeeWindow.eventManager is not None:
                    self.wrapeeWindow.eventManager.notify(self, self._updateWireframe) 
                print(f"wireframe: {self._wireframeMode}")
        #
        # simple slider for color
        self._changed, self._colorEditor = imgui.color_edit3("Color edit", *self._colorEditor)
        if self._changed:
            print(f"_colorEditor: {self._colorEditor}")
        imgui.separator()
        #
        # START
        # simple slider for eye - IMPORTANT PART HERE
        self._changed, self._eye = imgui.drag_float3( "Eye", *self._eye, change_speed = 0.01, min_value=-10, max_value=10,format="%.3f")
        if self._changed:
            self._updateCamera.value = util.lookat(util.vec(self._eye), util.vec(self._target), util.vec(self._up))
            print ("NEW CAMERA VALUE", self._updateCamera.value)
            if self._wrapeeWindow.eventManager is not None:
                    self.wrapeeWindow.eventManager.notify(self, self._updateCamera)
            print(f"_eye: {self._eye}")
        imgui.separator()
        #
        # simple slider for target
        self._changed, self._target = imgui.drag_float3( "Target", *self._target, change_speed = 0.01, min_value=-10, max_value=10,format="%.3f")
        if self._changed:
            self._updateCamera.value = util.lookat(util.vec(self._eye), util.vec(self._target), util.vec(self._up))
            print ("NEW CAMERA VALUE", self._updateCamera.value)
            if self._wrapeeWindow.eventManager is not None:
                self.wrapeeWindow.eventManager.notify(self, self._updateCamera)
            print(f"_target: {self._target}")
        imgui.separator()
        # simple slider for up
        self._changed, self._up = imgui.drag_float3( "Up", *self._up, change_speed = 0.01 ,min_value=-5, max_value=5,format="%.3f")
        if self._changed:
            self._updateCamera.value = util.lookat(util.vec(self._eye), util.vec(self._target), util.vec(self._up))
            print ("NEW CAMERA VALUE", self._updateCamera.value)
            if self._wrapeeWindow.eventManager is not None:
                self.wrapeeWindow.eventManager.notify(self, self._updateCamera)
            print(f"_up: {self._up}")
        imgui.separator()
        # END
        # simple FPS counter
        strFrameRate = str(("Application average: ", imgui.get_io().framerate, " FPS"))
        imgui.text(strFrameRate)
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
            imgui.begin("ECSS graph")
            imgui.columns(2,"Properties")
            if imgui.tree_node(sceneRoot, imgui.TREE_NODE_OPEN_ON_ARROW):
                self.drawNode(self.wrapeeWindow.scene.world.root)
                imgui.tree_pop()
            imgui.next_column()
            imgui.text("Properties")
            imgui.separator()
        else:
            imgui.begin("ECSS graph")
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
            changed, value = imgui.drag_float3("X,Y,Z",self.translation["x"],self.translation["y"],self.translation["z"], 0.01, -30, 30, "%.001f", 1);
            self.translation["x"],self.translation["y"],self.translation["z"] = value[0],value[1], value[2]
            imgui.tree_pop();
        if imgui.tree_node("Rotation", imgui.TREE_NODE_OPEN_ON_ARROW):
            # changed, value = imgui.slider_float("X", self.rotation["x"], -90, 90, "%.1f", 1);
            # self.rotation["x"] = value;
            # changed, value = imgui.slider_float("Y", self.rotation["y"], -90, 90, "%.1f", 1);
            # self.rotation["y"] = value;
            # changed, value = imgui.slider_float("Z", self.rotation["z"], -90, 90, "%.1f", 1);
            # self.rotation["z"] = value;
            changed, value = imgui.drag_float3("X,Y,Z",self.rotation["x"],self.rotation["y"],self.rotation["z"], 1, -180, 180, "%.1f", 1);
            self.rotation["x"],self.rotation["y"],self.rotation["z"] = value[0],value[1], value[2]
            imgui.tree_pop();
        if imgui.tree_node("Scale", imgui.TREE_NODE_OPEN_ON_ARROW):
            # changed, value = imgui.slider_float("X", self.scale["x"], 0, 3, "%.01f", 1);
            # self.scale["x"] = value;
            # changed, value = imgui.slider_float("Y", self.scale["y"], 0, 3, "%.01f", 1);
            # self.scale["y"] = value;
            # changed, value = imgui.slider_float("Z", self.scale["z"], 0, 3, "%.01f", 1);
            # self.scale["z"] = value;
            changed, value = imgui.drag_float3("X,Y,Z",self.scale["x"],self.scale["y"],self.scale["z"], 0.01, 0, 4, "%.01f", 1);
            self.scale["x"],self.scale["y"],self.scale["z"] = value[0],value[1], value[2]
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
                                self.selected = comp;
                                if isinstance(comp, BasicTransform):
                                    [x, y, z] = comp.translation;
                                    self.translation["x"] = x;
                                    self.translation["y"] = y;
                                    self.translation["z"] = z;
                                    [x, y, z] = comp.scale;
                                    self.scale["x"] = x;
                                    self.scale["y"] = y;
                                    self.scale["z"] = z;
                                    [x, y, z] = comp.rotationEulerAngles;
                                    self.rotation["x"] = x;
                                    self.rotation["y"] = y;
                                    self.rotation["z"] = z;
                                # elif isinstance(comp, GameObjectEntity):
                                    # self.color = comp.color.copy();
                            else:                       # Set GUI values to trs;
                                if isinstance(comp, BasicTransform):
                                    transMat = util.translate(self.translation["x"], self.translation["y"], self.translation["z"]);
                                    rotMatX = util.rotate((1, 0, 0), self.rotation["x"])
                                    rotMatY = util.rotate((0, 1, 0), self.rotation["y"])
                                    rotMatZ = util.rotate((0, 0, 1), self.rotation["z"])
                                    scaleMat = util.scale(self.scale["x"], self.scale["y"], self.scale["z"])

                                    comp.trs = util.identity() @ transMat @ rotMatX @ rotMatY @ rotMatZ @ scaleMat;
                                    # comp.trs = scaleMat @ rotMatZ @ rotMatY @ rotMatX @ transMat;
                                elif hasattr(comp, "drawSelfGui"):
                                    comp.drawSelfGui(imgui);

                        imgui.tree_pop()
                    
                    self.drawNode(comp) # recursive call of this method to traverse hierarchy
                    imgui.unindent(10) # Corrent placement of unindent

    def event_input_process(self):
        """
        process SDL2 basic events and input
        """
        return super().event_input_process()


class ImGUIecssDecorator2(ImGUIDecorator):
    """custom ImGUI decorator for this example

    :param ImGUIDecorator: [description]
    :type ImGUIDecorator: [type]
    """
    def __init__(self, wrapee: RenderWindow, imguiContext = None):
        super().__init__(wrapee, imguiContext)
        self.selected = None # Selected should be a component
        self.selected_node = None

    def hierarchyVisualizer(self, sceneRoot):
        imgui.begin("ECSS Hierarchy")
        imgui.columns(1,"Hierarchy")
        self.drawNodes(sceneRoot, True)
        imgui.end()

    def inspectorVisualizer(self):
        imgui.begin("ECSS Inspector")
        imgui.columns(1,"Components")
            
        if self.selected_node is not None:
            imgui.text(self.selected_node.name + " Components")
            imgui.separator()

        #if imgui.tree_node("Translation", imgui.TREE_NODE_OPEN_ON_ARROW):
            # changed, value = imgui.slider_float("X", self.translation["x"], -3, 3, "%.01f", 1);
            # self.translation["x"] = value;
            # changed, value = imgui.slider_float("Y", self.translation["y"], -3, 3, "%.01f", 1);
            # self.translation["y"] = value;
            # changed, value = imgui.slider_float("Z", self.translation["z"], -3, 3, "%.01f", 1);
            # self.translation["z"] = value;
            imgui.text("Translation")
            changed, value = imgui.drag_float3("X,Y,Z",self.translation["x"],self.translation["y"],self.translation["z"], 0.01, -30, 30, "%.001f", 1)
            self.translation["x"],self.translation["y"],self.translation["z"] = value[0],value[1], value[2]
        #imgui.tree_pop()
        #if imgui.tree_node("Rotation", imgui.TREE_NODE_OPEN_ON_ARROW):
            # changed, value = imgui.slider_float("X", self.rotation["x"], -90, 90, "%.1f", 1);
            # self.rotation["x"] = value;
            # changed, value = imgui.slider_float("Y", self.rotation["y"], -90, 90, "%.1f", 1);
            # self.rotation["y"] = value;
            # changed, value = imgui.slider_float("Z", self.rotation["z"], -90, 90, "%.1f", 1);
            # self.rotation["z"] = value;
            imgui.text("Rotation")
            changed, value = imgui.drag_float3("X,Y,Z",self.rotation["x"],self.rotation["y"],self.rotation["z"], 1, -180, 180, "%.1f", 1)
            self.rotation["x"],self.rotation["y"],self.rotation["z"] = value[0],value[1], value[2]
    #    imgui.tree_pop()
        #if imgui.tree_node("Scale", imgui.TREE_NODE_OPEN_ON_ARROW):
            # changed, value = imgui.slider_float("X", self.scale["x"], 0, 3, "%.01f", 1);
            # self.scale["x"] = value;
            # changed, value = imgui.slider_float("Y", self.scale["y"], 0, 3, "%.01f", 1);
            # self.scale["y"] = value;
            # changed, value = imgui.slider_float("Z", self.scale["z"], 0, 3, "%.01f", 1);
            # self.scale["z"] = value;
            imgui.text("Scale")
            changed, value = imgui.drag_float3("X,Y,Z",self.scale["x"],self.scale["y"],self.scale["z"], 0.01, 0, 4, "%.01f", 1)
            self.scale["x"],self.scale["y"],self.scale["z"] = value[0],value[1], value[2]
        else: 
            imgui.text("Components")
        
        if self.selected_node is not None:
            self.drawNodes(self.selected_node, False)
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
        
    def drawNodes(self, component, checkEntityFlag=True):
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
                    if (checkEntityFlag == True and comp.type == "Entity") or (not checkEntityFlag and comp.type != "Entity"): 
                        #imgui.indent(10)
                        clicked = False
                        flags = SELECTED_FLAGS if self.selected_node == comp else DEFAULT_FLAGS
                        if imgui.tree_node(comp.name + "##" + str(comp.id), flags):
                            clicked = self.drawNodes(comp, checkEntityFlag) # recursive call of this method to traverse hierarchy
                            imgui.tree_pop()
                        
                        if comp.type == "Entity" and not clicked and imgui.is_item_clicked():
                            self.selected_node = comp
                            ret = True
                        #imgui.unindent(10) # Corrent placement of unindent
        return ret

    def event_input_process(self):
        """
        process SDL2 basic events and input
        """
        return super().event_input_process()
        


        #imgui.text(comp.name)
                        #_, selected = imgui.selectable(comp.__str__(), True)
                        #     if selected:

                        #         if comp != self.selected: # First time selecting it. Set trs values to GUI;
                        #             self.selected = comp;
                        #             if isinstance(comp, BasicTransform):
                        #                 [x, y, z] = comp.translation;
                        #                 self.translation["x"] = x;
                        #                 self.translation["y"] = y;
                        #                 self.translation["z"] = z;
                        #                 [x, y, z] = comp.scale;
                        #                 self.scale["x"] = x;
                        #                 self.scale["y"] = y;
                        #                 self.scale["z"] = z;
                        #                 [x, y, z] = comp.rotationEulerAngles;
                        #                 self.rotation["x"] = x;
                        #                 self.rotation["y"] = y;
                        #                 self.rotation["z"] = z;
                        #             # elif isinstance(comp, GameObjectEntity):
                        #                 # self.color = comp.color.copy();
                        #         else:                       # Set GUI values to trs;
                        #             if isinstance(comp, BasicTransform):
                        #                 transMat = util.translate(self.translation["x"], self.translation["y"], self.translation["z"]);
                        #                 rotMatX = util.rotate((1, 0, 0), self.rotation["x"])
                        #                 rotMatY = util.rotate((0, 1, 0), self.rotation["y"])
                        #                 rotMatZ = util.rotate((0, 0, 1), self.rotation["z"])
                        #                 scaleMat = util.scale(self.scale["x"], self.scale["y"], self.scale["z"])

                        #                 comp.trs = util.identity() @ transMat @ rotMatX @ rotMatY @ rotMatZ @ scaleMat;
                        #                 # comp.trs = scaleMat @ rotMatZ @ rotMatY @ rotMatX @ transMat;
                        #             elif hasattr(comp, "drawSelfGui"):
                        #                 comp.drawSelfGui(imgui);