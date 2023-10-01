"""
Simple example converting point cloud to mesh 
    
@author Nikos Iliakis csd4375
"""

import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import  TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.utils.terrain import generateTerrain
from OpenGL.GL import GL_POINTS

import imgui
from PointCloudToMesh import generateTrianglesFromCustomList
from PointCloudToMesh import generateBunnyExample
from Elements.utils.helper_function import displayGUI_text

example_description = \
"This example shows the conversion of a point cloud to a mesh. \n\
Input can be randomly generated or you can see the bunny example\n\
The scene is being lit using the Blinn-Phong algorithm. \n\
You may move the camera using the mouse or the GUI. \n\
You may alter the variables of the shader through the Shader vars window \n\
Hit ESC OR Close the window to quit." 

ambColor, ambStr = [1,0,0], 0
vwPos, lghtPos, lghtCol, lghtInt = [0,0,0], [0,2,2], [0.5, 0.5, 0.5], 3
str, matCol= 0.5, [0.5, 0.5, 0.5]

def displayGUI():
    global ambColor, ambStr
    global vwPos, lghtPos, lghtCol, lghtInt
    global str, matCol
    
    imgui.begin("Shader vars")
    
    changed, ambColor = imgui.drag_float3("ambientColor", *ambColor, change_speed=0.05)
    changed, ambStr = imgui.drag_float("ambientStr", ambStr, change_speed=0.05)
    
    changed, vwPos = imgui.drag_float3("viewPos", *vwPos, change_speed=0.05)
    changed, lghtPos = imgui.drag_float3("lightPos", *lghtPos, change_speed=0.05)
    changed, lghtCol = imgui.drag_float3("lightColor", *lghtCol, change_speed=0.05)
    changed, lghtInt = imgui.drag_float("lightIntensity", lghtInt, change_speed=0.05)
    
    changed, str = imgui.drag_float("shininess", str, change_speed=0.05)
    changed, matCol = imgui.drag_float3("matColor", *matCol, change_speed=0.05)
    
    imgui.end()
    
def main():
    scene = Scene()    

    # Scenegraph with Entities, Components
    rootEntity = scene.world.createEntity(Entity(name="RooT"))
    entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
    scene.world.addEntityChild(rootEntity, entityCam1)
    trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()))

    node4 = scene.world.createEntity(Entity(name="node4"))
    scene.world.addEntityChild(rootEntity, node4)
    trans4 = scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.identity())) #util.identity()
    mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

    # Systems
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())

    #hexagonical prism
    vertices = np.array([
        [-0.5, -0.5, 0.5, 1.0],   # Bottom left-front corner
        [0.5, -0.5, 0.5, 1.0],    # Bottom right-front corner
        [0.25, 0.25, 0.5, 1.0],   # Bottom middle-front
        [-0.5, -0.5, -0.5, 1.0],  # Bottom left-back corner
        [0.5, -0.5, -0.5, 1.0],   # Bottom right-back corner
        [0.25, 0.25, -0.5, 1.0],  # Bottom middle-back
        [0.0, 0.0, 0.75, 1.0],    # Top center
        [0.0, 0.0, -0.75, 1.0],   # Bottom center
    ], dtype=np.float32)

    #tree with branches
    # vertices = np.array([
    #     [0.0, 0.0, 1.0, 1.0],      # Tree trunk base
    #     [0.0, 0.0, 0.5, 1.0],      # Middle of the trunk
    #     [0.0, 0.0, 0.2, 1.0],      # Top of the trunk
    #     [0.0, 0.0, -0.2, 1.0],     # Root of the tree
    #     [0.0, 0.4, 0.5, 1.0],      # Branch 1
    #     [0.0, -0.4, 0.5, 1.0],     # Branch 2
    #     [0.4, 0.0, 0.5, 1.0],      # Branch 3
    #     [-0.4, 0.0, 0.5, 1.0],     # Branch 4
    # ], dtype=np.float32)



    #mesh_vertices, mesh_normals, mesh_indices = generateTrianglesFromCustomList(vertices)
    mesh_vertices, mesh_normals, mesh_indices = generateBunnyExample()

    # Define the gray color as an RGB array.
    gray_color = np.array([0.5, 0.5, 0.5])

    # Create an array of the same gray color for each vertex in your mesh.
    num_vertices = len(mesh_vertices)
    mesh_colors = np.tile(gray_color, (num_vertices, 1))

    # attach object
    mesh4.vertex_attributes.append(mesh_vertices)
    mesh4.vertex_attributes.append(mesh_colors)
    mesh4.vertex_attributes.append(mesh_normals)
    mesh4.vertex_index.append(mesh_indices)
    vArray4 = scene.world.addComponent(node4, VertexArray())
    shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG_MATERIAL)))

    ## ADD POINTS ##
    points = scene.world.createEntity(Entity(name="points"))
    scene.world.addEntityChild(rootEntity, points)
    points_trans = scene.world.addComponent(points, BasicTransform(name="points_trans", trs=util.identity()))
    points_mesh = scene.world.addComponent(points, RenderMesh(name="points_mesh"))
    points_vArray = scene.world.addComponent(points, VertexArray(primitive=GL_POINTS)) # note the primitive change
    points_shader = scene.world.addComponent(points, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))


    # MAIN RENDERING LOOP

    running = True
    scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements: point Cloud to Mesh", openGLversion = 4)
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



    eye = util.vec(2.5, 3.5, 2.5)
    target = util.vec(0.5, 0.5, 0.0)
    up = util.vec(0.0, 1.0, 0.0)
    view = util.lookat(eye, target, up)

    projMat = util.perspective(50.0, 1.0, 0.01, 10.0)

    gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update
    gWindow._colorEditor = 173, 216, 230
    
    model_cube = trans4.trs @ util.scale(10,10,10)


    model_terrain_axes = util.translate(0.0,0.0,0.0) ## COMPLETELY OVERRIDE OBJECT's TRS

    while running:
        running = scene.render()
        scene.world.traverse_visit(renderUpdate, scene.world.root)
        view =  gWindow._myCamera # updates view via the imgui
        mvp_cube = projMat @ view @ model_cube
        mvp_terrain_axes = projMat @ view @ model_terrain_axes
        
        displayGUI()
        displayGUI_text(example_description)
        
        points_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
        
        shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
        shaderDec4.setUniformVariable(key='model', value=model_cube, mat4=True)
        
        shaderDec4.setUniformVariable(key='ambientColor', value=ambColor, float3=True)
        shaderDec4.setUniformVariable(key='ambientStr', value=ambStr, float1=True)
        
        shaderDec4.setUniformVariable(key='viewPos', value=vwPos, float3=True)
        shaderDec4.setUniformVariable(key='lightPos', value=lghtPos, float3=True)
        shaderDec4.setUniformVariable(key='lightColor', value=lghtCol, float3=True)
        shaderDec4.setUniformVariable(key='lightIntensity', value=lghtInt, float1=True)
        
        shaderDec4.setUniformVariable(key='shininess', value=str, float1=True)
        shaderDec4.setUniformVariable(key='matColor', value=matCol, float3=True)
        
        
        scene.render_post()
        
    scene.shutdown()

if __name__ == "__main__":    
    main()