import numpy as np
import os

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform,  Camera, RenderMesh
from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import IMGUIecssDecoratorBundle

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.utils.normals as norm
from Elements.pyGLV.GL.Textures import Texture

from Elements.utils.terrain import generateTerrain
from Elements.definitions import TEXTURE_DIR

from OpenGL.GL import GL_LINES

from Elements.utils.Shortcuts import displayGUI_text

example_description = \
"This example demonstrates the ability to apply image textures to geometry. \n\
You may move the camera using the mouse or the GUI. \n\
You may see the ECS Scenegraph showing Entities & Components of the scene and \n\
various information about them. Hit ESC OR Close the window to quit." 


myshader =  """
        #version 410

        layout (location=0) in vec4 vPos;
        layout (location=1) in vec2 vTexCoord;

        out vec2 fragmentTexCoord;

        uniform mat4 model;
        uniform mat4 View;
        uniform mat4 Proj;

        void main()
        {
            gl_Position =  Proj * View * model * vPos;
            fragmentTexCoord = vTexCoord;
        }
    """


winWidth = 1024
winHeight = 768
scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.translate(0,0.5,0)@util.scale(0.7))) #util.identity()
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))
vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = myshader, fragment_source=Shader.SIMPLE_TEXTURE_FRAG)))

terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES)) # note the primitive change
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))



# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())




## ADD AXES: RenderMesh attributes ##
vertexAxes = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0] ],dtype=np.float32) 
colorAxes = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0] ], dtype=np.float32)
indexAxes = np.array((0,1,2,3,4,5), np.uint32) #3 simple colored Axes as R,G,B lines
axes_mesh.vertex_attributes.append(vertexAxes) 
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)

## ADD SIMPLE CUBE : RenderMesh attributes ##
vertexCube = np.array([
    [-1, -1,  1, 1.0],
    [-1,  1,  1, 1.0],
    [ 1,  1,  1, 1.0],
    [ 1, -1,  1, 1.0], 
    [-1, -1, -1, 1.0], 
    [-1,  1, -1, 1.0], 
    [ 1,  1, -1, 1.0], 
    [ 1, -1, -1, 1.0] ],dtype=np.float32)

indexCube = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) #rhombus out of two triangles

vertices, indices, _ = norm.generateUniqueVertices(vertexCube,indexCube)

UV_MAP = [ 
    [0.0, 1], [0.0, 0.0], [1, 0.0], [0.0, 1], [1, 0.0], [1, 1],
    [0.0, 2], [0.0, 0.0], [2, 0.0], [0.0, 2], [2, 0.0], [2, 2],
    [0.0, 2/3], [0.0, 1/3], [1/3, 1/3], [0.0, 2/3], [1/3, 1/3], [1/3, 2/3],
    [1/3, 3/3], [1/3, 2/3], [2/3, 2/3], [1/3, 3/3], [2/3, 2/3], [2/3, 3/3],
    [2/3, 1/3], [2/3, 0.0], [3/3, 0.0], [2/3, 1/3], [3/3, 0.0], [3/3, 1/3],
    [0.0, 3/3], [0.0, 2/3], [1/3, 2/3], [0.0, 3/3], [1/3, 2/3], [1/3, 3/3],
    ] 

mesh4.vertex_attributes.append(vertices)
mesh4.vertex_attributes.append(UV_MAP)
mesh4.vertex_index.append(indices)


## ADD TERRAIN : RenderMesh attributes ##
vertexTerrain, indexTerrain, colorTerrain= generateTerrain(size=4,N=20)
terrain_mesh.vertex_attributes.append(vertexTerrain) 
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)




# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight, 
           windowTitle = "Elements: Textures example 2", customImGUIdecorator = IMGUIecssDecoratorBundle, 
           openGLversion = 4)
scene.world.traverse_visit(initUpdate, scene.world.root)

################### EVENT MANAGER - START ###################

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext
renderGLEventActuator = RenderGLStateSystem()
eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow 
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

################### EVENT MANAGER - END ###################

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)

projMat = util.perspective(50.0, 1.0, 0.01, 100.0)   

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update

texturePath = TEXTURE_DIR / "3x3.jpg"
texture = Texture(texturePath)
shaderDec4.setUniformVariable(key='ImageTexture', value=texture, texture=True)


while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(transUpdate, scene.world.root)
    view =  gWindow._myCamera # updates view via the imgui
    mvp_terrain_axes = projMat @ view @ terrain.getChild(0).l2world 

    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    shaderDec4.setUniformVariable(key='model', value=trans4.l2world, mat4=True)
    shaderDec4.setUniformVariable(key='View', value=view, mat4=True)
    shaderDec4.setUniformVariable(key='Proj', value=projMat, mat4=True)
    
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()
    
scene.shutdown()

