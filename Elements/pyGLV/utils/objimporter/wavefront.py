import codecs
from Elements.pyGLV.utils.objimporter.wavefront_obj_face import WavefrontObjectFace
from Elements.pyGLV.utils.objimporter.wavefront_obj_mesh import WavefrontObjectMesh
from Elements.pyGLV.utils.objimporter.mesh import Mesh

class Wavefront:
    """
    Imports a Wavefront .obj file

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
    meshes : dict # The named meshes of the imported object in a dict with their names as keys, each containing its vertices/normals/uvs
    mesh_list : list # All the meshes of the imported object in a list, each containing its vertices/normals/uvs

    __file_path : str
    __calculate_smooth_normals : bool
    __mtllibs : list
    __vertices : list
    __normals : list
    __texture_coords : list
    __obj_meshes : dict
    __obj_mesh_list : list

    __parse_dispatch : dict

    def __init__(self, file_path, calculate_smooth_normals=False, encoding = 'utf-8') -> None:
        self.__file_path = file_path
        self.__calculate_smooth_normals = calculate_smooth_normals
        self.__mtllibs = []
        
        self.__vertices = [] # Array with float4 with (x, y, z, w) like [[1.0, 1.0, 1.0, 1.0], [2.0, 1.5, 2.65, 1.0], ...]
        self.__normals = [] # Array with float3 with (x, y, z) like [[1.0, 1.0, 1.0], [2.0, 1.5, 2.65], ...]
        self.__texture_coords = [] # Array with float3 with (u, v, w) like [[1.0, 0.33, 0.6], [0.5, 0.5, 0.0], ...]

        self.__obj_meshes = {}
        self.__obj_mesh_list = []

        self.meshes = {} # Dictionary to store the Meshes of the obj file imported by name
        self.mesh_list = [] # Stores all the meshes of the obj file imported. (Can also have anonymous meshes)

        self.__parse_dispatch = {
            "mtllib" : self.__parse_mtllib,
            "o" : self.__parse_object,
            "v" : self.__parse_vertex,
            "vt": self.__parse_texture_coord,
            "vn" : self.__parse_normal,
            "f" : self.__parse_face,
            "usemtl" : self.__parse_use_material,
        }

        self.__parse_from_file(encoding)

        self.__convert_obj_meshes_to_meshes()

    def __get_current_mesh(self) -> WavefrontObjectMesh:
        if len(self.__obj_mesh_list) > 0:
            return self.__obj_mesh_list[len(self.__obj_mesh_list)-1]
        else: # If current mesh not exists create a new anonymous one
            current_mesh = WavefrontObjectMesh("")
            self.__obj_mesh_list.append(current_mesh)
            return current_mesh 
    
    def __parse_from_file(self, encoding) -> None:
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
            print("Could not load object, file %s not found" % self.__file_path)

    def __parse_mtllib(self, line, line_number) -> None:
        line = line.split(' ')

        self.__mtllibs.append(line[1]) # The name of the mtllib

    def __parse_object(self, line, line_number) -> None:
        line = line.split(' ')
        if len(line) > 1:
            mesh_name = line[1]
        else:
            mesh_name = ""

        current_mesh = WavefrontObjectMesh(name = mesh_name)

        # Add current mesh to imported meshes
        self.__obj_mesh_list.append(current_mesh)
        if current_mesh.name != "":
            self.__obj_meshes[current_mesh.name] = current_mesh

    def __parse_vertex(self, line, line_number) -> None:

        line = line.split(' ')

        vertex = [float(line[1]), float(line[2]), float(line[3])]

        # Check if w component exists in line, else use 1.0
        if len(line) > 4:
            vertex.append(float(line[4]))
        else:
            vertex.append(1.0)

        self.__vertices.append(vertex)

    def __parse_normal(self, line, line_number) -> None:
        line = line.split(' ')

        self.__normals.append([float(line[1]), float(line[2]), float(line[3])])

    def __parse_texture_coord(self, line, line_number) -> None:

        line = line.split(' ')

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
        
        tokens = line.split(' ')[1:]

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

            face.vertex_indices.append(vertex_index)

            # Has texture coord index?
            if len(index_set)>1 and index_set[1]!="":
                texture_coords_index = int(index_set[1])
                if texture_coords_index<0:
                    print("Relative color indices (%d) are not supported" % color_index)
                    color_index = -1
                
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
        print("Unsupported %s in line %d" % (line, line_number))

    def __parse_use_material(self, line, line_number) -> None:
        line = line.split(' ')
        
        current_mesh = self.__get_current_mesh()
        current_mesh.material = line[1]

    def __parse_unknown(self, line, line_number) -> None:
        print("Unsupported command %s in line %d" % (line, line_number))
    
    def __convert_obj_meshes_to_meshes(self) -> None:
        
        for obj_mesh in self.__obj_mesh_list:

            mesh = Mesh.from_objmesh(self.__vertices, self.__normals, self.__texture_coords, obj_mesh, self.__calculate_smooth_normals)

            self.mesh_list.append(mesh)
            if mesh.name != "":
                self.meshes[mesh.name] = mesh
