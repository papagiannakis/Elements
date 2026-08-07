# billboard_label_component.py - Reusable Billboard Label Component System

import os
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import OpenGL.GL as gl

from Elements.pyECSS.Component import Component, BasicTransform
from Elements.pyECSS.System import System
from Elements.pyECSS.Entity import Entity
import Elements.pyECSS.math_utilities as util
from Elements.pyGLV.GL.Textures import Texture
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyECSS.Component import RenderMesh
from Elements.definitions import SHADER_DIR


#shaders
BILLBOARD_VERT = (SHADER_DIR / "Billboard.vert").read_text()

BILLBOARD_FRAG = (SHADER_DIR / "Billboard.frag").read_text()
# BILLBOARD LABEL COMPONENT
class BillboardLabel(Component):
    """
    Component for creating labels.
    
    Use:
        label = scene.world.addComponent(entity, BillboardLabel(
            text="My Label",
            bg_rgba=(0.85, 0.10, 0.10, 0.88),
            world_height=0.6,
            offset_local=(0, 1.1, 0)
        ))
    """
    
    def __init__(self, 
                 text="Label",
                 bg_rgba= (0.9, 0.10, 0.10, 0.9),
                 fg_rgba= (1.0, 1.0, 1.0, 1.0),
                 world_height= 0.6,
                 offset_local= (0.0, 1.1, 0.0),
                 padding_px= 16,
                 font_size= 20,
                 name="BillboardLabel"):
        super().__init__()
        self.name =name
        self.text= text
        self.bg_rgba= bg_rgba
        self.fg_rgba= fg_rgba
        self.world_height= world_height
        self.offset_local= np.array(offset_local, dtype=np.float32)
        self.padding_px= padding_px
        self.font_size= font_size
        
        # Internal state
        self.label_entity = None
        self.shader = None
        self.texture = None
        self.world_width = 0.0
        self._initialized = False
    
    def init(self):
        """Initialize the billboard label"""
        if self._initialized:
            return
        
        # Create texture from text
        png_path, (px_w, px_h) = self._make_text_texture()
        self.texture = Texture(png_path)
        
        # Calculate world dimensions
        aspect = px_w / max(1, px_h)
        self.world_width = self.world_height * aspect
        
        self._initialized = True
    
    def _make_text_texture(self):
        """Generate a PNG texture with the label text"""
        try:
            font = ImageFont.truetype("arial.ttf", self.font_size)
        except:
            try:
                font = ImageFont.truetype("Arial.ttf", self.font_size)
            except:
                font = ImageFont.load_default()
        
        # Measure text size
        tmp = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
        d = ImageDraw.Draw(tmp)
        bbox = d.textbbox((0, 0), self.text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        W, H = tw + 2 * self.padding_px, th + 2 * self.padding_px
        
        # Create image with background
        img = Image.new("RGBA", (W, H), tuple(int(c * 255) for c in self.bg_rgba))
        draw = ImageDraw.Draw(img)
        draw.text((self.padding_px, self.padding_px), self.text, 
                 font=font, fill=tuple(int(c * 255) for c in self.fg_rgba))
        
        # Save to temp file
        tmpdir = tempfile.gettempdir()
        path = os.path.join(tmpdir, f"billboard_{abs(hash((self.text, W, H, self.bg_rgba)))}.png")
        img.save(path)
        
        return path, (W, H)
    
    def update(self):
        pass
    
    def accept(self, system):
        if hasattr(system, 'apply2BillboardLabel'):
            system.apply2BillboardLabel(self)

# to system gia ta labels
class BillboardLabelSystem(System):
    """ System for updating billboard labels to follow the camera.
    
    Use:
        labelSys = scene.world.createSystem(BillboardLabelSystem())
        # In render loop:
        labelSys.set_camera(view_matrix, projection_matrix)
        scene.world.traverse_visit(labelSys, scene.world.root)
    """   
          
    def __init__(self, name="BillboardLabelSystem"):
        super().__init__(name)
        self.view_matrix = util.identity()
        self.proj_matrix = util.identity()
    
    def set_camera(self, view_mat, proj_mat):
        """Set the current camera matrices"""
        self.view_matrix = view_mat
        self.proj_matrix = proj_mat
    
    def execute(self, entity, *args, **kwargs):
    
        if entity is None:
            return
        
        # Find the billboardLabel component and transform
        label_comp = None
        transform = None
        
        if hasattr(entity, 'getComponents'):
            for comp in entity.getComponents():
                if isinstance(comp, BillboardLabel):
                    label_comp = comp
                elif isinstance(comp, BasicTransform):
                    transform = comp
        
        if not label_comp or not label_comp._initialized or not transform:
            return
        offset_world = transform.l2world @ util.vec(*label_comp.offset_local, 1.0)
        center = offset_world[:3]
        
        # Extract camera right and up vectors from view matrix
        view_inv = np.linalg.inv(self.view_matrix)
        cam_right = view_inv[:3, 0]
        cam_up = view_inv[:3, 1]
        
        # Update shader uniforms
        if label_comp.shader:
            label_comp.shader.setUniformVariable(key='View', value=self.view_matrix, mat4=True)
            label_comp.shader.setUniformVariable(key='Proj', value=self.proj_matrix, mat4=True)
            label_comp.shader.setUniformVariable(key='center', value=center, float3=True)
            label_comp.shader.setUniformVariable(key='camRight', value=cam_right, float3=True)
            label_comp.shader.setUniformVariable(key='camUp', value=cam_up, float3=True)
            label_comp.shader.setUniformVariable(
                key='size',
                value=util.vec(label_comp.world_width, label_comp.world_height, 0.0),
                float3=True
            ) 

# functions copied from previews version without component (exactly the same as the presentation)
def create_billboard_label(scene, parent_entity, 
                          text="Label",
                          bg_rgba=(0.85, 0.10, 0.10, 0.88),
                          fg_rgba=(1.0, 1.0, 1.0, 1.0),
                          world_height=0.6,
                          offset_local=(0.0, 1.1, 0.0),
                          padding_px=16,
                          font_size=42):
    """Function to create a billboard label
        Arguments:
            scene: the Scene object
            parent_entity: Entity to attach the label to
            text: Label text
            bg_rgba: Background color rgba
            fg_rgba: text color rgba
            world_height: height of label in world
            offset_local: Offset from parent in local space se sxesi me to obj
            padding_px: Padding around text in pixels
            font_size: Font size in pixels
        
        Returns:
            label_entity, billboard_component
    """
    # Create the billboard component
    billboard = BillboardLabel(
        text=text,
        bg_rgba=bg_rgba,
        fg_rgba=fg_rgba,
        world_height=world_height,
        offset_local=offset_local,
        padding_px=padding_px,
        font_size=font_size,
        name=f"Billboard_{text}"
    )
    
    # Add to parent entity
    scene.world.addComponent(parent_entity, billboard)
    
    # Initialize the component
    billboard.init()
    
    # Create label entity as child
    label_entity = scene.world.createEntity(Entity(name=f"LabelEntity_{text}"))
    scene.world.addEntityChild(parent_entity, label_entity)
    billboard.label_entity = label_entity
    
    scene.world.addComponent(label_entity, BasicTransform(
        name=f"LabelTRS_{text}", 
        trs=util.identity()
    ))
    
    # Create quad
    quad_xy = np.array([
        [-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]
    ], dtype=np.float32)
    quad_uv = np.array([
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]
    ], dtype=np.float32)
    quad_idx = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
    
    # Add mesh
    mesh = scene.world.addComponent(label_entity, RenderMesh(name=f"LabelMesh_{text}"))
    mesh.vertex_attributes.append(quad_xy)
    mesh.vertex_attributes.append(quad_uv)
    mesh.vertex_index.append(quad_idx)
    
    # Add VAO
    scene.world.addComponent(label_entity, VertexArray())
    
    # Add texture
    scene.world.addComponent(label_entity, billboard.texture)
    
    # Add shader
    shader = scene.world.addComponent(
        label_entity,
        ShaderGLDecorator(Shader(
            vertex_source=BILLBOARD_VERT,
            fragment_source=BILLBOARD_FRAG
        ))
    )
    shader.setUniformVariable(key='uTex', value=billboard.texture, texture=True)
    billboard.shader = shader
    
    return label_entity, billboard