from __future__ import annotations
from typing import List
from dataclasses import dataclass
from imgui_bundle import (
    imgui as imgui,
    imgui_node_editor as ed, # type: ignore
)
import Elements.extensions.BasicShapes.BasicShapes as bshapes
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GUI.Viewer import RenderWindow

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator

shapes = {"Cube" : bshapes.CubeSpawn, "Sphere" : bshapes.SphereSpawn, "Cylinder" : bshapes.CylinderSpawn, "Cone" : bshapes.ConeSpawn, "Torus" : bshapes.TorusSpawn};

update_needed = True;

class IdProvider:
    """A simple utility to obtain unique ids, and to be able to restore them at each frame"""

    _next_id: int = 1

    def next_id(self):
        """Gets a new unique id"""
        r = self._next_id
        self._next_id += 1
        return r

    def reset(self):
        """Resets the counter (called at each frame)"""
        self._next_id = 1

ID = IdProvider()

class Node:
    def __init__(self, _name = None, _parent = None):
        if _name is None:
            self.name = "new_node"
        else:
            self.name = _name;
        
        if _parent is None:
            self.parentId = None 
        else:
            self.parentId = _parent;
        
        self.id = ed.NodeId(ID.next_id())
        self.childrenPinId = ed.PinId(ID.next_id())
        self.parentPinId = ed.PinId(ID.next_id())
        self.creation = None;
        self.parent = None;

    
    def display(self):
        """
        Displays a node in the node
        """
        ed.begin_node(self.id)

        imgui.text(self.name)
        ed.begin_pin(self.parentPinId, ed.PinKind.input)
        imgui.text("Parent")
        ed.end_pin()
        imgui.same_line()
        ed.begin_pin(self.childrenPinId, ed.PinKind.output)
        imgui.text("Children")
        ed.end_pin()

        ed.end_node()

@dataclass
class LinkInfo:
    id: ed.LinkId
    input_id: ed.PinId
    output_id: ed.PinId

