from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform,  RenderMesh
from Elements.pyECSS.Event import Event
import Elements.pyECSS.utilities as util
import numpy as np

from Elements.pyGLV.GUI.Viewer import  RenderGLStateSystem,  ImGUIecssDecorator
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera


# Creates a basic object with a transform, mesh, shader, and vertex array
# This is a helper class to make it easier to create objects
# .entity is the entity that contains all the components and can be added to the scene
class ObjectCreator():
    def __init__(self, name=None, type=None, id=None) -> None:
        self.entity = Entity(name, type, id);
        # Gameobject basic properties
        # Create basic components of a primitive object
        self.entity.trans          = BasicTransform(name="trans", trs=util.identity());
        self.entity.mesh           = RenderMesh(name="mesh");
        self.entity.shaderDec      = ShaderGLDecorator(Shader(vertex_source = Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG));
        self.entity.vArray         = VertexArray();
        # Add components to entity
        scene = Scene();
        scene.world.createEntity(self.entity);
        scene.world.addComponent(self.entity, self.entity.trans);
        scene.world.addComponent(self.entity, self.entity.mesh);
        scene.world.addComponent(self.entity, self.entity.shaderDec);
        scene.world.addComponent(self.entity, self.entity.vArray);
    
    @property
    def color(self):
        return self.entity._color;
    @color.setter
    def color(self, colorArray):
        self.entity._color = colorArray;

    def SetVertexAttributes(self, vertex, color, index, normals = None):
        self.entity.mesh.vertex_attributes.append(vertex);
        self.entity.mesh.vertex_attributes.append(color);
        if normals is not None:
            self.entity.mesh.vertex_attributes.append(normals);
        self.entity.mesh.vertex_index.append(index);

# Creates a cube with the given name and color
# Returns the entity that contains the cube
def CubeSpawn(cubename = "Cube", color = None): 
    cube = ObjectCreator(cubename);
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
    if color is None:
        colors = np.array([
        [0.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 1.0],
        [1.0, 1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 1.0],
        [1.0, 0.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [0.0, 1.0, 1.0, 1.0]
        ], dtype=np.float32)
    else:
        colors =  [color] * len(vertices)
        colors = np.array(colors)
    
    #index arrays for above vertex Arrays
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
    ) #rhombus out of two triangles
    vertices, colors, indices, normals = IndexedConverter().Convert(vertices, colors, indices, produceNormals=True);
    cube.SetVertexAttributes(vertices, colors, indices, normals);
    return cube.entity;


def SphereSpawn(spherename = "Sphere", color = None):
    sphere = ObjectCreator(spherename);
    if color is None:
        color = [1.0, 1.0, 1.0, 1.0];
    #vertices of a simple sphere
    vertices = [];
    colors = [];
    indices = [];
    normals = [];
    for i in range(0, 20):
        for j in range(0, 20):
            x = np.cos(2 * np.pi * j / 20) * np.sin(np.pi * i / 20);
            y = np.sin(2 * np.pi * j / 20) * np.sin(np.pi * i / 20);
            z = np.cos(np.pi * i / 20);
            vertices.append([x, y, z, 1.0]);
            colors.append(color);
            normals.append([x, y, z]);
    for i in range(0, 20):
        for j in range(0, 20):
            indices.append(i * 20 + j);
            indices.append((i + 1) * 20 + j);
            indices.append((i + 1) * 20 + (j + 1) % 20);
            indices.append(i * 20 + j);
            indices.append((i + 1) * 20 + (j + 1) % 20);
            indices.append(i * 20 + (j + 1) % 20);
    sphere.SetVertexAttributes(vertices, colors, indices, normals);
    return sphere.entity;

def CylinderSpawn(cylindername = "Cylinder", color = None):
    cylinder = ObjectCreator(cylindername);
    if color is None:
        color = [1.0, 1.0, 1.0, 1.0]
    #vertices of a simple cylinder
    vertices = [];
    colors = [];
    indices = [];
    normals = [];
    for i in range(0, 20):
        for j in range(0, 20):
            x = np.cos(2 * np.pi * j / 20);
            y = np.sin(2 * np.pi * j / 20);
            z = 2 * i / 20 - 1;
            vertices.append([x, y, z, 1.0]);
            colors.append(color);
            normals.append([x, y, 0]);
    for i in range(0, 20):
        for j in range(0, 20):
            indices.append(i * 20 + j);
            indices.append((i + 1) * 20 + j);
            indices.append((i + 1) * 20 + (j + 1) % 20);
            indices.append(i * 20 + j);
            indices.append((i + 1) * 20 + (j + 1) % 20);
            indices.append(i * 20 + (j + 1) % 20);
    cylinder.SetVertexAttributes(vertices, colors, indices, normals);
    return cylinder.entity;

