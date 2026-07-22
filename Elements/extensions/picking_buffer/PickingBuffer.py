# PickingSystem.py
import Elements
import OpenGL.GL as gl
import numpy as np

from Elements.pyECSS.System import System
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.pyECSS.math_utilities as util
import sdl2
from typing import Optional, Tuple


PICKING_VERT = """#version 410
layout(location = 0) in vec4 vPosition;
uniform mat4 modelViewProj;
void main() {
    gl_Position = modelViewProj * vPosition;
}
"""

PICKING_FRAG = """#version 410
uniform vec3 objectIDColor;
out vec4 FragColor;
void main() {
    FragColor = vec4(objectIDColor, 1.0);
}
"""


class PickingSystem(System):
    def __init__(self, width: int, height: int):
        super().__init__("PickingSystem")
        
        self.width = width
        self.height = height
        
        # Shader container (initialized under GL context)
        self._shader = Shader(vertex_source=PICKING_VERT, fragment_source=PICKING_FRAG)
        self.shader_dec = ShaderGLDecorator(self._shader)
        
        # FBO resources
        self.fbo: Optional[int] = None
        self.tex_color: Optional[int] = None
        self.rbo_depth: Optional[int] = None
        
        # ID bookkeeping
        self._next_id = 1
        self.id_to_entity = {}
        self.entity_to_id = {}
        
        # Camera matrices (must be set by caller each frame)
        self.projMat = util.identity()
        self.view = util.identity()
        
        # State tracking
        self._rendering_picking_pass = False

        # Mouse state
        self._mouse_state = 0

    def init(self):
        """Call after GL context is ready."""
        self.shader_dec.init()
        self._init_fbo(self.width, self.height)

    def _init_fbo(self, w: int, h: int):
        """Initialize framebuffer objects."""
        self.fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        
        # Color texture
        self.tex_color = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_color)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB8, w, h, 0, 
                       gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, 
                                 gl.GL_TEXTURE_2D, self.tex_color, 0)
        
        # Depth renderbuffer
        self.rbo_depth = gl.glGenRenderbuffers(1)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.rbo_depth)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT24, w, h)
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, 
                                    gl.GL_RENDERBUFFER, self.rbo_depth)
        
        # Check framebuffer status
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("Picking FBO is not complete")
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)

    def resize(self, width: int, height: int):
        """Handle window resize."""
        if width <= 0 or height <= 0:
            return
            
        self.width = width
        self.height = height
        
        if self.tex_color:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_color)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB8, width, height, 0,
                           gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None)
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        
        if self.rbo_depth:
            gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self.rbo_depth)
            gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT24, 
                                     width, height)
            gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, 0)

    def set_camera_matrices(self, proj: np.ndarray, view: np.ndarray):
        """Set projection and view matrices."""
        self.projMat = proj
        self.view = view

    def begin_picking_pass(self):
        """Start picking pass - call before traversal."""
        self._next_id = 1
        self.id_to_entity.clear()
        self.entity_to_id.clear()
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glViewport(0, 0, self.width, self.height)
        
        # Clear with black (ID 0 = no object)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        # Optimize state for picking (disable unnecessary features)
        gl.glDisable(gl.GL_BLEND)
        gl.glDisable(gl.GL_MULTISAMPLE)
        gl.glDisable(gl.GL_DITHER)
        gl.glEnable(gl.GL_DEPTH_TEST)

    def end_picking_pass(self):
        """End picking pass - call after traversal."""
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def apply2VertexArray(self, vertexArray: VertexArray, event=None):
        """
        Called by traverse_visit. Renders entity with unique color ID.
        """            
        parent = vertexArray.parent
        if parent is None:
            return
            
        # Check if entity has RenderMesh
        compRenderMesh = parent.getChildByType(RenderMesh.getClassName())
        if not compRenderMesh:
            return
            
        # Get or assign ID for this entity
        if parent in self.entity_to_id:
            obj_id = self.entity_to_id[parent]
        else:
            obj_id = self._next_id
            self._next_id += 1
            self.id_to_entity[obj_id] = parent
            self.entity_to_id[parent] = obj_id
            
            # Safety: ensure ID doesn't exceed 24-bit RGB range
            if obj_id >= (1 << 24):
                print(f"Warning: Picking ID overflow! Max 16.7 million objects supported.")
                return
        
        # Encode ID to normalized RGB
        r = ((obj_id) & 0xFF) / 255.0
        g = ((obj_id >> 8) & 0xFF) / 255.0
        b = ((obj_id >> 16) & 0xFF) / 255.0
        
        # Get model matrix
        basicTrans = parent.getChildByType(BasicTransform.getClassName())
        model = basicTrans.l2world if basicTrans else util.identity()
        
        # Compute MVP
        mvp = self.projMat @ self.view @ model
        
        # Set uniforms
        self.shader_dec.setUniformVariable(key='modelViewProj', value=mvp, mat4=True)
        self.shader_dec.setUniformVariable(key='objectIDColor', 
                                          value=np.array([r, g, b], dtype=np.float32), 
                                          float3=True)
        
        # Draw
        self.shader_dec.enableShader()
        vertexArray.draw()
        self.shader_dec.disableShader()

    def pick(self, x, y, window_height: Optional[int] = None) -> Tuple[Optional[object], int]:
        """
        Read pixel at screen coordinates (x, y).
        Returns (entity, object_id) or (None, 0) if nothing.
        """
        if window_height is None:
            window_height = self.height
            
        # Clamp coordinates to viewport bounds
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, window_height - 1))
        
        # Convert y from top-left to bottom-left origin
        read_y = window_height - y - 1
        
        gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER, self.fbo)
        
        # Read pixel
        px = gl.glReadPixels(x, read_y, 1, 1, gl.GL_RGB, gl.GL_UNSIGNED_BYTE)
        
        gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER, 0)
        
        # Parse pixel data
        try:
            if isinstance(px, (bytes, bytearray)):
                r, g, b = px[0], px[1], px[2]
            else:
                # Handle PyOpenGL's nested sequence
                r, g, b = int(px[0][0]), int(px[0][1]), int(px[0][2])
        except (IndexError, TypeError, ValueError):
            return None, 0
        
        picked_id = int(r) | (int(g) << 8) | (int(b) << 16)
        
        if picked_id == 0:
            return None, 0
            
        return self.id_to_entity.get(picked_id, None), picked_id
    

    def check_for_click(self):
        """Capture mouse click from SDL mouse state."""
        x = sdl2.Sint32()
        y = sdl2.Sint32()

        buttons = sdl2.SDL_GetMouseState(x, y)

        left_down = buttons & sdl2.SDL_BUTTON_LMASK
        prev_left_down = self._mouse_state & sdl2.SDL_BUTTON_LMASK

        self._mouse_state = buttons

        if left_down and not prev_left_down:
            return int(x.value), int(y.value)


    def cleanup(self):
        """Clean up GL resources."""
        if self.fbo:
            gl.glDeleteFramebuffers(1, [self.fbo])
            self.fbo = None
        if self.tex_color:
            gl.glDeleteTextures(1, [self.tex_color])
            self.tex_color = None
        if self.rbo_depth:
            gl.glDeleteRenderbuffers(1, [self.rbo_depth])
            self.rbo_depth = None

    def __del__(self):
        """Destructor for cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass