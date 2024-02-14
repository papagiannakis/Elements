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
from OpenGL.GL import GL_LINES

import imgui
from PointCloudToMesh import generateTrianglesFromCustomList
from PointCloudToMesh import generateBunnyExample
from Elements.utils.Shortcuts import displayGUI_text

example_description = \
"This example shows the conversion of a point cloud to a mesh. \n\
One point cloud to mesh is the bunny and the other point cloud n\
to mesh is a randomly generated sphere using the ball_pivoting algorithm n\
The scene is being lit using the Blinn-Phong algorithm. \n\
You may move the camera using the mouse or the GUI. \n\
You may alter the variables of the lighting through the Shader vars window \n\
Hit ESC OR Close the window to quit." 

ambColor, ambStr = [1,0,0], 0
vwPos, lghtPos, lghtCol, lghtInt = [0,0,0], [0,2,0], [0.5, 0.5, 0.5], 3
str, matCol= 0.0, [0.5, 0.5, 0.5]

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

    object1 = scene.world.createEntity(Entity(name="object1"))
    scene.world.addEntityChild(rootEntity, object1)
    trans4 = scene.world.addComponent(object1, BasicTransform(name="trans4", trs=util.identity())) #util.identity()
    mesh4 = scene.world.addComponent(object1, RenderMesh(name="mesh4"))
    
    bunny = scene.world.createEntity(Entity(name="bunny"))
    scene.world.addEntityChild(rootEntity, bunny)
    trans5 = scene.world.addComponent(bunny, BasicTransform(name="trans5", trs=util.identity())) #util.identity()
    mesh5 = scene.world.addComponent(bunny, RenderMesh(name="mesh5"))
    
    floor = scene.world.createEntity(Entity(name="floor"))
    scene.world.addEntityChild(rootEntity, floor)
    trans6 = scene.world.addComponent(floor, BasicTransform(name="trans6", trs=util.scale(100, 0.5, 100))) #util.identity()
    mesh6 = scene.world.addComponent(floor, RenderMesh(name="mesh6"))
    

    # Systems
    transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
    renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
    initUpdate = scene.world.createSystem(InitGLShaderSystem())

    # Number of points representing sphere the more the better the sphere will be
    num_points = 100000

    # Generate random values for θ and ϕ (for a sphere)
    theta = np.random.uniform(0, 2 * np.pi, num_points)
    phi = np.random.uniform(0, np.pi, num_points)

    # Initialize an empty list to store the points
    points_on_sphere = []

    # Convert spherical coordinates to Cartesian coordinates and append to the list
    for i in range(num_points):
        x = np.sin(phi[i]) * np.cos(theta[i])
        y = np.sin(phi[i]) * np.sin(theta[i])
        z = np.cos(phi[i])
        points_on_sphere.append([x, y, z])


    # Now, points_on_sphere contains the list of points in the desired format
    vertices = np.array(points_on_sphere, dtype=np.float32) 
    
    mesh_vertices, mesh_normals, mesh_indices = generateTrianglesFromCustomList(vertices, isItASphere = True)
    bunny_vertices, bunny_normals, bunny_indices = generateBunnyExample()

    # Define the white color as an RGB array.
    white_color = np.array([1, 1, 1])

    # attach object
    mesh4.vertex_attributes.append(mesh_vertices)
    mesh4.vertex_attributes.append(np.tile(white_color, (len(mesh_vertices), 1)))
    mesh4.vertex_attributes.append(mesh_normals)
    mesh4.vertex_index.append(mesh_indices)
    vArray4 = scene.world.addComponent(object1, VertexArray())
    shaderDec4 = scene.world.addComponent(object1, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

    # attach object
    mesh5.vertex_attributes.append(bunny_vertices)
    mesh5.vertex_attributes.append(np.tile(white_color, (len(bunny_vertices), 1)))
    mesh5.vertex_attributes.append(bunny_normals)
    mesh5.vertex_index.append(bunny_indices)
    vArray5 = scene.world.addComponent(bunny, VertexArray())
    shaderDec5 = scene.world.addComponent(bunny, ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

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

    # MAIN RENDERING LOOP

    running = True
    scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements: point Cloud to Mesh - Bunny and the ball", openGLversion = 4)
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

    gGUI._colorEditor = 0.2, 0.2, 0
    gGUI._eye = eye
    gGUI._target = target
    gGUI._up = up
    
    projMat = util.perspective(50.0, 1.0, 0.01, 10.0)

    gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update
    
    object1_trans = trans4.trs @ util.translate(0, 0.25, 0.5) @ util.scale(0.3, 0.3, 0.3) 
    bunny_trans = trans5.trs @ util.translate(1,-0.25,0) @ util.scale(7,7,7)

    model_terrain_axes = util.translate(0.0,0.0,0.0) ## COMPLETELY OVERRIDE OBJECT's TRS

    while running:
        running = scene.render()
        scene.world.traverse_visit(renderUpdate, scene.world.root)
        view =  gWindow._myCamera # updates view via the imgui
        
        ovp_1 = projMat @ view @ object1_trans
        ovp_2 = projMat @ view @ bunny_trans
        mvp_terrain_axes = projMat @ view @ model_terrain_axes
        
        displayGUI()
        displayGUI_text(example_description)
                
        shaderDec4.setUniformVariable(key='modelViewProj', value=ovp_1, mat4=True)
        shaderDec4.setUniformVariable(key='model', value=object1_trans, mat4=True)
        shaderDec4.setUniformVariable(key='ambientColor', value=ambColor, float3=True)
        shaderDec4.setUniformVariable(key='ambientStr', value=ambStr, float1=True)
        shaderDec4.setUniformVariable(key='viewPos', value=vwPos, float3=True)
        shaderDec4.setUniformVariable(key='lightPos', value=lghtPos, float3=True)
        shaderDec4.setUniformVariable(key='lightColor', value=lghtCol, float3=True)
        shaderDec4.setUniformVariable(key='lightIntensity', value=lghtInt, float1=True)
        shaderDec4.setUniformVariable(key='shininess', value=str, float1=True)
        shaderDec4.setUniformVariable(key='matColor', value=matCol, float3=True)
        
        shaderDec5.setUniformVariable(key='modelViewProj', value=ovp_2, mat4=True)
        shaderDec5.setUniformVariable(key='model', value=bunny_trans, mat4=True)
        shaderDec5.setUniformVariable(key='ambientColor', value=ambColor, float3=True)
        shaderDec5.setUniformVariable(key='ambientStr', value=ambStr, float1=True)
        shaderDec5.setUniformVariable(key='viewPos', value=vwPos, float3=True)
        shaderDec5.setUniformVariable(key='lightPos', value=lghtPos, float3=True)
        shaderDec5.setUniformVariable(key='lightColor', value=lghtCol, float3=True)
        shaderDec5.setUniformVariable(key='lightIntensity', value=lghtInt, float1=True)
        shaderDec5.setUniformVariable(key='shininess', value=str, float1=True)
        shaderDec5.setUniformVariable(key='matColor', value=matCol, float3=True)
        
        terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)

        scene.render_post()
        
    scene.shutdown()

if __name__ == "__main__":    
    main()