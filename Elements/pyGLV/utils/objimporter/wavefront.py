import codecs
from Elements.pyGLV.GL.objimporter.wavefront_obj_face import WavefrontObjectFace
from Elements.pyGLV.GL.objimporter.wavefront_obj_mesh import WavefrontObjectMesh
from Elements.pyGLV.GL.objimporter.mesh import Mesh

class Wavefront:
    """
    Class to import a Wavefront .obj file

    Most common .obj file formats are supported.
    """
    def __init__(self, file_path) -> None:
        self.__file_path = file_path
        self.__mtllibs = []
        self.materials = {}
        
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

        self.__parse_from_file()

        self.__convert_obj_meshes_to_meshes()

    def __get_current_mesh(self) -> WavefrontObjectMesh:
        if len(self.__obj_mesh_list) > 0:
            return self.__obj_mesh_list[len(self.__obj_mesh_list)-1]
        else:
            current_mesh = WavefrontObjectMesh()
            self.__obj_mesh_list.append(current_mesh)
            return current_mesh 
    
    def __parse_from_file(self) -> None:
        try:
            with codecs.open(self.__file_path, encoding='utf-8') as f:
                
                line_number = 0
                # Parse file lines
                for line in f:
                    line_number +=1

                    line = line.strip()

                    # Line is comment? Skip
                    if line[0] == "#" or len(line)<=1:
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

        vertex = [[float(line[1]), float(line[2]), float(line[3])]]

        # Check if w component exists in line, else use 1.0
        if len(line) > 4:
            vertex.append(float(line[4]))
        else:
            vertex.append(1.0)

        self.__vertices.append([float(line[1]), float(line[2]), float(line[3])])

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

            # Has color index?
            if len(index_set)>1 and index_set[1]!="":
                color_index = int(index_set[1])
                if color_index<0:
                    print("Relative color indices (%d) are not supported" % color_index)
                    color_index = -1
                
                face.texture_coords_indices.append(color_index)
            else:
                face.texture_coords_indices.append(-1)

            # Has normal index?
            if len(index_set)>2 and index_set[2]!="":
                normal_index = int(index_set[2])
                if normal_index<0:
                    print("Relative normal indices (%d) are not supported" % normal_index)
                    normal_index = -1

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

            mesh = Mesh.from_objmesh(self.__vertices, self.__normals, self.__texture_coords, obj_mesh)

            self.mesh_list.append(mesh)
            if mesh.name != "":
                self.meshes[mesh.name] = mesh
