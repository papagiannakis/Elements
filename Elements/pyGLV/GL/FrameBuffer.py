import OpenGL.GL as gl
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
        self.vao = 0;
        self.rbo = 0;
        self.textureId = 0;
        self.shader = 0;
        
    
    def createFrameBuffer(self):
        gl.glGenFramebuffers(1, self.fbo)
        gl.glBindFramebuffer(gl.gl.GL_FRAMEBUFFER, self.fbo)
        
        gl.glGenTextures(1, self.textureId)
        gl.glBindTexture(gl.gl.GL_TEXTURE_2D, self.textureId)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, self.width, self.height, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR);
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.texture_id, 0);

        gl.glGenRenderbuffers(1, self.rbo);
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.rbo);
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH24_STENCIL8, self.width, self.height);
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_STENCIL_ATTACHMENT, gl.GL_RENDERBUFFER, self.rbo);

        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            print("ERROR::FRAMEBUFFER:: Framebuffer is not complete!\n")

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0);
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0);
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0);
        
        
    def bindFramebuffer(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo);

    def unbindFramebuffer(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0);

    def rescaleFramebuffer(self, _width, _height):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.textureId);
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, _width, _height, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR);
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.textureId, 0);

        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.rbo);
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH24_STENCIL8, _width, _height);
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_STENCIL_ATTACHMENT, gl.GL_RENDERBUFFER, None);
        
    def drawFramebuffer(self):
        imgui.begin("Scene")
        
        width = imgui.get_content_region_avail().x;
        height = imgui.get_content_region_avail().y;
        self.rescaleFramebuffer(width, height);
        gl.glViewport(0,0, width, height);
        
        p_min = imgui.ImVec2(imgui.get_cursor_pos_x(), imgui.get_cursor_pos_y());
        p_max = imgui.ImVec2(p_min.x + width, p_min.y + height);
        
        imgui.get_window_draw_list().add_image(
            self.textureId,
            p_min,
            p_max,
            imgui.ImVec2(0,1),
            imgui.ImVec2(1,0)
        )
        
        imgui.end()
    
        
        
        