def ConeSpawn(conename = "Cone", color = None):
    cone = ObjectCreator(conename);
    if color is None:
        color = [1.0, 1.0, 1.0, 1.0];
    #vertices of a simple cone
    vertices = [];
    colors = [];
    indices = [];
    normals = [];
    for i in range(0, 20):
        for j in range(0, 20):
            x = np.cos(2 * np.pi * j / 20) * (1 - i / 20);
            y = np.sin(2 * np.pi * j / 20) * (1 - i / 20);
            z = 2 * i / 20 - 1;
            vertices.append([x, y, z, 1.0]);
            colors.append(color);
            normals.append([x, y, 0]);
    for i in range(0, 20):
        for j in range(0, 20):
            indices.append(i * 20 + j);
            indices.append((i + 1) * 20 + j);
            indices.append((i + 1) * 20 + (j + 1) % 20);
            indices.append(i * 20 + j);
            indices.append((i + 1) * 20 + (j + 1) % 20);
            indices.append(i * 20 + (j + 1) % 20);
    cone.SetVertexAttributes(vertices, colors, indices, normals);
    return cone.entity;

def TorusSpawn(torusname = "Torus", color = None):
    torus = ObjectCreator(torusname);
    if color is None:
        color = [1.0, 1.0, 1.0, 1.0];
    #vertices of a simple torus
    vertices = [];
    colors = [];
    indices = [];
    normals = [];
    for i in range(0, 20):
        for j in range(0, 20):
            x = np.cos(2 * np.pi * j / 20) * (1 + np.cos(2 * np.pi * i / 20) / 2);
            y = np.sin(2 * np.pi * j / 20) * (1 + np.cos(2 * np.pi * i / 20) / 2);
            z = np.sin(2 * np.pi * i / 20) / 2;
            vertices.append([x, y, z, 1.0]);
            colors.append(color);
            normals.append([x, y, z]);
    for i in range(0, 20):
        for j in range(0, 20):
            indices.append(i * 20 + j);
            indices.append((i + 1) * 20 + j);
            indices.append((i + 1) * 20 + (j + 1) % 20);
            indices.append(i * 20 + j);
            indices.append((i + 1) * 20 + (j + 1) % 20);
            indices.append(i * 20 + (j + 1) % 20);
    torus.SetVertexAttributes(vertices, colors, indices, normals);
    return torus.entity;

class IndexedConverter():
    # Assumes triangulated buffers. Produces indexed results that support
    # normals as well.
    def Convert(self, vertices, colors, indices, produceNormals=True):

        iVertices = [];
        iColors = [];
        iNormals = [];
        iIndices = [];
        for i in range(0, len(indices), 3):
            iVertices.append(vertices[indices[i]]);
            iVertices.append(vertices[indices[i + 1]]);
            iVertices.append(vertices[indices[i + 2]]);
            iColors.append(colors[indices[i]]);
            iColors.append(colors[indices[i + 1]]);
            iColors.append(colors[indices[i + 2]]);
            

            iIndices.append(i);
            iIndices.append(i + 1);
            iIndices.append(i + 2);

        if produceNormals:
            for i in range(0, len(indices), 3):
                iNormals.append(util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]));
                iNormals.append(util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]));
                iNormals.append(util.calculateNormals(vertices[indices[i]], vertices[indices[i + 1]], vertices[indices[i + 2]]));

        iVertices = np.array( iVertices, dtype=np.float32 )
        iColors   = np.array( iColors,   dtype=np.float32 )
        iIndices  = np.array( iIndices,  dtype=np.uint32  )

        iNormals  = np.array( iNormals,  dtype=np.float32 )

        return iVertices, iColors, iIndices, iNormals;

