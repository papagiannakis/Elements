import os
import numpy as np

import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh, Keyframe
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem, ImGUIecssDecorator

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES
import OpenGL.GL as gl

import Elements.pyGLV.utils.normals as norm
from Elements.pyGLV.utils.terrain import generateTerrain
from Elements.pyGLV.utils.obj_to_mesh import obj_to_mesh

import Elements.pyECSS.GA.quaternion as quat
from gate_module_euclidean import *
from pyassimp import load

# VERT_PHONG_MVP = """
#         #version 410

#         layout (location=0) in vec4 vPosition;
#         layout (location=1) in vec4 vColor;
#         layout (location=2) in vec4 vNormal;
#         layout (location=3) in vec4 vWeight;

#         out     vec4 pos;
#         out     vec4 color;
#         out     vec3 normal;
        
#         uniform mat4 modelViewProj;
#         uniform mat4 model;
#         uniform mat4 MM;

#         void main()
#         {         
#             pos = pos + vWeight * model * MM * vPosition;
#             gl_Position = modelViewProj *  MM * vPosition;
#             color = vColor;
#             normal = mat3(transpose(inverse(model))) * vNormal.xyz;
#         }
#     """


def lerp(a, b, t):
    return (1 - t) * a + t * b

#Light
Lposition = util.vec(2.0, 5.5, 2.0) #uniform lightpos
Lambientcolor = util.vec(1.0, 1.0, 1.0) #uniform ambient color
Lambientstr = 0.3 #uniform ambientStr
LviewPos = util.vec(2.5, 2.8, 5.0) #uniform viewpos
Lcolor = util.vec(1.0,1.0,1.0)
Lintensity = 0.8
#Material
Mshininess = 0.4 
Mcolor = util.vec(0.8, 0.0, 0.8)

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

node4 = scene.world.createEntity(Entity(name="Object"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="Object_TRS", trs=util.scale(0.1)@util.translate(0,0,0) ))
mesh4 = scene.world.addComponent(node4, RenderMesh(name="Object_mesh"))
#skin4 = scene.world.addComponent(node4,SkinnedMesh(name="Object_skin"))
key1 = scene.world.addComponent(node4, Keyframe(name="Object_key_1"))
key2 = scene.world.addComponent(node4, Keyframe(name="Object_key_2"))

#Colored Axes
vertexAxes = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.5, 0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 1.5, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.5, 1.0]
],dtype=np.float32) 
colorAxes = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
], dtype=np.float32)
indexAxes = np.array((0,1,2,3,4,5), np.uint32) #3 simple colored Axes as R,G,B lines

##################################################################################################
scene2 = load('D:/IMPORTANT_FILES/THESIS_2_0/Diplwmatikh/astroBoy_walk.dae')
mesh_id = 3

#Vertices, Incdices/Faces, Bones from the scene we loaded with pyassimp
mesh = scene2.meshes[mesh_id]
v = mesh.vertices
f = mesh.faces
b = mesh.bones
vw = vertex_weight(len(v))
vw.populate(b)

v2 = np.concatenate((v, np.ones((v.shape[0], 1))), axis=1)

length = len(v2)
c = np.random.rand(length, 3)
c = np.around(c, decimals=1)
c = np.concatenate((c, np.ones((length, 1))), axis=1)

f2 = f.flatten()

#transform = False  
transform = True

M = initialize_M(b)

M[1] = np.dot(np.diag([1,1,1,1]),M[1])
key1.array_MM.append(read_tree(scene2,mesh_id,M,transform))

M[1][0:3,0:3] = eulerAnglesToRotationMatrix([0.3,0.3,0.4])
M[1][0:3,3] = [0.5,0.5,0.5]
key2.array_MM.append(read_tree(scene2,mesh_id,M,transform))

BB = [b[i].offsetmatrix for i in range(len(b))]
newv = np.zeros([(len(v)),3])

alpha = 1
MM1=[]

for i in range(len(key1.rotate)):
    MM1.append(np.eye(4))

