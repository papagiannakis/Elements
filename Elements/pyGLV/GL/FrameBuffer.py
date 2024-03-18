from OpenGL.GL.framebufferobjects import *
from OpenGL.GL import *
from imgui_bundle import imgui

class FrameBuffer:
    def __init__(self, width = None, height = None):
        if width is None:
            self.width = 800;
        else:
            self.width = width;
            
        if height is None:
            self.height = 600;
        else:
            self.height = height;
        
        self.width = 200;
        self.height = 200;
        
        self.fbo = 0;
        self.rbo = 0;
        self.textureId = 0;
        
    
    def createFrameBuffer(self):
        self.fbo = glGenFramebuffers(1);
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        self.generateTexture();
        self.generateRenderbuffer();

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print("ERROR::FRAMEBUFFER:: Framebuffer is not complete!\n")

        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        
    
    def generateTexture(self):
        self.textureId = glGenTextures(1);
        
        glBindTexture(GL_TEXTURE_2D, self.textureId)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.width, self.height, 0, GL_RGB, GL_UNSIGNED_BYTE, None);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.textureId, 0);
        
        glBindTexture(GL_TEXTURE_2D, 0);
        
    
    def generateRenderbuffer(self):
        self.rbo = glGenRenderbuffers(1);
        
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo);
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.rbo);
        
        glBindRenderbuffer(GL_RENDERBUFFER, 0);
        
    def bindFramebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo);

    def unbindFramebuffer(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0);

    def rescaleFramebuffer(self, _width, _height):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glBindTexture(GL_TEXTURE_2D, self.textureId);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, _width, _height, 0, GL_RGB, GL_UNSIGNED_BYTE, None);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.textureId, 0);


        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo);
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, _width, _height);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.rbo);
        
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glBindTexture(GL_TEXTURE_2D, 0);
        glBindRenderbuffer(GL_RENDERBUFFER, 0);
        
    def drawFramebuffer(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) 
        
        imgui.begin("Scene")
        
        WIDTH = int(imgui.get_content_region_avail().x);
        HEIGHT = int(imgui.get_content_region_avail().y);
        self.rescaleFramebuffer(WIDTH, HEIGHT);
        glViewport(0,0, WIDTH, HEIGHT);
        
        p_min = imgui.ImVec2(imgui.get_cursor_screen_pos().x, imgui.get_cursor_screen_pos().y);
        p_max = imgui.ImVec2(p_min.x + WIDTH, p_min.y + HEIGHT);
        
        print()
        imgui.get_window_draw_list().add_image(
            self.textureId,
            p_min,
            p_max,
            imgui.ImVec2(0,1),
            imgui.ImVec2(1,0)
        )
        
        imgui.end()
    

        
        
        