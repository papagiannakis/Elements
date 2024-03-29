import OpenGL.GL as gl 
from imgui_bundle import imgui


first_run = True;

class FrameBuffer:

    _instance = None;

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, width = None, height = None, context = None):
        if not hasattr(self, 'init'):
            self.init = True;
            self._use = False;

            self.width = width if width is not None else 800
            self.height = height if height is not None else 600
            
            self.fbo = 0;
            self.textureId = 0;
            self.depth_rbo = 0;
    
    def createFrameBuffer(self):
        self.fbo = gl.glGenFramebuffers(1);
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)

        self.generateTexture()
        self.generateRenderbuffers()
        
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            print("ERROR::FRAMEBUFFER:: Framebuffer is not complete!\n")

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0);
        
    
    def generateTexture(self):
        ##--------------- Color Texture --------------------##
        self.textureId = gl.glGenTextures(1);
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.textureId)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_BORDER);
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_BORDER);
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.width, self.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None);
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0);
    

        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self.textureId, 0);

        
    def generateRenderbuffers(self):
        ##---------------- Depth Renderbuffer --------------##
        self.depth_rbo = gl.glGenRenderbuffers(1);
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.depth_rbo)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT, self.width, self.height);
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0);

        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_RENDERBUFFER, self.depth_rbo)

    def bindFramebuffer(self):
        if self._use:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo);
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            gl.glClearColor(0.0, 0.0, 0.0, 1.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT | gl.GL_STENCIL_BUFFER_BIT)
            gl.glClearDepth(1.0);
            gl.glDisable(gl.GL_CULL_FACE)
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glDepthFunc(gl.GL_LESS)

    def unbindFramebuffer(self):
        if self._use:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0);

    def rescaleFramebuffer(self, _width, _height):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.textureId);
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, _width, _height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None);
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0);

        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.depth_rbo)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT, _width, _height);
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0);
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0);

        self.width = _width;
        self.height = _height;
        
        
    def drawFramebuffer(self): 
        global first_run

        if first_run:
            self._use = True;

        WIDTH = int(imgui.get_window_size().x);
        HEIGHT = int(imgui.get_window_size().y);

        if  WIDTH != self.width or HEIGHT != self.height or first_run:
            first_run = False;
            self.rescaleFramebuffer(WIDTH, HEIGHT);
            gl.glViewport(0,0, WIDTH, HEIGHT);
        
        p_min = imgui.ImVec2(imgui.get_cursor_screen_pos().x, imgui.get_cursor_screen_pos().y);
        p_max = imgui.ImVec2(p_min.x + WIDTH, p_min.y + HEIGHT);

        imgui.get_window_draw_list().add_image(
            self.textureId,
            p_min,
            p_max,
            imgui.ImVec2(1,1),
            imgui.ImVec2(0,0)
        )
        
    

        
        
        