for i in range(len(key1.rotate)):
    MM1[i][:3, :3] = quat.Quaternion.to_rotation_matrix(quat.quaternion_slerp(key1.rotate[i], key2.rotate[i], alpha))
    MM1[i][:3, 3] = lerp(key1.translate[i], key2.translate[i], alpha)


for i in range(len(v)):
    for j in range(4):
        if vw.id[i][j] >=0:
            #mat = key2.array_MM[0][vw.id[i][j]] @ BB[vw.id[i][j]]     
            mat = MM1[vw.id[i][j]] @ BB[vw.id[i][j]]       
            newv[i] = newv[i] +  vw.weight[i][j]*(vertex_apply_M(v[i],mat))

print(vw.id)
#mesh4.vertex_attributes[0] = np.concatenate((newv, np.ones((newv.shape[0], 1))), axis=1)

normals = norm.generateNormals(v2 , f2)

mesh4.vertex_attributes.append(v2)
mesh4.vertex_attributes[0] = np.concatenate((newv, np.ones((newv.shape[0], 1))), axis=1)
mesh4.vertex_attributes.append(c)
mesh4.vertex_attributes.append(normals)
mesh4.vertex_attributes.append(vw.weight)
mesh4.vertex_index.append(f2)
vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

##################################################################################################

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())



# Generate terrain
vertexTerrain, indexTerrain, colorTerrain= generateTerrain(size=4,N=20)
# Add terrain
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain) 
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
# terrain_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)

## ADD AXES ##
axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.translate(0.0, 0.001, 0.0))) #util.identity()
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes) 
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=gl.GL_LINES)) # note the primitive change

# shaderDec_axes = scene.world.addComponent(axes, Shader())
# OR
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
# axes_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)


# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = 1200, windowHeight = 800, windowTitle = "Elements: Let There Be Light", openGLversion = 4, customImGUIdecorator = ImGUIecssDecorator)

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
projMat = util.perspective(50.0, 1200/800, 0.01, 100.0)   

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update

model_terrain_axes = util.translate(0.0,0.0,0.0)



while running:
    running = scene.render(running)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)
    view =  gWindow._myCamera # updates view via the imgui

    mvp_obj = projMat @ view @ trans4.trs
    mvp_terrain = projMat @ view @ terrain_trans.trs
    mvp_axes = projMat @ view @ axes_trans.trs

    
    # mvp_cube = projMat @ view @ model_cube
    # if alpha > 1:
    #     alpha = 0

    # MM1 = []
    # for i in range(len(key1.rotate)):
    #     MM1.append(np.eye(4))

    # for i in range(len(key1.rotate)):
    #     MM1[i][:3, :3] = quat.Quaternion.to_rotation_matrix(quat.quaternion_slerp(key1.rotate[i], key2.rotate[i], alpha))
    #     MM1[i][:3, 3] = lerp(key1.translate[i], key2.translate[i], alpha)


    # for i in range(len(v)):
    #     for j in range(4):
    #         if vw.id[i][j] >=0:
    #             #mat = key2.array_MM[0][vw.id[i][j]] @ BB[vw.id[i][j]]     
    #             mat = MM1[vw.id[i][j]] @ BB[vw.id[i][j]]       
    #             #newv[i] = newv[i] + vw.weight[i][j]*(vertex_apply_M(v[i],mat))
                 
    # alpha += 0.05 

    axes_shader.setUniformVariable(key='modelViewProj', value = mvp_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain, mat4=True)


    shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_obj, mat4=True)
    shaderDec4.setUniformVariable(key='model', value=trans4.trs, mat4=True)
    # shaderDec4.setUniformVariable(key='MM', value=mat, mat4=True)

    shaderDec4.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
    shaderDec4.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
    shaderDec4.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
    shaderDec4.setUniformVariable(key='lightPos', value=Lposition, float3=True)
    shaderDec4.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
    shaderDec4.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
    shaderDec4.setUniformVariable(key='shininess', value=Mshininess, float1=True)
    shaderDec4.setUniformVariable(key='matColor', value=Mcolor, float3=True)

    scene.render_post()
    
scene.shutdown()