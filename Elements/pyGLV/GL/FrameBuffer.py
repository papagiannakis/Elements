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
        self.depthId = 0;
        self.textureId = 0;
        
        self.color_render = 0;
        self.depth_render = 0;
        
    
    def createFrameBuffer(self):
        self.fbo = glGenFramebuffers(1);
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        self.generateTexture()
        #self.generateRenderbuffers();
        
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print("ERROR::FRAMEBUFFER:: Framebuffer is not complete!\n")

        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        
    
    def generateTexture(self):
        ##--------------- Main Texture --------------------##
        self.textureId = glGenTextures(1);
        
        glBindTexture(GL_TEXTURE_2D, self.textureId)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER);
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.width, self.height, 0, GL_RGB, GL_UNSIGNED_BYTE, None);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.textureId, 0);
        
        glBindTexture(GL_TEXTURE_2D, 0);
        
        ##--------------- Depth Attachment ----------------##
        #self.depthId = glGenTextures(1);

        #glBindTexture(GL_TEXTURE_2D, self.depthId)
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        #glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, self.width, self.height, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_BYTE, None);
        #glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depthId, 0);

        #glBindTexture(GL_TEXTURE_2D, 0);
    
    def generateRenderbuffers(self):
        self.color_render = glGenRenderbuffers(1);
        glBindRenderbuffer(GL_RENDERBUFFER, self.color_render);
        glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA8, self.width, self.height);
        glBindRenderbuffer(GL_RENDERBUFFER, 0);
        
        #self.depth_render = glGenRenderbuffers(1);
        #glBindRenderbuffer(GL_RENDERBUFFER, self.depth_render);
        #glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, self.width, self.height);
        #glBindRenderbuffer(GL_RENDERBUFFER, 0);
        
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, self.color_render);
        #glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.depth_render);

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
        
        glBindTexture(GL_TEXTURE_2D, 0);
        
        #glBindRenderbuffer(GL_RENDERBUFFER, self.color_render);
        #glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA8, _width, _height);
        #glBindRenderbuffer(GL_RENDERBUFFER, 0);
        
        #glBindRenderbuffer(GL_RENDERBUFFER, self.depth_render);
        #glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, _width, _height);
        #glBindRenderbuffer(GL_RENDERBUFFER, 0); 
        
        #glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, self.color_render);
        #glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.depth_render);
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        
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
        
        imgui.get_window_draw_list().add_image(
            self.textureId,
            p_min,
            p_max,
            imgui.ImVec2(1,1),
            imgui.ImVec2(0,0)
        )
        
        imgui.end()
    

        
        
        