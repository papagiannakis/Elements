from imgui_bundle import imgui# type: ignore
from Elements.pyGLV.GL.FrameBuffer import FrameBuffer
from Elements.pyGLV.GUI.Guizmos import Gizmos
import Elements.extensions.BasicShapes.BasicShapes as bshapes
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GUI.Viewer import RenderWindow
import numpy as np
from imgui_bundle import imguizmo #type: ignore
import Elements.pyECSS.math_utilities as util
import glm
from Elements.pyGLV.GL.FrameBuffer import FrameBuffer

shapes = {"Cube" : bshapes.CubeSpawn, "Sphere" : bshapes.SphereSpawn, "Cylinder" : bshapes.CylinderSpawn, "Cone" : bshapes.ConeSpawn, "Torus" : bshapes.TorusSpawn};

update_needed = True;
first_run = True;

class SceneWindow:
    def __init__(self, wrapee: RenderWindow, imguiContext = None, ) -> None:
        self._buffer = FrameBuffer();
        self.wrapee = wrapee;
    
        if imguiContext is None:
            print("Error. You did not provide an imgui context for the gizmos\nShutting Down...");
            exit(1);
            
        self.gizmo = Gizmos(imguiContext);
        self.changed = None;
        
        self.selected_parent = None;
        self.shape = None;
        
        self.name = "";
        self.add_entity = False;
        self.remove_entity = False;

        self.entities = [];

        self.to_be_removed = None;
        self._buffer = FrameBuffer();
    

    def mainWindowLoop(self, view, wireframe, selected, currOperation):
        """
        Main Loop Method. Responsible for displaying all windows of the main dockspace including the top menu bar.

        :param view: Combination of eye, target and up vectors to be used for the camera gizmo
        :type view: Tuple
        :param wireFrame: Wireframe flag controller by the checkbox in the GUI.
        :type wireFrame: boolean
        :param selected: Reference to the selected component from the node editor
        :type selected: Component
        :param currOperation: Current operation of transformation gizmos (translate, rotate, scale)
        :type currOperation: imguizmo.imguizmo.OPERATION  
        """
        global update_needed, main_window_selected
        
        if update_needed:
            self.entities = [];
            self.update_entities(self.wrapee.scene.world.root);
            update_needed = False;
            
        self.mainMenuBar();
        self.gizmo.currentGizmoOperation = currOperation;

        imgui.begin("Scene");
        self.wrapee.scene._window = imgui.is_window_hovered();
    
        self._buffer.drawFramebuffer(wireframe);

        cameraChange = False;
        if self.gizmo.drawCameraGizmo():
            cameraChange = True;
            view[0] = self.gizmo.decompose_look_at();
        else:
            self.gizmo.setView(np.array(glm.lookAt(view[0], view[1], view[2])));
            
        
        trsChange, trs = self.gizmo.drawTransformGizmo(selected);
        
        imgui.end();
        

        if cameraChange and self.gizmo._cameraSystem is not None:
            camera_trs = imguizmo.im_guizmo.decompose_matrix_to_components(self.gizmo._view);
            [x, y, z] = self.gizmo._cameraSystem._children[0]._children[0].translation
            transMat = util.translate(x,y,z);
            rotMatX = util.rotate((1, 0, 0), -camera_trs.rotation[0])
            rotMatY = util.rotate((0, 1, 0), -camera_trs.rotation[1])
            rotMatZ = util.rotate((0, 0, 1), -camera_trs.rotation[2])
            scaleMat = util.scale(camera_trs.scale[0],camera_trs.scale[1],camera_trs.scale[2])
            self.gizmo._cameraSystem._children[0]._children[0].trs = util.identity() @ transMat @ rotMatX @ rotMatY @ rotMatZ @ scaleMat

        return cameraChange, view, trsChange, imguizmo.im_guizmo.decompose_matrix_to_components(trs)

    def mainMenuBar(self):
        """
        Displays the main menu bar on top of the main window for accessing the entity management features
        """
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File"):
                if imgui.begin_menu("Entites"):
                    _, clicked = imgui.menu_item("Add", "", False)
                    if clicked:
                        self.add_entity = True;
                    if imgui.begin_menu("Remove"):
                        self.show_selectable_entities(self.wrapee.scene.world.root);
                        imgui.end_menu();
                    imgui.end_menu()
                if imgui.menu_item("Close", "Lal", False):
                    pass
                imgui.end_menu() 
            imgui.end_main_menu_bar()


    def addEntityWindow(self):
        """
        Displays the entity addition window. Called when the approppriate tab is clicked through the menu bar
        """
        global update_needed
        tmp = None;
        add = False;

        if self.add_entity:
            _, self.add_entity = imgui.begin("Create Entity",  1)

            imgui.text("Name: "); imgui.same_line()
            _, self.name = imgui.input_text(' ', self.name)

            prev_shape = "Select Shape"
            if self.shape is not None:
                prev_shape = self.shape

            imgui.text("Shape: "); imgui.same_line();
            if imgui.begin_combo("#S", prev_shape):
                for shape in shapes.keys():
                    _ ,selected = imgui.selectable(shape, self.shape is not None and self.shape == shape)
                    if selected:
                        self.shape = shape
                imgui.end_combo()
                    
            prev_parent = "Select Parent"
            if self.selected_parent is not None:
                prev_parent = self.selected_parent.name;

            imgui.text("Parent:"); imgui.same_line();
            if imgui.begin_combo("#P", prev_parent):
                for entity in self.entities:
                    _, clicked = imgui.selectable(entity.name, False);
                    if clicked:
                        self.selected_parent = entity;
                imgui.end_combo();

            if imgui.button("Add"):
                
                if self.name == "":
                    tmp = shapes[self.shape](parent = self.selected_parent);
                else:
                    tmp = shapes[self.shape](self.name, parent = self.selected_parent);
            
                self.shape = None;
                self.selected_parent = None;
                update_needed = True;
                add = True;
                self.add_entity = False;
            
            imgui.end()
        
        return add, tmp;
        
    def removeEntityWindow(self):
        """
        Displays a confirmation dialog when an entity is about to be deleted
        """
        remove = False;
        node = None;

        if self.remove_entity and self.to_be_removed is not None:
            _, self.remove_entity = imgui.begin("Warning",  1)
            imgui.text("Are you sure you want to remove " + self.to_be_removed.name + "?");
            yes = imgui.button("Yes", imgui.ImVec2(40,20)); 
            imgui.same_line();
            no = imgui.button("No", imgui.ImVec2(40,20));
            

            if yes or no:   
                if yes:
                    self.to_be_removed.parent.remove(self.to_be_removed);
                    remove = True;
                    node = self.to_be_removed;
                
                self.to_be_removed = None;
            
            imgui.end()
            
        return remove, node;


    def update_entities(self, component):
        """
        Updates the ECSS when a new entity is added.
        Recursive function beginning from the given component.

        :param component: Component from which the update will be initiated
        :type component: Component
        """
        global first_run 
        if component._children is not None:
            debugIterator = iter(component._children)
            done_traversing = False
            while not done_traversing:
                try:
                    comp = next(debugIterator)
                except StopIteration:
                    done_traversing = True
                else:
                    if isinstance(comp, Entity):
                        if first_run:
                            print("first_run");
                            first_run = False;
                            from Elements.pyGLV.GL.SimpleCamera import SimpleCamera
                            if isinstance(comp, SimpleCamera):
                                self.gizmo._cameraSystem = comp;

                        self.entities.append(comp);
                    self.update_entities(comp);
    

    def show_selectable_entities(self, comp: Entity):
        """
        Displays a list of all the entities. Recursive beginning with the entity given as a parameter

        :param comp: Entity from which the list will be begin to be put together
        :type comp: Entity
        """
        if comp._children is not None:
            for child in comp._children:
                if isinstance(child, Entity):
                    _, clicked = imgui.menu_item(child.name, "", False);
                    if clicked:
                        self.to_be_removed = child;
                        self.remove_entity = True
                self.show_selectable_entities(child);
        
        if not self.remove_entity:
            self.remove_entity = False