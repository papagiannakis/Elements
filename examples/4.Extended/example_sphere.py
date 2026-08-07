import sys
import numpy as np
import imgui

from Elements.extensions.BasicShapes import BasicShapes

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.pyGLV.GL.Textures import Texture

from Elements.definitions import TEXTURE_DIR
import Elements.extensions.Normals_USDimporter_BSP.normals as norm
from Elements.utils.Shortcuts import displayGUI_text

example_description = \
"This is a scene with a procedurally generated sphere, textured to represent \n\
the Earth. This example demonstrates per-vertex normal computation, with \n\
both smooth and flat shading, and an option to visualize normals as vertex \n\
colors, toggled live via the 'Sphere Options' GUI panel. \n\
You may move the camera using the mouse or the GUI. \n\
Hit ESC OR Close the window to quit."


#SPHERE taken from basic shapes
def generate_sphere(radius=1.0, num_latitude=20, num_longitude=20, perturbation = 0.0):
    color = [1.0, 1.0, 1.0, 1.0]
    vertices = []
    colors = []
    indices = []
    normals = []

    for i in range(num_latitude + 1):
        for j in range(num_longitude + 1):
            theta = (j / num_longitude) * (2 * np.pi)
            phi = (i / num_latitude) * np.pi

            x = radius * np.cos(theta) * np.sin(phi)
            y = radius * np.sin(theta) * np.sin(phi)
            z = radius * np.cos(phi)

            if perturbation == 0.0:
                vertices.append([x, y, z, 1.0])
            else:
                perturbation_vector = 0.02*np.random.normal(0, perturbation, 3)
                vertices.append([x + perturbation_vector[0], y + perturbation_vector[1], z + perturbation_vector[2], 1.0])

            colors.append([168/255, 168/255 , 210/255, 1.0])
            normals.append([x, y, z])

    for i in range(num_latitude):
        for j in range(num_longitude):
            first = i * (num_longitude + 1) + j
            second = first + num_longitude + 1

            indices.extend([first, second, first + 1])
            indices.extend([second, second + 1, first + 1])

    return (
        np.array(vertices, dtype=np.float32),
        np.array(colors, dtype=np.float32),
        np.array(indices, dtype=np.uint32),
        np.array(normals, dtype=np.float32),
    )

#Light
Lposition = util.vec(2.0, 5.5, 2.0) #uniform lightpos
Lambientcolor = util.vec(1.0, 1.0, 1.0) #uniform ambient color
Lambientstr = 0.3 #uniform ambientStr
LviewPos = util.vec(2.5, 2.8, 5.0) #uniform viewpos
Lcolor = util.vec(1.0,1.0,1.0)
Lintensity = 0.8
#Material
Mshininess = 0.4 
Mcolor = util.vec(0, 0, 0)

winWidth = 1200
winHeight = 800

# initial UI state
shading_idx = 0   # 0 = smooth
show_normals_as_color = False

scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="Entity1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="Entity1_TRS", trs=util.translate(0,0,-8)))

eye = util.vec(1, 0.54, 1.0)
target = util.vec(0.02, 0.14, 0.217)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
# projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)  
# projMat = util.perspective(90.0, 1.33, 0.1, 100)  
projMat = util.perspective(50.0, 1.0, 1.0, 10.0)   

m = np.linalg.inv(projMat @ view)


entityCam2 = scene.world.createEntity(Entity(name="Entity_Camera"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="Camera_TRS", trs=util.identity()))
# orthoCam = scene.world.addComponent(entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))
orthoCam = scene.world.addComponent(entityCam2, Camera(m, "orthoCam","Camera","500"))

node4 = scene.world.createEntity(Entity(name="Earth"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="Earth_TRS", trs=util.scale(0.3)@util.translate(0,0.5,0) ))
mesh4 = scene.world.addComponent(node4, RenderMesh(name="Earth_mesh"))


# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# # #POint light
# pointLight = BasicShapes.PointLight()
# pointLight.trans.trs = util.translate(0.8, 1, 1)@util.scale(0.1)
# scene.world.addEntityChild(rootEntity, pointLight)
vert, col, ind, _ = generate_sphere()

# precompute both
v_flat,   i_flat,   c_flat,   n_flat   = norm.generateFlatNormalsMesh(vert, ind, col)
v_smooth, i_smooth, c_smooth, n_smooth = norm.generateSmoothNormalsMesh(vert, ind, col)

cn_flat   = n_flat   * 0.5 + 0.5
cn_smooth = n_smooth * 0.5 + 0.5

# store for runtime swaps
mesh4._flat   = {"V": v_flat,   "I": i_flat,   "C": c_flat,   "N": n_flat,   "CN": cn_flat}
mesh4._smooth = {"V": v_smooth, "I": i_smooth, "C": c_smooth, "N": n_smooth, "CN": cn_smooth}

d = mesh4._flat if shading_idx == 1 else mesh4._smooth

mesh4.vertex_attributes.append(d["V"])                               # 0 positions
mesh4.vertex_attributes.append(d["CN"] if show_normals_as_color else d["C"])  # 1 colors
mesh4.vertex_attributes.append(d["N"])                               # 2 normals
mesh4.vertex_index.append(d["I"])

vArray4 = scene.world.addComponent(node4, VertexArray())

shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source = Shader.FRAG_PHONG)))
# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight, windowTitle = "Elements: Earth spinny spinny", openGLversion = 4, customImGUIdecorator = ImGUIecssDecorator2)

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
# projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0)  
# projMat = util.perspective(90.0, 1.33, 0.1, 100)  
projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)   

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update

model_sphere = util.translate(0.0,0.5,0.0)

shading_items = ["Smooth", "Flat"]
prev_shading_idx = shading_idx
prev_show_normals = show_normals_as_color

while running:
    # lightPos = pointLight.trans.l2world[:3, 3].tolist()
    # pointLight.shaderDec.setUniformVariable(key='modelViewProj', value=pointLight.trans.l2cam, mat4=True)
    running = scene.render()
    displayGUI_text(example_description)
    imgui.begin("Sphere Options")

    changed1, shading_idx = imgui.combo("Shading", shading_idx, shading_items)
    changed2, show_normals_as_color = imgui.checkbox("Normals as color", show_normals_as_color)

    imgui.end()

    if shading_idx != prev_shading_idx or show_normals_as_color != prev_show_normals:
        d = mesh4._flat if shading_idx == 1 else mesh4._smooth

        mesh4.vertex_attributes[0] = d["V"]
        mesh4.vertex_attributes[1] = d["CN"] if show_normals_as_color else d["C"]
        mesh4.vertex_attributes[2] = d["N"]
        mesh4.vertex_index[0] = d["I"]

        # re-upload buffers to GPU
        scene.world.traverse_visit(initUpdate, scene.world.root)

        prev_shading_idx = shading_idx
        prev_show_normals = show_normals_as_color

    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)
    view =  gWindow._myCamera # updates view via the imgui
    # mvp_cube = projMat @ view @ model_cube

    shaderDec4.setUniformVariable(key='modelViewProj', value=projMat@view@model_sphere, mat4=True)
    shaderDec4.setUniformVariable(key='model', value=model_sphere, mat4=True)
    shaderDec4.setUniformVariable(key='View', value=view, mat4=True)
    shaderDec4.setUniformVariable(key='Proj', value=projMat, mat4=True)
    shaderDec4.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
    shaderDec4.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
    shaderDec4.setUniformVariable(key='viewPos',value=LviewPos,float3=True)
    shaderDec4.setUniformVariable(key='lightPos',value=Lposition,float3=True)
    shaderDec4.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
    shaderDec4.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)

    scene.render_post()
    
scene.shutdown()