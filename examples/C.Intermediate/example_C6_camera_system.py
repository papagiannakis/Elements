"""
The Camera System: a camera that lives in the scenegraph as an Entity, rather than a view matrix
built by hand with util.lookat().

CameraSystem walks the graph and hands every object an l2cam matrix -- its own place in the world,
already expressed from the camera's point of view -- so the render loop below feeds l2cam straight
to modelViewProj and never touches a view or projection matrix itself.
"""

from __future__ import annotations

import numpy as np
import OpenGL.GL as gl
from OpenGL.GL import GL_LINES

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh

from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera
from Elements.utils.terrain import generateTerrain
from Elements.utils.normals import Convert

from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR

example_description = \
"This is the first examples that demonstrates the usage of the Camera System \n\
instead of the use of the lookAt function to create the view matrix. \n\
You may move the camera using the mouse or the Scenegraph GUI. \n\n\
NOTE: To change any TRS via the Scenegraph GUI, only this TRS must be toggled on!\n\n\
You may see the ECS Scenegraph showing Entities & Components of the scene and \n\
various information about them. Hit ESC OR Close the window to quit."


class GameObjectEntity(Entity):
    """An Entity that carries its own transform, mesh, shader and vertex array."""

    def __init__(self, name=None, type=None, id=None) -> None:
        super().__init__(name, type, id);

        # Gameobject basic properties
        self._color          = [1, 0.5, 0.2, 1.0]; # this will be used as a uniform var
        # Create basic components of a primitive object
        self.trans          = BasicTransform(name="trans", trs=util.identity());
        self.mesh           = RenderMesh(name="mesh");
        self.shaderDec      = ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag"));
        self.vArray         = VertexArray();
        # Add components to entity
        scene = Scene();
        scene.world.createEntity(self);
        scene.world.addComponent(self, self.trans);
        scene.world.addComponent(self, self.mesh);
        scene.world.addComponent(self, self.shaderDec);
        scene.world.addComponent(self, self.vArray);

    @property
    def color(self):
        return self._color;
    @color.setter
    def color(self, colorArray):
        self._color = colorArray;

    def drawSelfGui(self, imgui):
        changed, value = imgui.color_edit3("Color", self.color[0], self.color[1], self.color[2]);
        self.color = [value[0], value[1], value[2], 1.0];

    def SetVertexAttributes(self, vertex, color, index, normals = None):
        self.mesh.vertex_attributes.append(vertex);
        self.mesh.vertex_attributes.append(color);
        if normals is not None:
            self.mesh.vertex_attributes.append(normals);
        self.mesh.vertex_index.append(index);



def CubeSpawn(cubename = "Cube"): 
    cube = GameObjectEntity(cubename);
    vertices = [
        [-0.5, -0.5, 0.5, 1.0],
        [-0.5, 0.5, 0.5, 1.0],
        [0.5, 0.5, 0.5, 1.0],
        [0.5, -0.5, 0.5, 1.0], 
        [-0.5, -0.5, -0.5, 1.0], 
        [-0.5, 0.5, -0.5, 1.0], 
        [0.5, 0.5, -0.5, 1.0], 
        [0.5, -0.5, -0.5, 1.0]
    ];
    colors = [
        [1.0, 0.0, 0.0, 1.0],
        [1.0, 0.5, 0.0, 1.0],
        [1.0, 0.0, 0.5, 1.0],
        [0.5, 1.0, 0.0, 1.0],
        [0.0, 1.0, 1.5, 1.0],
        [0.0, 1.0, 1.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0]                    
    ];
    # OR, for a single flat colour:
    # colors =  [cube.color] * len(vertices)

    #which corners each triangle joins: 6 faces, 2 triangles each
    indices = np.array(
        (
            1,0,3, 1,3,2,
            2,3,7, 2,7,6,
            3,0,4, 3,4,7,
            6,5,1, 6,1,2,
            4,5,6, 4,6,7,
            5,4,0, 5,0,1
        ),
        dtype=np.uint32
    )

    vertices, colors, indices, normals = Convert(vertices, colors, indices, produceNormals=True);
    cube.SetVertexAttributes(vertices, colors, indices, normals);
    
    return cube;




