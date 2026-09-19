'''
    @Authors: MANOS DIMITRIS csd5188, STAUROS MANESIS csd5266s
    @Date: December 2025
    @Description: 
    This class is used for generating 3D objects with UV mapping capabilities.
    It provides methods to create spheres and cylinders with proper UV coordinates for texture mapping.
'''

from matplotlib import colors
import numpy as np
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform
from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform,  RenderMesh
from Elements.pyECSS.Event import Event
import Elements.pyECSS.math_utilities as util
import numpy as np

from Elements.pyGLV.GUI.Viewer import  RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.SimpleCamera import SimpleCamera
from Elements.utils import normals
from Elements.pyGLV.GL.Textures import Texture
from Elements.utils.normals import Convert
from Elements.definitions import SHADER_DIR


TEXTURE_VERT = (SHADER_DIR / "UVMappingTexture.vert").read_text()
TEXTURE_FRAG = (SHADER_DIR / "UVMappingTexture.frag").read_text()

class UVObjectGenerator(Entity):
    def __init__(self, name=None, type=None, id=None) -> None:
        super().__init__(name, type, id);  


        self._color          = [1, 1, 1, 1.0];
        # Create basic components of a primitive object
        self.trans          = BasicTransform(name="trans", trs=util.identity());
        self.mesh           = RenderMesh(name="mesh");
        # THIS IS THE SHADER WITH TEXTURE SUPPORT
        # CAN ALSO BE CHANGED TO OTHER SHADERS AS NEEDED THOURGH A PROGRAM
        self.shaderDec      = ShaderGLDecorator(Shader(vertex_import_file = SHADER_DIR / "SimpleTexturePhong.vert", fragment_import_file=SHADER_DIR / "SimpleTexturePhong.frag"));
        #self.shaderDec      = ShaderGLDecorator(Shader(vertex_import_file= SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag"));
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

    def SetTexturedVertexAttributes(self, vertex, normals, uvs, index):
        self.mesh.vertex_attributes.append(vertex)   # THIS SAME AS THE SHADERS LOCATION 0
        self.mesh.vertex_attributes.append(normals)  # location 1 and so on
        self.mesh.vertex_attributes.append(uvs)      # location 2...
        self.mesh.vertex_index.append(index)

    def setMVP(self, mvp):
        self.shaderDec.setUniformVariable(key='modelViewProj', value=mvp, mat4=True)


    def Sphere(name="Sphere", radius=0.5, sectorCount=32, stackCount=16):
        sphere = UVObjectGenerator(name)
        # Sector count is the number of vertical slices the sphere has kinda like longitude lines
        # Stack count is the number of horizontal slices the sphere same as latitude lines
        vertices = []
        normals = []
        indices = []

        for i in range(stackCount + 1):
            
            phi = -np.pi/2 + (np.pi * i / stackCount)  # from -pi/2 to pi/2

            y = radius * np.sin(phi)
            r = radius * np.cos(phi)

            for j in range(sectorCount + 1):
                theta = 2 * np.pi * j / sectorCount 
                x = r * np.cos(theta)
                z = r * np.sin(theta)

                vertices.append([x, y, z, 1.0])
                normals.append([x/radius, y/radius, z/radius, 0.0])


        
        for i in range(stackCount):
            k1 = i * (sectorCount + 1)
            k2 = k1 + sectorCount + 1
            for j in range(sectorCount):
                indices.extend([
                    k1+j, k2+j, k1+j+1,
                    k1+j+1, k2+j, k2+j+1
                ])

        vertices = np.array(vertices, dtype=np.float32)
        normals  = np.array(normals,  dtype=np.float32)
        indices  = np.array(indices,  dtype=np.uint32)

        uvs = sphere.ProjectUV_Sphere(vertices)

        sphere.SetTexturedVertexAttributes(vertices, normals, uvs, indices)

        return sphere

    def Cylinder(name="Cylinder", radius=0.5, height=2.0, sectorCount=32):
        cylinder = UVObjectGenerator(name)

        vertices = []
        normals = []
        indices = []

        half_h = height / 2.0

        # ----- Side wall -----
        for i in range(sectorCount + 1):
            angle = i * 2 * np.pi / sectorCount
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)

            # bottom
            vertices.append([x, y, -half_h, 1.0])
            normals.append([x/radius, y/radius, 0.0, 0.0])


            # top
            vertices.append([x, y, +half_h, 1.0])
            normals.append([x/radius, y/radius, 0.0, 0.0])

            

        # Side indices
        for i in range(sectorCount):
            k = i * 2
            indices += [k, k+1, k+2,  k+1, k+3, k+2]

        base_index = len(vertices)

        # ----- Bottom cap -----
        vertices.append([0, 0, -half_h, 1.0])
        normals.append([0, 0, -1, 0])

        center_bottom = len(vertices) - 1

        for i in range(sectorCount + 1):
            angle = i * 2 * np.pi / sectorCount
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)

            vertices.append([x, y, -half_h, 1.0])
            normals.append([0, 0, -1, 0])

            if i < sectorCount:
                indices += [
                    center_bottom,
                    center_bottom + i + 1,
                    center_bottom + i + 2
                ]

        # ----- Top cap -----
        start_top = len(vertices)

        vertices.append([0, 0, +half_h, 1.0])
        normals.append([0, 0, +1, 0])

        center_top = len(vertices) - 1
        
      

        for i in range(sectorCount + 1):
            angle = i * 2 * np.pi / sectorCount
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)

            vertices.append([x, y, +half_h, 1.0])
            normals.append([0, 0, +1, 0])

            if i < sectorCount:
                indices += [
                    center_top,
                    center_top + i + 2,
                    center_top + i + 1
                ]

        vertices = np.array(vertices, dtype=np.float32)
        normals = np.array(normals, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)


        uvs = cylinder.ProjectUV_Cylinder(vertices)   

        cylinder.SetTexturedVertexAttributes(vertices, normals, uvs, indices)

        return cylinder

    @staticmethod
    def ProjectUV_Sphere(vertices, offset_u=0.0, offset_v=0.0, scale_u=1.0, scale_v=1.0, flip_u=False, flip_v=False, seam_offset=0.0):
        uvs = []

        for v in vertices:
            x, y, z = v[0], v[1], v[2]

            length = np.sqrt(x*x + y*y + z*z)
            if length == 0:
                uvs.append([0.5, 0.5])
                continue

            x /= length
            y /= length
            z /= length

            theta = np.arctan2(z, x)
            phi   = np.arcsin(y)

            u = 1 - (theta + np.pi) / (2 * np.pi)
            v_coord = (phi + np.pi/2) / np.pi

           
            if flip_u:
                u = 1.0 - u
            if flip_v:
                v_coord = 1.0 - v_coord

        
            u = 0.5 + (u - 0.5) * scale_u
            v_coord = 0.5 + (v_coord - 0.5) * scale_v

           
            u += offset_u
            v_coord += offset_v

            
            u = u % 1.0
            v_coord = v_coord % 1.0

            u = (u + seam_offset) % 1.0

            uvs.append([u, v_coord])

        return np.array(uvs, dtype=np.float32)

    @staticmethod
    def ProjectUV_Cylinder(vertices, axis='y', offset_u=0.0, offset_v=0.0, scale_u=1.0, scale_v=1.0, flip_u=False, flip_v=False):
        uvs = []

        ys = [v[1] for v in vertices]
        minY, maxY = min(ys), max(ys)

        for v in vertices:
            x, y, z = v[0], v[1], v[2]

            theta = np.arctan2(z, x)
            u = 1 - (theta + np.pi) / (2 * np.pi)

            if maxY > minY:
                v_coord = (y - minY) / (maxY - minY)
            else:
                v_coord = 0.0

            
            if flip_u:
                u = 1.0 - u
            if flip_v:
                v_coord = 1.0 - v_coord

            u = 0.5 + (u - 0.5) * scale_u
            v_coord = 0.5 + (v_coord - 0.5) * scale_v

            
            u += offset_u
            v_coord += offset_v

            
            u = u % 1.0
            v_coord = v_coord % 1.0

            uvs.append([u, v_coord])

        return np.array(uvs, dtype=np.float32)

    @staticmethod
    def AutoProjectUV(vertices, return_type=False):
        """
        Automatically choose between cylindrical and spherical UV projection.
        Cylindrical for tall objects (like bottles/cans), Spherical for round objects.
        
        :param vertices: Array of vertex positions
        :param return_type: If True, returns (uvs, projection_type), else just uvs
        :return: UV coordinates, or (UV coordinates, projection_type) if return_type=True
        """
        vertices_array = np.array(vertices)
        coords = vertices_array[:, :3]
        
        
        min_coords = np.min(coords, axis=0)
        max_coords = np.max(coords, axis=0)
        height = max_coords[1] - min_coords[1]  # Y axis
        width = max(max_coords[0] - min_coords[0], max_coords[2] - min_coords[2])  # XZ plane
        
        
        if height > width * 1.5:
            projection_type = 'cylinder'
            uvs = UVObjectGenerator.ProjectUV_Cylinder(vertices)
        else:
            projection_type = 'sphere'
            uvs = UVObjectGenerator.ProjectUV_Sphere(vertices)
        
        if return_type:
            return uvs, projection_type
        else:
            return uvs
        
        
    @staticmethod
    def BuildSphereProjectionGizmo(radius=1.0, rings=12, sectors=24):
        vertices = []

        for i in range(rings):
            phi = -np.pi / 2 + i * np.pi / (rings - 1)
            for j in range(sectors):
                theta = j * 2 * np.pi / sectors
                x = radius * np.cos(phi) * np.cos(theta)
                y = radius * np.sin(phi)
                z = radius * np.cos(phi) * np.sin(theta)
                vertices.append([x, y, z, 1.0])

        return np.array(vertices, dtype=np.float32)    