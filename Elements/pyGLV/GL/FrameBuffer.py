from OpenGL.GL.framebufferobjects import *
from OpenGL.GL import *
from imgui_bundle import imgui
from Elements.pyGLV.GUI.Guizmos import Gizmos

first_run = True;

class FrameBuffer:
    def __init__(self, width = None, height = None):
        self.width = width if width is not None else 800
        self.height = height if height is not None else 600
        
        self.fbo = 0;
        self.textureId = 0;
        self.depthId = 0;
    
        self.gizmo = Gizmos(imgui.get_current_context());
    
    def createFrameBuffer(self):
        self.fbo = glGenFramebuffers(1);
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        self.generateTexture()
        
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print("ERROR::FRAMEBUFFER:: Framebuffer is not complete!\n")

        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        
    
    def generateTexture(self):
        ##--------------- Main Texture --------------------##
        self.textureId = glGenTextures(1);
        
        glBindTexture(GL_TEXTURE_2D, self.textureId)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None);
        glBindTexture(GL_TEXTURE_2D, 0);

        glBindTexture(GL_TEXTURE_2D, self.depthId)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, self.width, self.height, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_BYTE, None);
        glBindTexture(GL_TEXTURE_2D, 0);
    
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.textureId, 0);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depthId, 0);
        

    def bindFramebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo);

    def unbindFramebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0);

    def rescaleFramebuffer(self, _width, _height):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glBindTexture(GL_TEXTURE_2D, self.textureId);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, _width, _height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None);
        glBindTexture(GL_TEXTURE_2D, 0);

        glBindTexture(GL_TEXTURE_2D, self.depthId);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, _width, _height, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_BYTE, None);
        glBindTexture(GL_TEXTURE_2D, 0);

        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.textureId, 0);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depthId, 0);

        glBindFramebuffer(GL_FRAMEBUFFER, 0);

        self.width = _width;
        self.height = _height;
        
        
    def drawFramebuffer(self): 
        global first_run
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) 
        
        imgui.begin("Scene")
        
        w = imgui.get_window_size().x
        h = imgui.get_window_size().y
        x = imgui.get_window_pos().x;
        y = imgui.get_window_pos().y;

        WIDTH = int(w);
        HEIGHT = int(h);

        if  WIDTH != self.width or HEIGHT != self.height or first_run:
            first_run = False;
            self.rescaleFramebuffer(WIDTH, HEIGHT);
            glViewport(0,0, WIDTH, HEIGHT);
        
        p_min = imgui.ImVec2(imgui.get_cursor_screen_pos().x, imgui.get_cursor_screen_pos().y);
        p_max = imgui.ImVec2(p_min.x + WIDTH, p_min.y + HEIGHT);
        
        imgui.get_window_draw_list().add_image(
            self.textureId,
            p_min,
            p_max,
            imgui.ImVec2(1,1),
            imgui.ImVec2(0,0)
        )
        
        self.gizmo.drawGizmo(x, y, w, h);
        
        imgui.end()
    

        
        
        