def main(imguiFlag = False):
    # A complete ECSS: Entities, Components, Camera, Shader, VertexArray and RenderMesh

    winWidth = 1024
    winHeight = 1024

    scene = Scene()

    # Initialize Systems used for this script
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())
    
    # Scenegraph with Entities, Components
    rootEntity = scene.world.createEntity(Entity(name="Root"))

    # The camera is an Entity under the root, with two nested transforms: trans2 pulls it back
    # from what it orbits, trans1 turns it. Its name is what the GUI looks for to drive it.
    mainCamera = SimpleCamera("Simple Camera")
    mainCamera.trans2.trs = util.translate(0, 0, 8) # VIEW
    mainCamera.trans1.trs = util.rotate((1, 0, 0), -45);

    #-----------------------------------------
    # Spawn Two Homes on top of each other
    home1 = scene.world.createEntity(Entity("Home"))
    scene.world.addEntityChild(rootEntity, home1)

    trans = BasicTransform(name="trans", trs=util.identity());    
    scene.world.addComponent(home1, trans)
    
    cube_bot: GameObjectEntity = CubeSpawn("BOT CUBE")
    scene.world.addEntityChild(home1, cube_bot)
    
    cube_top: GameObjectEntity = CubeSpawn()
    scene.world.addEntityChild(home1, cube_top)
    
    home1.getChild(0).trs = util.translate(0, 0, 0)
    cube_top.trans.trs = util.translate(0, 1, 0)
    cube_top.name = "TOP CUBE"
    
    
    # ---------------------------
    # Generate terrain

    vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size=4, N=20)
    # Add terrain
    terrain = scene.world.createEntity(Entity(name="terrain"))
    scene.world.addEntityChild(rootEntity, terrain)
    terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))

    terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
    terrain_mesh.vertex_attributes.append(vertexTerrain)
    terrain_mesh.vertex_attributes.append(colorTerrain)
    terrain_mesh.vertex_index.append(indexTerrain)

    terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(
        Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))
    
    scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))

    # MAIN RENDERING LOOP
    running = True
    scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight, windowTitle = "Elements: A CameraSystem Example", customImGUIdecorator = ImGUIecssDecorator2)

    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glDisable(gl.GL_CULL_FACE);
    gl.glEnable(gl.GL_DEPTH_TEST);
    gl.glDepthFunc(gl.GL_LESS);

    # pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
    # needs an active GL context
    scene.world.traverse_visit(initUpdate, rootEntity)

    # ---------------- the window, the GUI and the camera ----------------

    gWindow = scene.renderWindow    # the SDL2 window: the pixels, the mouse and the keyboard
    gGUI = scene.gContext           # the ImGUI layer wrapped around it

    # No gGUI.createViewMatrix() here, unlike the other examples: the GUI finds mainCamera by name
    # (any root child with "camera" in it) and drags mainCamera.trans1.trs directly, so there is no
    # eye/target pair to seed and gWindow._myCamera is never read below.

    while running:

        scene.world.traverse_visit(transUpdate, scene.world.root)
        # the camera's own branch first, so l2cam is ready when the rest of the graph is visited
        scene.world.traverse_visit_pre_camera(camUpdate, mainCamera.camera)
        scene.world.traverse_visit(camUpdate, scene.world.root)

        # l2cam is already model @ view @ projection -- no matrix multiplication needed here
        home1.getChild(1).shaderDec.setUniformVariable(key='modelViewProj', value=home1.getChild(1).trans.l2cam, mat4=True);
        home1.getChild(2).shaderDec.setUniformVariable(key='modelViewProj', value=home1.getChild(2).trans.l2cam, mat4=True);
        home1.getChild(1).shaderDec.setUniformVariable(key='my_color;', value=[0.4, 0.4, 0.4, 1.0], float4=True);

        terrain_shader.setUniformVariable(key='modelViewProj', value=terrain_trans.l2cam, mat4=True);

        # call SDLWindow/ImGUI display() and ImGUI event input process
        running = scene.render()
        displayGUI_text(example_description)
        # call the GL State render System
        scene.world.traverse_visit(renderUpdate, scene.world.root)
        # ImGUI post-display calls and SDLWindow swap
        scene.render_post()

    scene.shutdown()


if __name__ == "__main__":    
    main(imguiFlag = True)
