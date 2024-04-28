from imgui_bundle import imgui# type: ignore
from Elements.pyGLV.GL.FrameBuffer import FrameBuffer
from Elements.pyGLV.GUI.Guizmos import Gizmos
import Elements.extensions.BasicShapes.BasicShapes as bshapes
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GUI.Viewer import RenderWindow
import numpy as np
import glm

shapes = {"Cube" : bshapes.CubeSpawn, "Sphere" : bshapes.SphereSpawn, "Cylinder" : bshapes.CylinderSpawn, "Cone" : bshapes.ConeSpawn, "Torus" : bshapes.TorusSpawn};

update_needed = True;

class SceneWindow:
    def __init__(self, wrapee: RenderWindow, imguiContext = None, ) -> None:
        self._buffer = FrameBuffer();
        self.wrapee = wrapee;
    
        if imguiContext is None:
            print("Error. You did not provide an imgui context for the gizmos\nShutting Down...");
            exit(1);
            
        self.gizmo = Gizmos(imguiContext);
        self.changed = None;
        self.cameraView = None;
        
        self.to_add = None;
        self.selected_parent = None;
        self.shape = None;
        
        self.name = "";
        self.add_entity = False;
        self.remove_entity = False;

        self.entities = [];

        self.to_be_removed = None;
    

    def mainWindowLoop(self, view, wireframe, selected, currOperation):
        if self.to_add is not None:
            self.wrapee.scene.world.addEntityChild(self.wrapee.scene.world.root, self.to_add); 
            self.to_add = None;
            
        self.mainMenuBar();
        self.gizmo.currentGizmoOperation = currOperation;

        imgui.begin("Scene");
    
        self._buffer.drawFramebuffer(wireframe);

        cameraChange = False;
        if self.gizmo.drawCameraGizmo():
            cameraChange = True;
            view[0], view[1], view[2] = self.gizmo.decompose_look_at();
        else:
            self.gizmo.setView(np.array(glm.lookAt(view[0], view[2], view[1]), np.float32));
        
        trsChange, trs = self.gizmo.drawTransformGizmo(selected);
        
        imgui.end();

        return cameraChange, view, trsChange, self.gizmo.gizmo.decompose_matrix_to_components(trs)

    def mainMenuBar(self):
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File"):
                if imgui.begin_menu("Entites"):
                    _, clicked = imgui.menu_item("Add", "", False)
                    if clicked:
                        self.add_entity = True;
                    if imgui.begin_menu("Remove"):
                        self.remove_entity = self.show_selectable_entities();
                        imgui.end_menu();
                    imgui.end_menu()
                if imgui.menu_item("Close", "Lal", False):
                    pass
                imgui.end_menu() 
            imgui.end_main_menu_bar()


    def addEntityWindow(self):
        global update_needed
        tmp = None;
        add = False;
        if self.add_entity:
            _, self.add_entity = imgui.begin("Create Entity",  1)
            
            if update_needed:
                self.update_entities(self.wrapee.scene.world.root);
                update_needed = False;

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
                
                if self.name is "":
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
                    self.wrapee.scene.world.root.remove(self.to_be_removed);
                    remove = True;
                    node = self.to_be_removed;


                self.to_be_removed = None;
                print(self.to_be_removed)
            
            imgui.end()
            
        return remove, node;


    def update_entities(self, component):
        """
        Updates the ECSS when a new entity is added.
        Recursing function beginning from the given component.

        :param component: [description]
        :type component: Component
        """
        self.entities = [];
        if component._children is not None:
            debugIterator = iter(component._children)
            done_traversing = False
            while not done_traversing:
                try:
                    comp = next(debugIterator)
                    imgui.indent(10)
                except StopIteration:
                    done_traversing = True
                else:
                    if isinstance(comp, Entity):
                        self.entities.append(comp);

    def show_selectable_entities(self):
        for child in self.wrapee.scene.world.root._children:
            _, clicked = imgui.menu_item(child.name, "", False);
            if clicked:
                self.to_be_removed = child;
                return True

        return False