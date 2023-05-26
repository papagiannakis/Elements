import codecs, os
from typing import Dict, List, Tuple
from Elements.pyGLV.utils.objimporter.material import Material, StandardMaterial
from Elements.pyGLV.utils.objimporter.wavefront_obj_face import WavefrontObjectFace
from Elements.pyGLV.utils.objimporter.wavefront_obj_mesh import WavefrontObjectMesh
from Elements.pyGLV.utils.objimporter.model import Model
from PIL import Image
from pathlib import Path
import traceback


class WavefrontMaterialLibrary():
    materials:List[Material]

    def __init__(self, name, file_path, encoding = 'utf-8'):
        self.name = name
        self.__file_path = file_path
        self.__parse_dispatch = {
            "newmtl" : self.__parse_newmtl,
            # "Ka" : self.__parse_ambient_reflectivity,
            # "Ns" : self.__parse_specular_exponent,
            # "Ks": self.__parse_specular_reflectivity,
            # "Ke" : self.__parse_normal,
            # "Ni" : self.__parse_face,
            # "d" : self.__parse_dissolve,
            # "illum" : self.__parse_illumination_mode,
            "map_Kd" : self.__parse_diffuse_map,
            "map_Bump" : self.__parse_normal_map,
            "bump" : self.__parse_normal_map, # Alternative command for map_Bump
            "map_refl" : self.__parse_metallic_map,
            "map_Pr" : self.__parse_roughness_map,
            "map_Ka" : self.__parse_ambient_occlusion_map
        }

        self.materials = []

        self.__parse_from_file(encoding)

    def get_material(self, name:str)->Material:
        """
        Searches a material by name

        Params
        ------
        name : str
            The name of the material to search for.

        Returns
        -------
        Material | None
            The material if found, None otherwise.
        """
        try:
            index = [ x.name for x in self.materials ].index(name)
            return self.materials[index]
        except ValueError:
            return None 

    def __parse_from_file(self, encoding):
        try:
            with codecs.open(self.__file_path, encoding=encoding) as f:
                
                line_number = 0
                # Parse file lines
                for line in f:
                    line_number +=1

                    line = line.strip()

                    # Line is empty or comment? Skip
                    if len(line)<1 or line[0] == "#":
                        continue

                    parse_function = self.__parse_dispatch.get(line.split(' ')[0], self.__parse_unknown)
                    parse_function(line, line_number)


        except FileNotFoundError as err:
            print("Could not load material library %s, file not found" % (self.__file_path))
    
    def __get_current_material(self):
        if len(self.materials) > 0:
            return self.materials[len(self.materials)-1]
        else: # If current material does not exist create a new one but do not save, file has not correct format
            return Material("")

    def __parse_unknown(self, line, line_number) -> None:
        print("Unsupported command '%s' in file %s, line %d" % (line, self.__file_path, line_number))

    def __parse_newmtl(self, line, line_number) -> None:
        line = line.split(' ')
    
        # TODO: for now we only support StandardMaterials. Make more shaders and extend Material to support more illumination modes
        
        # Invalid command, materials must have name
        if len(line) < 2:
            return 

        material_name = line[1]

        self.materials.append(StandardMaterial(material_name))

    # def __parse_ambient_reflectivity(self, line, line_number)-> None:
    #     material:StandardMaterial = self.__get_current_material()

    #     pass

    # def __parse_specular_exponent(self, line, line_number)-> None:
    #     pass

    # def __parse_texture_coord(self, line, line_number)-> None:
    #     pass

    # Textures
    def __parse_diffuse_map(self, line, line_number)-> None:
        line = line.split(' ')
        
        # Check command validity
        if len(line) < 2:
            return
        
        # Parse image texture
        image_path = os.path.join(os.path.dirname(self.__file_path), line[len(line)-1])
        image_loaded, image_data = self.__load_texture(image_path)

        if image_loaded:
            material:StandardMaterial = self.__get_current_material()
            material.albedo_map = image_data
        else:
            print("Could not load image in line {}, of file {}. Maybe the image name contains spaces, not currently supported.".format(line_number, self.__file_path))

    def __parse_normal_map(self, line, line_number)-> None:
        line = line.split(' ')
        
        # NOTE: only -bm option is supported for now
        
        # Parse -bm multiplier
        multiplier = 1.0
        try:
            # Find multiplier
            arg_index = line.index('-bm')
            if len(line)> arg_index+2:
                multiplier_index = arg_index+1
                multiplier = float(line[multiplier_index])
        except ValueError as err:
            pass  

        # Parse image texture
        image_path = os.path.join(os.path.dirname(self.__file_path), line[len(line)-1])
        image_loaded, image_data = self.__load_texture(image_path)

        if image_loaded:
            material:StandardMaterial = self.__get_current_material()
            material.normal_map_intensity = multiplier
            material.normal_map = image_data
        else:
            print("Could not load image in line {}, of file {}. Maybe the image name contains spaces, not currently supported.".format(line_number, self.__file_path))

    def __parse_metallic_map(self, line, line_number)-> None:
        line = line.split(' ')
        
        # Parse image texture
        image_path = os.path.join(os.path.dirname(self.__file_path), line[len(line)-1])
        image_loaded, image_data = self.__load_texture(image_path)

        if image_loaded:
            material:StandardMaterial = self.__get_current_material()
            material.metallic_map = image_data
        else:
            print("Could not load image in line {}, of file {}. Maybe the image name contains spaces, not currently supported.".format(line_number, self.__file_path))

    def __parse_roughness_map(self, line, line_number)-> None:
        line = line.split(' ')
        
        # Parse image texture
        image_path = os.path.join(os.path.dirname(self.__file_path), line[len(line)-1])
        image_loaded, image_data = self.__load_texture(image_path)

        if image_loaded:
            material:StandardMaterial = self.__get_current_material()
            material.roughness_map = image_data
        else:
            print("Could not load image in line {}, of file {}. Maybe the image name contains spaces, not currently supported.".format(line_number, self.__file_path))

    def __parse_ambient_occlusion_map(self, line, line_number)-> None:
        line = line.split(' ')
        
        # Parse image texture
        image_path = os.path.join(os.path.dirname(self.__file_path), line[len(line)-1])
        image_loaded, image_data = self.__load_texture(image_path)

        if image_loaded:
            material:StandardMaterial = self.__get_current_material()
            material.ambient_occlusion_map = image_data
        else:
            print("Could not load image in line {}, of file {}. Maybe the image name contains spaces, not currently supported.".format(line_number, self.__file_path))

    def __load_texture(self, texture_path) -> Tuple[bytes, int, int]:
        
        try:
            img = Image.open(texture_path)
            img_bytes = img.tobytes("raw", "RGBA", 0, -1)

            return True, (img_bytes, img.width, img.height)
        except FileNotFoundError as err:

            return False, None


