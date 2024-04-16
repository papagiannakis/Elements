from __future__ import annotations
from typing import List
from dataclasses import dataclass
from imgui_bundle import (
    imgui as imgui,
    imgui_node_editor as ed,
)
import Elements.extensions.BasicShapes.BasicShapes as bshapes

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator

shapes = {"Cube" : bshapes.CubeSpawn, "Sphere" : bshapes.SphereSpawn, "Cylinder" : bshapes.CylinderSpawn, "Cone" : bshapes.ConeSpawn, "Torus" : bshapes.TorusSpawn};


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

    def __init__(self):
        ID.reset()
        self.config = None;
        self.editor_context = ed.create_editor();
        self.links = []
        self.selected = None
        self.creation = False
        self.nodes = []
        self.name = ""
        self.children = ""
        self.shape = None;
        self.to_add = None;
     
    def addNode(self, node = None):
        if node is None:
            tmp = Node(self.name)
            tmp.parentId = self.nodes[0].id
            self.links.append(LinkInfo(ed.LinkId(ID.next_id()), tmp.parentPinId, self.nodes[0].childrenPinId))
            self.nodes.append(tmp)
            self.name = ""
        else:
            self.nodes.append(node)

    def find_parent(self, name):
        for node in self.nodes:
            if name == node.name:
                return node
        return None

    def createLink(self, parent, child):
        self.links.append(LinkInfo(ed.LinkId(ID.next_id()), child.parentPinId, parent.childrenPinId))
    
    def display_nodes(self):
        for node in self.nodes:
            node.display()

    def generate(self, component):
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
                    parent = self.find_parent(comp._parent.name)
                    if parent is not None:
                        tmp.parentId = parent.id
                        self.createLink(parent, tmp)
                    self.addNode(tmp)
                    self.generate(comp) 


    def on_frame(self):
        if self.to_add is not None:
            from Elements.pyGLV.GL.Scene import Scene
            scene = Scene(); 
            scene.world.addEntityChild(scene.world.root, self.to_add); 
            self.to_add = None;


        ed.set_current_editor(self.editor_context); 
        ed.begin("My Editor", imgui.ImVec2(0.0, 0.0))

        self.display_nodes()
        
        for linkInfo in self.links:
            ed.link(linkInfo.id, linkInfo.input_id, linkInfo.output_id)

        if ed.begin_create():
            input_pin_id = ed.PinId()
            output_pin_id = ed.PinId()

            if ed.query_new_link(input_pin_id, output_pin_id):


                if input_pin_id and output_pin_id: 
                    if ed.accept_new_item():

                        link_info = LinkInfo(
                            ed.LinkId(self.next_link_id), input_pin_id, output_pin_id
                        )
                        self.next_link_id += 1
                        self.links.append(link_info)

                        # Draw new link.
                        ed.link(
                            self.links[-1].id,
                            self.links[-1].input_id,
                            self.links[-1].output_id,
                        )

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

    def entity_window(self):
        imgui.text("Name: "); imgui.same_line()
        _, self.name = imgui.input_text(' ', self.name)

        imgui.separator_text("Shape");
        for shape in shapes.keys():
            _ ,selected = imgui.selectable(shape, self.shape is not None and self.shape == shape)
            if selected:
                self.shape = shape

        if imgui.button("Add"):
            from Elements.pyGLV.GL.Scene import Scene
            scene = Scene(); 
            print(scene.world.root)
            if self.name is "":
                tmp = shapes[self.shape]();
            else:
                tmp = shapes[self.shape](self.name);
            
            self.name = tmp.name;
            self.addNode();
            self.generate(tmp);
            self.shape = None;

            return tmp;
        
        return False;
        


        