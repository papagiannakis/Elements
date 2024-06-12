from __future__ import annotations
from typing import List
from dataclasses import dataclass
from imgui_bundle import (
    imgui as imgui,
    imgui_node_editor as ed, # type: ignore
)
import Elements.extensions.BasicShapes.BasicShapes as bshapes
import numpy as np
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import Component
from Elements.pyGLV.GUI.Viewer import RenderWindow
from Elements.definitions import EDITOR_CONFIG_DIR, IMAGE_DIR
import OpenGL.GL as gl
from PIL import Image

shapes = {"Cube" : bshapes.CubeSpawn, "Sphere" : bshapes.SphereSpawn, "Cylinder" : bshapes.CylinderSpawn, "Cone" : bshapes.ConeSpawn, "Torus" : bshapes.TorusSpawn};

update_needed = True;
rounding = 5.0;
padding  = 12.0;

first_run = False;
frame_counter = 0;
arrow_texture_id = None;

def generate_image():
    arrow_image = Image.open(IMAGE_DIR / "arrow.png")
    arrow_image_data = np.array(arrow_image.convert("RGBA"))

    arrow_texture_id = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, arrow_texture_id)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, arrow_image.width, arrow_image.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, arrow_image_data)
    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

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
    def __init__(self, _name = None, _parent = None, _type = None):
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
        self.type = _type;
    
        if first_run:
            generate_image();

    
    def display(self):
        """
        Displays a node in the node
        """
        global padding, rounding
        ed.push_style_var(ed.StyleVar.node_rounding, rounding);

        if self.type == "Root":
            ed.push_style_color(ed.StyleColor.node_bg, imgui.ImVec4(1, 0, 0, 0.5));
        elif self.type == "Entity":
            ed.push_style_color(ed.StyleColor.node_bg, imgui.ImVec4(0, 0.5, 0.5, 0.5));
        elif self.type == "Component":
            ed.push_style_color(ed.StyleColor.node_bg, imgui.ImVec4(0.5, 0.5, 0, 0.5));
        
        ed.push_style_color(ed.StyleColor.node_border, imgui.ImVec4(1, 1, 1, 1));
        ed.push_style_color(ed.StyleColor.pin_rect, imgui.ImVec4(60, 180, 255, 150));
        ed.push_style_color(ed.StyleColor.pin_rect_border, imgui.ImVec4( 60, 180, 255, 150));
        
        ed.begin_node(self.id)

        imgui.text_unformatted(self.name);

        ed.begin_pin(self.parentPinId, ed.PinKind.input)
        # imgui.image(arrow_texture_id, imgui.ImVec2(10, 10));
        # imgui.same_line()
        imgui.text("Parent")
        ed.end_pin()
        imgui.same_line()
        
        ed.begin_pin(self.childrenPinId, ed.PinKind.output)
        imgui.text("Children")
        # imgui.same_line()
        # imgui.image(arrow_texture_id, imgui.ImVec2(10, 10));
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

    def __init__(self, wrapee: RenderWindow, exampleName):
        ID.reset()
        self.wrapee = wrapee;
        self.config = ed.Config();
        self.config.settings_file = str(EDITOR_CONFIG_DIR / (exampleName + ".json"))
        self.editor_context = ed.create_editor(self.config);
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
        self.highlighted = None;
    
    def addNode(self, comp = None, child = None):
        """
        Adds a new node to the node list
        
        :param node: [description]
        :type node: Node
        """
        if comp is None:
            tmp = Node(self.name)
            if self.selected_parent is not None:
                parent = self.findNodeByName(self.selected_parent.name);
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
            comp_type = None;
            if isinstance(comp, Entity):
                comp_type = "Entity";
            elif isinstance(comp, Component):
                comp_type = "Component";
            else:
                comp_type = "Root";

            tmp = Node(comp.name, _type = comp_type);
            if comp.parent:
                parent = self.findNodeByName(comp.parent.name)
                if parent is not None:
                    tmp.parentId = parent.id
                    # pos = ed.get_node_position(parent.id)
                    # children = len(comp.parent._children)
                    # pos_y = pos.y - (10 * children / 2)
                    # if child:
                    #     ed.set_node_position(tmp.id, imgui.ImVec2(pos.x + 20, pos_y + (10 * child)))
                    self.createLink(parent, tmp)
                    tmp.parent = parent;
            self.nodes.append(tmp);

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
            child = 0
            while not done_traversing:
                try:
                    comp = next(debugIterator)
                except StopIteration:
                    done_traversing = True
                else:
                    self.addNode(comp, child)
                    child += 1;
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
    
    def set_node_positions(self):
        pass


    def on_frame(self, update = False):
        """
        Main loop of the editor
        """
        global frame_counter;
        ed.set_current_editor(self.editor_context); 
        ed.begin("ECSS Node Editor", imgui.ImVec2(0.0, 0.0))
        self.display_nodes()

        found = False;
        changed = False;
        for node in self.nodes:
            if ed.is_node_selected(node.id):
                found = True;
                if self.highlighted != node:
                    changed = True;
                    self.highlighted = node;
        
        if not found:
            self.highlighted = None;
        
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

        if frame_counter < 30:
            ed.navigate_to_content()
            frame_counter += 1;
        else:
            ed.navigate_to_selection(False);

        return changed, self.highlighted;