class Wavefront(Model):
    """
    Imports a Wavefront .obj file as a Model

    Most common .obj file formats are supported. An .obj file may contain multiple meshes either named or anonymous.
    
    Parameters
    ----------
    file_path : str
        The file path where the .obj file to import is.
    calculate_smooth_normals : bool, default False
        Whether to calculate smooth normals or import/flat shade the model. 
        If set to False, the imported normals will populate the normals array of each mesh. If the file does not contain normals, then flat shading normals will be used.
        If set to True, the normals will not be imported, but rather calculated in order to achieve a smooth shading result.
    encoding : str, default 'utf-8'
        The encoding the .obj file has

    Examples
    --------
    >>> x = Wavefront('./teapot.obj')
    >>> x.meshes['teapot'] # used to get a named mesh of the .obj file with the name teapot
    >>> x.mesh_list[0] # used to get the first mesh found in the .obj file, either named or not. This is only recommended for use when there are anonymous meshes in the file.
    """
    __file_path : str
    __calculate_smooth_normals : bool
    __vertices : list
    __normals : list
    __texture_coords : list
    __obj_meshes : Dict[str, WavefrontObjectMesh]
    __obj_mesh_list : List[WavefrontObjectMesh]
    __materials: Dict[str, Material]

    __parse_dispatch : dict

    def __init__(self, file_path, calculate_smooth_normals=False, encoding = 'utf-8') -> None:

        assert(file_path is not (None or ""))

        super().__init__(self.__get_model_name_from_path(file_path))
        
        self.__file_path = file_path
        self.__encoding = encoding
        self.__calculate_smooth_normals = calculate_smooth_normals
        self.__materials: Dict[str, Material] = {} # A dictionary with keys the name of each Material and value the Material 
        
        self.__vertices = [] # Array with float4 with (x, y, z, w) like [[1.0, 1.0, 1.0, 1.0], [2.0, 1.5, 2.65, 1.0], ...]
        self.__normals = [] # Array with float3 with (x, y, z) like [[1.0, 1.0, 1.0], [2.0, 1.5, 2.65], ...]
        self.__texture_coords = [] # Array with float3 with (u, v, w) like [[1.0, 0.33, 0.6], [0.5, 0.5, 0.0], ...]

        self.__obj_meshes = {}
        self.__obj_mesh_list = []

        self.__parse_dispatch = {
            "mtllib" : self.__parse_mtllib,
            "o" : self.__parse_object,
            "v" : self.__parse_vertex,
            "vt": self.__parse_texture_coord,
            "vn" : self.__parse_normal,
            "f" : self.__parse_face,
            "usemtl" : self.__parse_use_material,
        }

        self.__parse_from_file()

        self.__convert_obj_meshes_to_meshes()

    def __get_current_mesh(self) -> WavefrontObjectMesh:
        if len(self.__obj_mesh_list) > 0:
            return self.__obj_mesh_list[len(self.__obj_mesh_list)-1]
        else: # If current mesh not exists create a new anonymous one
            current_mesh = WavefrontObjectMesh("")
            current_mesh.vertices = self.__vertices
            current_mesh.normals = self.__normals
            current_mesh.uv = self.__texture_coords
            self.__obj_mesh_list.append(current_mesh)
            return current_mesh 
    
    def __get_model_name_from_path(self, path) -> str:
        return Path(path).stem

    def __parse_from_file(self) -> None:
        try:
            with codecs.open(self.__file_path, encoding=self.__encoding) as f:
                
                line_number = 0
                # Parse file lines
                for line in f:
                    line_number +=1

                    line = line.strip()

                    # Line is empty or comment? Skip
                    if len(line)<1 or line[0] == "#":
                        continue

                    try:
                        parse_function = self.__parse_dispatch.get(line.split(' ')[0], self.__parse_unknown)
                        parse_function(line, line_number)
                    except Exception:
                        traceback.print_exc()
                        print("Exception occured while trying to read line %d from %s" % ( line_number, self.__file_path))
                        exit()
                    

        except FileNotFoundError as err:
            print("Could not load object, file %s not found" % self.__file_path)

    def __parse_object(self, line, line_number) -> None:
        line = line.split(None, 1)
        if len(line) > 1:
            mesh_name = line[1]
        else:
            mesh_name = ""

        current_mesh = WavefrontObjectMesh(name = mesh_name)
        current_mesh.vertices = self.__vertices
        current_mesh.normals = self.__normals
        current_mesh.uv = self.__texture_coords

        # Add current mesh to imported meshes
        self.__obj_mesh_list.append(current_mesh)
        if current_mesh.name != "":
            self.__obj_meshes[current_mesh.name] = current_mesh

    def __parse_vertex(self, line, line_number) -> None:

        line = line.split()

        vertex = [float(line[1]), float(line[2]), float(line[3])]

        # Check if w component exists in line, else use 1.0
        if len(line) > 4:
            vertex.append(float(line[4]))
        else:
            vertex.append(1.0)

        self.__vertices.append(vertex)

    def __parse_normal(self, line, line_number) -> None:
        line = line.split()

        self.__normals.append([float(line[1]), float(line[2]), float(line[3])])

    def __parse_texture_coord(self, line, line_number) -> None:

        line = line.split()

        # texture coord = [u, (v), (w)] .v,w are optional and default to 0.0
        texture_coord = [float(line[1])]
        
        # Has v component?
        if len(line)>2:
            texture_coord.append(float(line[2]))

            # Has w component?
            if len(line)>3:
                texture_coord.append(float(line[3]))
            else:
                texture_coord.append(0.0)

        else:
            texture_coord.append(0.0)
            texture_coord.append(0.0)

        self.__texture_coords.append(texture_coord)

    def __parse_face(self, line, line_number) -> None:
        # Faces are in the format: f 6/4/1 3/5/3 7/6/5, with vertex_index/texture_index/normal_index (texture or normal index may be missing)
        
        tokens = line.split()[1:]

        if len(tokens) == 3:
            self.__parse_triangle_face(tokens)
        elif len(tokens) == 4:
            self.__parse_quad_face(tokens)
        else:
            self.__parse_poly_face(line, line_number)

    def __parse_triangle_face(self, face_tokens) -> None:
        face = WavefrontObjectFace()

        # Triangles, so go until 3
        for i in range(3):
            index_set = face_tokens[i].split('/')

            vertex_index = int(index_set[0])
            if vertex_index<0:
                print("Relative vertex indices (%d) are not supported" % vertex_index)
                vertex_index = 0
                exit()

            face.vertex_indices.append(vertex_index)

            # Has texture coord index?
            if len(index_set)>1 and index_set[1]!="":
                texture_coords_index = int(index_set[1])
                if texture_coords_index<0:
                    print("Relative color indices (%d) are not supported" % color_index)
                    color_index = -1
                    exit()
                
                face.has_texture_coords = True
                face.texture_coords_indices.append(texture_coords_index)
            else:
                face.texture_coords_indices.append(-1)

            # Has normal index?
            if len(index_set)>2 and index_set[2]!="":
                normal_index = int(index_set[2])
                if normal_index<0:
                    print("Relative normal indices (%d) are not supported" % normal_index)
                    normal_index = -1
                    exit()

                face.has_normals = True
                face.normal_indices.append(normal_index)
            else:
                face.normal_indices.append(-1)

        current_mesh = self.__get_current_mesh()
        current_mesh.faces.append(face)
        pass
    
    def __parse_quad_face(self, face_tokens) -> None:
        """
        Convert quad into two triangle faces
        """
        # Convert into two triangles and parse
        self.__parse_triangle_face(face_tokens[:3])
        face_tokens.pop(1)
        self.__parse_triangle_face(face_tokens[:3])

    def __parse_poly_face(self, line, line_number) -> None:
        # TODO: Implement ear-clipping algorithm to convert to triangles
        print("Unsupported %s in line %d" % (line, line_number))

    def __parse_unknown(self, line, line_number) -> None:
        print("Unsupported command '%s' in file %s, line %d" % (line, self.__file_path, line_number))
    
    # Material Parsing
    def __parse_mtllib(self, line:str, line_number) -> None:
        line = line.split(None, 1)

        mtllib_file_name:str = line[1]
        
        extension_start_index = mtllib_file_name.rfind('.')
        if extension_start_index != -1:
            mtllib_name = mtllib_file_name[:extension_start_index]
        else:
            mtllib_name = mtllib_file_name
        
        # Parse mtllib
        material_importer = WavefrontMaterialLibrary(mtllib_name, os.path.join(os.path.dirname(self.__file_path), mtllib_file_name), self.__encoding)
        # Store materials locally
        for material in material_importer.materials:
            self.__materials[material.name] = material

    def __parse_use_material(self, line, line_number) -> None:
        line = line.split(None, 1)
        
        # Check command error
        if len(line) < 2:
            return
        
        material_name = line[1]

        current_mesh:WavefrontObjectMesh = self.__get_current_mesh()

        # TODO: Implement submeshes
        # NOTE: If the current mesh has a material attached to it, then this means that this is a new submesh
        #       Submeshes are not supported as of now but can be simulated by different meshes

        if current_mesh.material is None:
            current_mesh.material = self.__materials.get(material_name, Material("Default"))

        else:
            # Create submesh
            new_mesh = WavefrontObjectMesh(name = ("%s_0" %(current_mesh.name)) if current_mesh.name !="" else "")
            new_mesh.vertices = self.__vertices
            new_mesh.normals = self.__normals
            new_mesh.uv = self.__texture_coords

            # Add new mesh to imported meshes
            self.__obj_mesh_list.append(new_mesh)
            if new_mesh.name != "":
                self.__obj_meshes[new_mesh.name] = new_mesh

            new_mesh.material = self.__materials.get(material_name, Material("Default"))
            
    # ------- Conversion to standard mesh --------
    def __convert_obj_meshes_to_meshes(self) -> None:
        for obj_mesh in self.__obj_mesh_list:
            
            obj_mesh.convert_to_mesh(self.__calculate_smooth_normals)

            super().add_mesh(obj_mesh)