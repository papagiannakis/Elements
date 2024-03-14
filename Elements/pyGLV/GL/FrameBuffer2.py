import OpenGL.GL as gl
from imgui_bundle import imgui
import glm

class Framebuffer:
    def __init__(self, _width = 300, _height = 200):
        self.size = imgui.ImVec2(_width, _height);
        self.width = _width;
        self.height = _height;
        self.textureID = 0;
        self.CC = {"r" : 1, "b" : 1, "g" : 1, "a" : 1};
        self.renderID = 0;
        
        gl.glGenFramebuffers(1, self.fbo);
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo);
        
        
        # CREATE COLOR TEXTURE
        gl.glGenTextures(1, self.textureID);
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.textureID);
        gl.glTexImage2D(gl.GL_TEXTURE_2D, gl.GL_RGBA, self.width, self.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None);
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0);
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.textureID, 0);
        
        # CREATE DEPTH RENDERBUFFER 
        gl.glGenRenderbuffers(1, self.renderID);
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.renderID);
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_STENCIL_ATTACHMENT, gl.GL_RENDERBUFFER, self.renderID);
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0);
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_STENCIL_ATTACHMENT, gl.GL_RENDERBUFFER, self.renderID);
    
        
        # COMPLETENESS CHECK
        
        status = gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER);
        if status is not gl.GL_FRAMEBUFFER_COMPLETE:
            print("FAILED TO CREATE FRAMEBUFFER");
            exit(1);
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0);
        
    def __del__(self):
        gl.glDeleteFramebuffers(1, self.fbo);
        self.fbo = 0;
        self.textureID = 0;
    
    def getFBO(self):
        return self.fbo;
    
    def getTextureID(self):
        return self.textureID;
    
    def getRenderBufferID(self):
        return self.renderID;
    
    def getSize(self):
        return self.size;
    
    def setClearColor(self, r, b, g, a):
        self.CC["r"] = r;
        self.CC["b"] = b;
        self.CC["g"] = g;
        self.CC["a"] = a;
    
    def getClearColor(self):
        return self.CC;