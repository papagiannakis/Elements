import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.utils.normals as norm
from Elements.pyGLV.GL.Textures import Texture

from Elements.utils.terrain import generateTerrain
from Elements.definitions import TEXTURE_DIR, SHADER_DIR

from OpenGL.GL import GL_LINES

from Elements.utils.Shortcuts import displayGUI_text

example_description = \
"The same texture mapped six different ways, one per cube face: the UV_MAP below \n\
decides which part of the image each face gets. One face takes the whole image, \n\
one tiles it 2x2, the rest take a single cell out of the 3x3 grid. \n\
Note also that this example's vertex shader is written inline, as a string. \n\
You may move the camera using the mouse or the GUI. \n\
You may see the ECS Scenegraph showing Entities & Components of the scene and \n\
various information about them. Hit ESC OR Close the window to quit."


# A vertex shader given as a string rather than a file -- Shader accepts either.
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
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = myshader, fragment_import_file=SHADER_DIR / "SimpleTexture.frag")))

terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES)) # note the primitive change
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))



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

# One (u, v) per vertex, six vertices per face: where each corner lands on the texture image.
# The first face tiles the whole image once, the second tiles it 2x2, the rest pick one cell each
# out of the 3x3 grid in 3x3.jpg.
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
           windowTitle = "Elements: Textures example", customImGUIdecorator = ImGUIecssDecorator, 
           openGLversion = 4)
scene.world.traverse_visit(initUpdate, scene.world.root)

# ---------------- the window, the GUI and the camera ----------------

gWindow = scene.renderWindow
gGUI = scene.gContext

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
# also stores eye/target/up, which the mouse camera reads and updates
gGUI.createViewMatrix(eye, target, up)

projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)

texturePath = TEXTURE_DIR / "3x3.jpg"
texture = Texture(texturePath)
shaderDec4.setUniformVariable(key='ImageTexture', value=texture, texture=True)

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(transUpdate, scene.world.root)

    view = gWindow._myCamera    # the mouse and the GUI both write here

    axes_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ axes_trans.l2world, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ terrain_trans.l2world, mat4=True)
    shaderDec4.setUniformVariable(key='model', value=trans4.l2world, mat4=True)
    shaderDec4.setUniformVariable(key='View', value=view, mat4=True)
    shaderDec4.setUniformVariable(key='Proj', value=projMat, mat4=True)

    # render after the uniforms are set, so this frame draws with this frame's camera
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()

