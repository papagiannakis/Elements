from __future__ import annotations
from typing import List
from dataclasses import dataclass
from imgui_bundle import (
    imgui,
    imgui_node_editor as ed,
)
import imgui as gui
from imgui_bundle.immapp import static, run_anon_block



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

kf0 = [0,0,0,0,0,0]
class DemoNodeEditor:
    is_first_frame: bool = True
    links: List[LinkInfo]
    next_link_id: int = 100

    def __init__(self):
        ID.reset()
        self.links = []
        self.selected = None
        self.creation = False
        self.nodes = []
        self.nodes.append(Node("test1"))
        self.nodes.append(Node("test2"))
        self.links.append(LinkInfo(ed.LinkId(ID.next_id()), self.nodes[1].parentPinId, self.nodes[0].childrenPinId))
        self.name = ""
        self.parent = None
        self.children = ""
        
    
    def addNode(self):
        tmp = Node(self.name)
        if self.parent is not None:
            for node in self.nodes:
                if node.name == self.parent.name:
                    tmp.parentId = node.id
                    self.links.append(LinkInfo(ed.LinkId(ID.next_id()), tmp.parentPinId, node.childrenPinId))
        self.nodes.append(tmp)
        self.name = ""
        self.parent = None


    def display_nodes(self):
        for node in self.nodes:
            node.display()
            
    

    def on_frame(self):
        
        if imgui.is_key_pressed(imgui.Key.n) or self.creation:
            self.creation = True
            imgui.begin("Create Entity")
            imgui.text("Name: "); imgui.same_line()
            _, self.name = imgui.input_text(' ', self.name)
            
            imgui.text("Select Parent:")
            for node in self.nodes:
                _ ,selected = imgui.selectable(node.name, ( self.parent is not None and node.name == self.parent.name))
                if selected:
                    self.parent = node
            
            if imgui.button("Add") :
                self.addNode()
                self.creation = False
                
            if imgui.button("check"):
                print(self.parent.name)
            imgui.end()

        imgui.begin("Editor")
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
        imgui.end()

        if self.is_first_frame:
            ed.navigate_to_content(0.0)

        self.is_first_frame = False



@static(demo_node_editor=None)
def demo_gui():
    statics = demo_gui
    if statics.demo_node_editor is None:
        statics.demo_node_editor = DemoNodeEditor()
    statics.demo_node_editor.on_frame()
    
    
def main():
    import os

    this_dir = os.path.dirname(__file__)
    config = ed.Config()
    config.settings_file = this_dir + "/demo_node_editor_basic.json"
    from imgui_bundle import immapp

    immapp.run(
        demo_gui,
        with_node_editor_config=config,
        with_markdown=True,
        window_size=(800, 600),
    )


if __name__ == "__main__":
    main()
