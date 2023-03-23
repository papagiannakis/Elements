"""
Texture classes

"""


import OpenGL.GL as gl
from PIL import Image

class Texture:
    """
    This Class is used for initializing simple 2D textures
    """

    CUBE_TEX_COORDINATES = [
    [0.0, 0.0],
    [1.0, 0.0],
    [1.0, 1.0],
    [0.0, 0.0],
    [1.0, 1.0],
    [0.0, 1.0]]*6


    def __init__(self,filepath):
        """
        Used to initialize a 2D texture
        """
        angle = -90

        img = Image.open(filepath)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img = img.rotate(angle) #need to rotate by 90 degrees
        image_data = img.convert("RGBA").tobytes()

        self._texture = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D,self._texture)
        
        #gl.glTexParameteri(gl.GL_TEXTURE_2D,gl.GL_TEXTURE_WRAP_S,gl.GL_MIRRORED_REPEAT)
        #gl.glTexParameteri(gl.GL_TEXTURE_2D,gl.GL_TEXTURE_WRAP_T,gl.GL_MIRRORED_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,gl.GL_TEXTURE_WRAP_S,gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,gl.GL_TEXTURE_WRAP_T,gl.GL_REPEAT)

        gl.glTexParameteri(gl.GL_TEXTURE_2D,gl.GL_TEXTURE_MIN_FILTER,gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,gl.GL_TEXTURE_MAG_FILTER,gl.GL_LINEAR)

        gl.glTexImage2D(gl.GL_TEXTURE_2D, #Target
                        0, # Level
                        gl.GL_RGBA, # Internal Format
                        img.width, # Width
                        img.height, # Height
                        0, # Border
                        gl.GL_RGBA, # Format
                        gl.GL_UNSIGNED_BYTE, # Type
                        image_data # Data
                        )
        gl.glGenerateMipmap(gl.GL_TEXTURE_2D)
    
    
    def bind(self):
        """
    Bind and Activate texture
    """
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D,self._texture)

    """
        unbind texture
    """
    def unbind(self):
        gl.glDeleteTextures(1,self._texture)


class texture_data:
    """
    A class storing the necessary texture data, such as height, width and data
    """

    def __init__(self,_height,_width,_data):
        self.set_height(_height)
        self.set_width(_width)
        self.set_data(_data)

    def set_height(self,h):
        self.height = h

    def set_width(self,w):
        self.width = w

    def set_data(self,d):
        self.data = d

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width
    
    def get_data(self):
        return self.data

class Texture3D:
    """
    This Class is used for initializing 3D textures using cube maps
    """


    def __init__(self, texture_faces: list):
        """
        Initializes a 3D texture using the texture data for all faces (texture_faces)
        """
        self._texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_CUBE_MAP, self._texture)
        
        count = 0
        for face in texture_faces:
            gl.glTexImage2D(gl.GL_TEXTURE_CUBE_MAP_POSITIVE_X+count, # Target
                            0, # Level
                            gl.GL_RGBA, # Internal Format
                            face.get_width(), # width
                            face.get_height(), # height
                            0, # border
                            gl.GL_RGBA, # format
                            gl.GL_UNSIGNED_BYTE, # Type
                            face.get_data() # Data
                            )
            count = count + 1
        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP, gl.GL_TEXTURE_WRAP_R, gl.GL_CLAMP_TO_EDGE)

    def bind(self):
        """
        Bind and Activate texture
        """
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_CUBE_MAP,self._texture)

    def unbind(self):
        """
        unbind texture
        """
        gl.glDeleteTextures(1,self._texture)
    

def get_texture_faces(front,back,top,bottom,left,right):
    """
    Takes 6 images as input and creates an array with their data that are used for cube mapping
    """
    faces = []
    front_img = Image.open(front)
    back_img = Image.open(back)
    top_img = Image.open(top)
    bottom_img = Image.open(bottom)
    left_img = Image.open(left)
    right_img = Image.open(right)

    faces.append(texture_data(right_img.height,right_img.width,right_img.convert("RGBA").tobytes())) #right face
    faces.append(texture_data(left_img.height,left_img.width,left_img.convert("RGBA").tobytes())) #left face
    faces.append(texture_data(top_img.height,top_img.width,top_img.convert("RGBA").tobytes())) #top face
    faces.append(texture_data(bottom_img.height,bottom_img.width,bottom_img.convert("RGBA").tobytes())) #bottom face
    faces.append(texture_data(front_img.height,front_img.width,front_img.convert("RGBA").tobytes())) #front face
    faces.append(texture_data(back_img.height,back_img.width,back_img.convert("RGBA").tobytes())) #back_img face

    return faces

def get_single_texture_faces(Tex_file,faces=6):
    """
    Creates an array with the data from a single image
    """
    img = Image.open(Tex_file)

    faces = [texture_data(img.height,img.width,img.convert("RGBA").tobytes()) for i in range(faces)]

    return faces