class NodeEditor:
    is_first_frame: bool = True
    links: List[LinkInfo]
    next_link_id: int = 100

    def __init__(self, wrapee: RenderWindow):
        ID.reset()
        self.wrapee = wrapee;

        self.editor_context = ed.create_editor();
        self.links = []
        self.selected = None
        self.creation = False
        self.nodes = []
        self.nodeAmount = 0;
        self.linkAmount = 0;
        self.name = ""
        self.children = ""
        self.entities = [];
        self.shape = None;
        self.to_add = None;
        self.selected_parent = None;
    
    def addNode(self, node = None):
        """
        Adds a new node to the node list
        
        :param node: [description]
        :type node: Node
        """
        if node is None:
            tmp = Node(self.name)
            if self.selected_parent is not None:
                parent = self.find_parent(self.selected_parent.name);
                if parent:
                    tmp.parent = parent;
                    tmp.parentId = parent.id;
                    self.links.append(LinkInfo(ed.LinkId(ID.next_id()), tmp.parentPinId, parent.childrenPinId))
            else:
                tmp.parentId = self.nodes[0].id
                tmp.parent = self.nodes[0]
                self.links.append(LinkInfo(ed.LinkId(ID.next_id()), tmp.parentPinId, self.nodes[0].childrenPinId))
            self.nodes.append(tmp)
            self.name = ""
        else:
            self.nodes.append(node)

    def remove(self, comp):
        """
        Removes the node correspoding the to component given as a parameter, and its links from the lists
        
        :param comp: [descprition]
        :type comp: Component
        """
        input_id = None;
        output_id = None;
        for node in self.nodes:
            print(node.name)
            if node.name == comp.name:
                input_id = node.parentPinId;
                output_id = node.childrenPinId;
                self.nodes.remove(node)
                break;
        
        i = 0;
        while i < len(self.nodes):
            if self.nodes[i].parent is not None and self.nodes[i].parent.name == comp.name:
                self.nodes.remove(self.nodes[i])
            else:
                i += 1;
        
        i = 0;
        while i < len(self.links):
            if self.links[i].input_id == output_id or self.links[i].output_id == input_id:
                self.links.remove(self.links[i])
            else:
                i += 1;

    
    def findNodeByName(self, name):
        """
        Finds and returns a node by the name given as a parameter, if not found it returns None

        :param name: [description]
        :type name: str
        """
        for node in self.nodes:
            if name == node.name:
                return node
        return None

    def createLink(self, parent, child):
        """
        Creates and appends a new link to the editor

        :param parent: [description]
        :type parent: LinkId
        :param child: [description]
        :type child: LinkId
        """
        self.links.append(LinkInfo(ed.LinkId(ID.next_id()), child.parentPinId, parent.childrenPinId))
    
    def display_nodes(self):
        """
        Displays all the nodes in the editor (Callback).
        """
        for node in self.nodes:
            node.display()

    def generate(self, component):
        """
        Generates the nodes and the links and appends them to the editor.
        Used for first time run and for any updates, should any occur in the ECSS.
        Recursive function, beginning from the given component

        :param component: [description]
        :type component: Component
        """
        if component._children is not None:
            debugIterator = iter(component._children)
            done_traversing = False
            while not done_traversing:
                try:
                    comp = next(debugIterator)
                except StopIteration:
                    done_traversing = True
                else:
                    tmp = Node(comp.name)
                    parent = self.findNodeByName(comp._parent.name)
                    if parent is not None:
                        tmp.parentId = parent.id
                        self.createLink(parent, tmp)
                        tmp.parent = parent;
                    self.addNode(tmp)
                    self.generate(comp)
        
        self.nodeAmount = len(self.nodes);
        self.linkAmount = len(self.links);

    def createMode(self):
        """
        Performs all actions of the create mode of the editor.
        """
        input_pin_id = ed.PinId()
        output_pin_id = ed.PinId()

        if ed.query_new_link(input_pin_id, output_pin_id):
            parent = None;
            child  = None;
            if input_pin_id and output_pin_id and input_pin_id != output_pin_id:
                flip = False;
                for node in self.nodes:
                    if parent is None and (input_pin_id == node.childrenPinId or output_pin_id == node.childrenPinId):
                        parent = node;
                        if output_pin_id == node.childrenPinId:
                            flip = True;
                        continue;
                    
                    if child is None and (output_pin_id == node.parentPinId or input_pin_id == node.parentPinId):
                        child = node;
                        child_node = node;
                
                    if parent and child:
                        break;

                parent = self.wrapee.scene.world.getEntityByName(parent.name);
                child = self.wrapee.scene.world.getEntityByName(child.name);

                old_parent = self.findNodeByName(child.parent.name)

                if ed.accept_new_item():
                    link_info = None;
                    if flip:
                        link_info = LinkInfo(
                            ed.LinkId(self.next_link_id), output_pin_id, input_pin_id
                        )
                    else:
                        link_info = LinkInfo(
                            ed.LinkId(self.next_link_id), input_pin_id, output_pin_id
                        )
                        
                    if self.wrapee.scene.world.changeEntityParent(child, parent):
                        self.next_link_id += 1
                        self.links.append(link_info)

                        # Draw new link.
                        ed.link(
                            self.links[-1].id,
                            self.links[-1].input_id,
                            self.links[-1].output_id,
                        )

                        print(old_parent.name, child_node.name);
                        for link in self.links:
                            if ((link.output_id == old_parent.childrenPinId and link.input_id == child_node.parentPinId) or
                                (link.input_id == old_parent.childrenPinId and link.output_id == child_node.parentPinId)): 
                                self.links.remove(link)
                                break;

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

    def on_frame(self):
        """
        Main loop of the editor
        """
        if self.to_add is not None:
            self.wrapee.scene.world.addEntityChild(self.wrapee.scene.world.root, self.to_add); 
            self.to_add = None;


        ed.set_current_editor(self.editor_context); 
        ed.begin("My Editor", imgui.ImVec2(0.0, 0.0))

        self.display_nodes()
        
        for linkInfo in self.links:
            ed.link(linkInfo.id, linkInfo.input_id, linkInfo.output_id)

        if ed.begin_create():
            self.createMode();
            ed.end_create() 
            
        if ed.begin_delete():

            deleted_link_id = ed.LinkId()
            while ed.query_deleted_link(deleted_link_id):

                if ed.accept_deleted_item():
  
                    for link in self.links:
                        if link.id == deleted_link_id:
                            self.links.remove(link)
                            break

            ed.end_delete()

        ed.end()


        if self.is_first_frame:
            ed.navigate_to_content(0.0)

        self.is_first_frame = False