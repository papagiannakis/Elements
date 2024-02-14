import numpy as np
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Textures import Texture
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator
import imgui
import Elements.extensions.usd.UsdImporter as SceneLoader
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from OpenGL.GL import GL_LINES
import OpenGL.GL as gl

from Elements.utils.terrain import generateTerrain
from Elements.definitions import SCENES_DIR

from Elements.utils.Shortcuts import displayGUI_text
example_description = \
"This example demonstrates the ability to import \n\
basic USD files. By pressing the button load scene \n\
on a blank scene, the default usd is loaded and \n\
3 yellow cubes are imported in the scene. You can choose to \n\
import the usd file of your choice, by inputing the \n\
appropriate filepath in the text box. Pressing \n\
button save scene the current scene is saved in usd format file."

models = []
newShaders = []

USD_input_filepath = SCENES_DIR / "ExampleScene.usd"
USD_input_filepath = str(USD_input_filepath) # this is required for the imgui input_text function, possix.path -> str

def SceneGUI(scene, initUpdate):
    global USD_input_filepath
    global newShaders
    imgui.begin("Scene")

    changed, USD_input_filepath = imgui.input_text(label="filepath", buffer_length=400,
                                                   flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE, value=USD_input_filepath)
    if imgui.button('Save Current Scene'):
        SceneLoader.SaveScene(scene, USD_input_filepath)
        print('Scene Saved to ', USD_input_filepath)
    if imgui.button('Load USD Scene'):
        newShaders = SceneLoader.LoadScene(scene, USD_input_filepath)
        scene.world.traverse_visit(initUpdate, scene.world.root)
        print('Scene loaded from ', USD_input_filepath)
    imgui.end()
    return scene


# Light
Lposition = util.vec(-1, 1.5, 1.2)  # uniform lightpos
Lambientcolor = util.vec(1.0, 1.0, 1.0)  # uniform ambient color
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 40.0

scene = Scene()

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))



# light_node = scene.world.createEntity(Entity(name="LightPos"))
# scene.world.addEntityChild(rootEntity, light_node)
# light_transform = scene.world.addComponent(light_node, BasicTransform(name="Light_TRS", trs=util.scale(1.0, 1.0, 1.0)))

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())


# Light Visualization
# a simple tetrahedron
tetrahedron_vertices = np.array([
    [1.0, 1.0, 1.0, 1.0],
    [-1.0, -1.0, 1.0, 1.0],
    [-1.0, 1.0, -1.0, 1.0],
    [1.0, -1.0, -1.0, 1.0]
], dtype=np.float32)
tetrahedron_colors = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0]
])
tetrahedron_indices = np.array([0, 2, 1, 0, 1, 3, 2, 3, 1, 3, 2, 0])

# light_vArray = scene.world.addComponent(light_node, VertexArray())
# light_shader_decorator = scene.world.addComponent(light_node, ShaderGLDecorator(
#     Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

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
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(
    Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

## ADD AXES ##
# Colored Axes
vertexAxes = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.5, 0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 1.5, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.5, 1.0]
], dtype=np.float32)
colorAxes = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
], dtype=np.float32)

# index arrays for above vertex Arrays
index = np.array((0, 1, 2), np.uint32)  # simple triangle
indexAxes = np.array((0, 1, 2, 3, 4, 5), np.uint32)  # 3 simple colored Axes as R,G,B lines

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans",
                                                           trs=util.translate(0.0, 0.00001, 0.0)))  # util.identity()
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes)
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=gl.GL_LINES))  # note the primitive change

axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(
    Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

# MAIN RENDERING LOOP
running = True
scene.init(imgui=True, windowWidth=1200, windowHeight=800, windowTitle="Elements: Import wavefront .obj example",
           openGLversion=4, customImGUIdecorator=ImGUIecssDecorator)

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

################### EVENT MANAGER ###################

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

renderGLEventActuator = RenderGLStateSystem()

eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, 1200 / 800, 0.01, 100.0)  ## WORKING

gWindow._myCamera = view  # otherwise, an imgui slider must be moved to properly update

model_terrain_axes = util.translate(0.0, 0.0, 0.0)

White_Map = (b'\xff\xff\x00\xff', 1, 1)
#q : what does the above line do?
#a: it creates a white texture map, with 1 pixel, 1 channel, 1 byte per channel
# q: what is the purpose of this?
# a: it is used as a default texture map for the shader, so that the shader can be used without a texture map
# q: what if I wanted a different color?
# a: you can change the color by changing the first argument of the tuple, which is a byte string
# q: what is the byte string for blue?
# a: b'\x00\x00\xff\xff'
while running:
    running = scene.render()
    displayGUI_text(example_description)
    SceneGUI(scene, initUpdate)
    scene.world.traverse_visit(transUpdate, scene.world.root)
    view = gWindow._myCamera  # updates view via the imgui
    # mvp_cube = projMat @ view @ model_cube
    try:  # if light is not in the scene, this will throw an error
        light_shader_decorator.setUniformVariable(key="modelViewProj", value=projMat @ view @ (
            util.translate(Lposition[0], Lposition[1], Lposition[2]) @ util.scale(1, 1, 1)), mat4=True)
    except:
        pass
    mvp_terrain = projMat @ view @ terrain_trans.l2world
    mvp_axes = projMat @ view @ axes_trans.l2world
    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)

    # Set Object Real Time Shader Data
    for shader in newShaders:
        model_cube = shader.parent.getChildByType(BasicTransform.getClassName()).l2world
        # --- Set vertex shader data ---
        shader.setUniformVariable(key='projection', value=projMat, mat4=True)
        shader.setUniformVariable(key='view', value=view, mat4=True)
        shader.setUniformVariable(key='model', value=model_cube, mat4=True)

        # --- Set fragment shader data ---
        normalMatrix = np.transpose(util.inverse(model_cube))
        shader.setUniformVariable(key='normalMatrix', value=normalMatrix, mat4=True)

        shader.setUniformVariable(key='albedoColor', value=np.array([100,100,100,0]), float3=True)
        texture = Texture(img_data=White_Map, texture_channel=0)

        shader.setUniformVariable(key='lightPos', value=Lposition, float3=True)
        shader.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
        shader.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)

        # Camera position
        shader.setUniformVariable(key='camPos', value=eye, float3=True)
    
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()


scene.shutdown()
