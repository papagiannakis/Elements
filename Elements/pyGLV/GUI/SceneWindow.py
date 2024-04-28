from imgui_bundle import imgui# type: ignore
from Elements.pyGLV.GL.FrameBuffer import FrameBuffer
from Elements.pyGLV.GUI.Guizmos import Gizmos
import numpy as np
import glm

class SceneWindow:
    def __init__(self, imguiContext = None) -> None:
        self._buffer = FrameBuffer();
    
        if imguiContext is None:
            print("Error. You did not provide an imgui context for the gizmos\nShutting Down...");
            exit(1);
            
        self.gizmos = Gizmos(imguiContext);
        self.changed = None;
        self.cameraView = None;
    
        self.shape = None;
        
        self.add_entity = False;
        self.remove_entity = False;

        self.to_be_removed = None;

    def mainWindow(self):
        self.mainMenuBar();

        imgui.begin("Scene");               # scene window


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
        if self.add_entity:
            _, self.add_entity = imgui.begin("Create Entity",  1)
            if self.add_entity_window():
                self.add_entity = False;
            imgui.end()
        

        if self.remove_entity and self.to_be_removed is not None:
            _, self.remove_entity = imgui.begin("Warning",  1)
            imgui.text("Are you sure you want to remove " + self.to_be_removed.name + "?");
            yes = imgui.button("Yes", imgui.ImVec2(40,20)); 
            imgui.same_line();
            no = imgui.button("No", imgui.ImVec2(40,20));

            if yes or no:   
                if yes:
                    self.wrapeeWindow.scene.world.root.remove(self.to_be_removed);
                    self.node_editor.remove(self.to_be_removed);

                self.to_be_removed = None;
                print(self.to_be_removed)
            
            imgui.end()

        self._buffer.drawFramebuffer(self._wireframeMode);
        if self.gizmo.drawCameraGizmo():
            self._eye, self._up, self._target = self.gizmo.decompose_look_at();
            self._updateCamera.value = np.array(glm.lookAt(self._eye, self._target, self._up), np.float32)
            if self._wrapeeWindow.eventManager is not None:
                    self.wrapeeWindow.eventManager.notify(self, self._updateCamera)
        else:
            self.gizmo.setView(np.array(glm.lookAt(self._eye, self._target, self._up), np.float32));
        
        changed, trs = self.gizmo.drawTransformGizmo(self.selected);

        if changed:
            components = self.gizmo.gizmo.decompose_matrix_to_components(trs);
            if self.gizmo.currentGizmoOperation == self.gizmo.gizmo.OPERATION.translate:
                self.tra['z'], self.tra['y'], self.tra['x'] = components.translation[0], components.translation[1], components.translation[2];
            elif self.gizmo.currentGizmoOperation == self.gizmo.gizmo.OPERATION.rotate:
                self.rot['z'], self.rot['y'], self.rot['x'] = -components.rotation[0], -components.rotation[1], -components.rotation[2];
            elif self.gizmo.currentGizmoOperation == self.gizmo.gizmo.OPERATION.scale:
                self.sc['z'], self.sc['y'], self.sc['x'] = components.scale[0], components.scale[1], components.scale[2];
        
        imgui.end();

    def add_entity_window(self):
        """
        Displays an imgui window for adding new entities to the ECSS.
        """
        global update_needed

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
            
            self.name = tmp.name;
            self.addNode();
            self.generate(tmp);
            self.shape = None;
            self.selected_parent = None;
            update_needed = True;

            return True;
        
        return False;

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