
import imgui
import Elements.pyECSS.math_utilities as util
from Elements.pyGLV.GUI.Viewer import RenderWindow, ImGUIDecorator
from Elements.pyECSS.Component import BasicTransform

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
                        if imgui.tree_node(comp.name + "##" + str(comp.id), imgui.TREE_NODE_BULLET):
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