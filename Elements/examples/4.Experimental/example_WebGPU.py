import time 

import glm

import wgpu    
import numpy as np   
import glfw
import Elements.definitions as definitions

from Elements.pyGLV.GUI.Viewer import GLFWWindow, RenderDecorator
from Elements.pyGLV.GL.Shader import ShaderLoader  
from Elements.pyECSS.Event import EventManager
from Elements.pyGLV.GUI.windowEvents import EventTypes 
from Elements.pyGLV.GUI.Viewer import button_map 
import Elements.pyECSS.math_utilities as util 

"""
This example renders a simple textured rotating cube. 
""" 
_eye = util.vec(2.5, 2.5, 2.5)
_target = util.vec(0.0, 0.0, 0.0)
_up = util.vec(0.0, 1.0, 0.0)

camt = {};
camt["x"] = 0; camt["y"] = 0; camt["z"] = 0; 

camr = {};
camr["x"] = 0; camr["y"] = 0; camr["z"] = 0; 

cams = {};
cams["x"] = 0; cams["y"] = 0; cams["z"] = 0; 

_updateCamera = None
# test_example = true 

def resetAll():
    camt["x"] = 0.0
    camt["y"] = 0.0
    camt["z"] = 0.0
    camr["x"] = 0.0
    camr["y"] = 0.0
    camr["z"] = 0.0
    cams["x"]= 1.0
    cams["y"]= 1.0
    cams["z"]= 1.0
    
def createViewMatrix(eye, lookAt, upVector): 
    global _eye 
    global _target
    global _up 
    global _updateCamera
    
    _eye = util.vec(tuple(eye)) 
    _target = util.vec(tuple(lookAt)) 
    
    #self._up = tuple(upVector)
    #directionVector = util.normalise(lookAt - eye) 
    #rightVector = util.normalise(np.cross(directionVector, upVector))
    #upVector = util.normalise(np.cross(rightVector, directionVector)) 
    #self.wrapeeWindow._updateCamera = util.lookat(eye, lookAt, upVector) 

    _updateCamera = glm.transpose(glm.lookAtLH(_eye, _target, _up))   
    
def updateCamera(moveX, moveY, moveZ, rotateX, rotateY):   
    global _eye 
    global _target
    global _up 
    global _updateCamera 
    
    cameraspeed = 0.2
    teye = np.array(_eye)
    ttarget = np.array(_target)
    tup = np.array(_up)

    forwardDir = util.normalise(ttarget - teye)
    rightDir = util.normalise(np.cross(forwardDir, tup))

    if rotateX:
        rotMatY = util.rotate(tup, camr["x"] * cameraspeed*15)
        transMatY = util.translate(ttarget) @ rotMatY @ util.translate(-ttarget)
        teye = transMatY @ np.append(teye, [1])
        teye = teye[:-1] / teye[-1]
    elif rotateY:
        rotMatX = util.rotate(rightDir, -camr["y"] * cameraspeed*15)
        transMatX = util.translate(ttarget) @ rotMatX @ util.translate(-ttarget)
        teye = transMatX @ np.append(teye, [1])
        teye = teye[:-1] / teye[-1]
    elif moveX or moveY:
        panX = -cameraspeed * camt["x"] * rightDir
        panY = -camt["y"] * cameraspeed * tup
        teye += panX + panY
        ttarget += panX + panY
    elif moveZ:
        zoom =  np.sign(camt["z"]) * cameraspeed * forwardDir
        teye += zoom
        ttarget += zoom
    createViewMatrix(teye, ttarget, tup)

def cameraHandling(x, y, height, width):
    # keystatus = sdl2.SDL_GetKeyboardState(None)
    resetAll()

    if abs(x) > abs(y):
        camr["x"] = np.sign(x) #event.wheel.x/height*180
        updateCamera(False, False,False, True, False)
    else:
        camr["y"] = np.sign(y) #event.wheel.y/width*180
        updateCamera(False, False,False, False, True)

# Create a canvas to render to
#canvas = WgpuCanvas(title="wgpu cube") 
canvas = GLFWWindow(windowHeight=800, windowWidth=1200, wgpu=True, windowTitle="Wgpu Example")
canvas.init()
canvas.init_post() 

width = canvas._windowWidth 
height = canvas._windowHeight

# Create a wgpu device
adapter = wgpu.gpu.request_adapter(power_preference="high-performance")
device = adapter.request_device()

# Prepare present context
present_context = canvas.get_context()
render_texture_format = present_context.get_preferred_format(device.adapter)
present_context.configure(device=device, format=render_texture_format)

#Simple Cube
vertex_data = np.array([
    [-0.5, -0.5, 0.5, 1.0],
    [-0.5, 0.5, 0.5, 1.0],
    [0.5, 0.5, 0.5, 1.0],
    [0.5, -0.5, 0.5, 1.0], 
    [-0.5, -0.5, -0.5, 1.0], 
    [-0.5, 0.5, -0.5, 1.0], 
    [0.5, 0.5, -0.5, 1.0], 
    [0.5, -0.5, -0.5, 1.0]
],dtype=np.float32) 
color_data = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [0.0, 1.0, 1.0, 1.0]
], dtype=np.float32)

#index arrays for above vertex Arrays

index_data = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) #rhombus out of two triangles

# Use numpy to create a struct for the uniform
uniform_dtype = np.dtype([
    ("proj", np.float32, (4, 4)),
    ("view", np.float32, (4, 4)),
    ("model", np.float32, (4, 4)),
    ("tint", np.float32, (4,)),
    ("time", np.float32),
    ("padding", np.float32, (3,)),
]) 

angle = glfw.get_time()
S = glm.scale(glm.mat4x4(1.0), glm.vec3(0.5));  
T1 = glm.translate(glm.mat4x4(1.0), glm.vec3(0.0, 0.0, 0.0))
R1 = glm.rotate(glm.mat4x4(1.0), angle, glm.vec3(0.0, 0.0, 1.0))

model = T1 @ S  

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
# eye = glm.vec3(2.5, 2.5, 2.5) 
# target = glm.vec3(0.0, 0.0, 0.0)
# up = glm.vec3(0.0, 1.0, 0.0)
_updateCamera = glm.transpose(glm.lookAtLH(eye, target, up))  
view = _updateCamera

ratio = width / height 
near = 0.001
far = 1000.0 

proj = glm.transpose(glm.perspectiveLH(glm.radians(60), ratio, near, far))

uniform_data = np.array((
    np.array(proj),
    np.array(view),
    np.array(model),
    [1.0, 1.0, 1.0, 1.0],
    1.0,
    [1.0, 1.0, 1.0]
), dtype=uniform_dtype)

# Create vertex buffer, and upload data
vertex_buffer = device.create_buffer_with_data(
    data=vertex_data, usage=wgpu.BufferUsage.VERTEX
) 

color_buffer = device.create_buffer_with_data(
    data=color_data, usage=wgpu.BufferUsage.VERTEX
)

# Create index buffer, and upload data
index_buffer = device.create_buffer_with_data(
    data=index_data, usage=wgpu.BufferUsage.INDEX
)

# Create uniform buffer - data is uploaded each frame
uniform_buffer = device.create_buffer(
    size=uniform_data.nbytes, usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
)


# GLSL
# vertex_shader = ShaderLoader(definitions.SHADER_DIR / "simple_mvp_vertex.vert");
# fragment_shader = ShaderLoader(definitions.SHADER_DIR / "simple_mvp_fragment.frag");
# Vshader = device.create_shader_module(code=vertex_shader, label="vert"); 
# Fshader = device.create_shader_module(code=fragment_shader, label="frag"); 

#WGSL
shader_code = ShaderLoader(definitions.SHADER_DIR / "simple_mvp2_shader.wgsl");
shader = device.create_shader_module(code=shader_code);

# We always have two bind groups, so we can play distributing our
# resources over these two groups in different configurations.
bind_groups_entries = [[]]
bind_groups_layout_entries = [[]]

bind_groups_entries[0].append(
    {
        "binding": 0,
        "resource": {
            "buffer": uniform_buffer,
            "offset": 0,
            "size": uniform_buffer.size,
        },
    }
)
bind_groups_layout_entries[0].append(
    {
        "binding": 0,
        "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
        "buffer": {"type": wgpu.BufferBindingType.uniform},
    }
)


# Create the wgou binding objects
bind_group_layouts = []
bind_groups = []

for entries, layout_entries in zip(bind_groups_entries, bind_groups_layout_entries):
    bind_group_layout = device.create_bind_group_layout(entries=layout_entries)
    bind_group_layouts.append(bind_group_layout)
    bind_groups.append(
        device.create_bind_group(layout=bind_group_layout, entries=entries)
    )

pipeline_layout = device.create_pipeline_layout(bind_group_layouts=bind_group_layouts)


# %% The render pipeline

render_pipeline = device.create_render_pipeline(
    layout=pipeline_layout,
    vertex={
        "module": shader,
        "entry_point": "vs_main", 
        "buffers": [
            {
                "array_stride": vertex_data.shape[1] * 4,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32x4,
                        "offset": 0,
                        "shader_location": 0,
                    },
                ],
            },
            {
                "array_stride": color_data.shape[1] * 4, 
                "step_mode": wgpu.VertexStepMode.vertex, 
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32x4,
                        "offset": 0,
                        "shader_location": 1,
                    },
                ]
            }
        ], 
    },
    primitive={
        "topology": wgpu.PrimitiveTopology.triangle_list,
        "front_face": wgpu.FrontFace.ccw,
        "cull_mode": wgpu.CullMode.front,
    },
    depth_stencil={
            "format": wgpu.TextureFormat.depth24plus,
            "depth_write_enabled": True,
            "depth_compare": wgpu.CompareFunction.less,
            "stencil_front": {
                "compare": wgpu.CompareFunction.always,
                "fail_op": wgpu.StencilOperation.keep,
                "depth_fail_op": wgpu.StencilOperation.keep,
                "pass_op": wgpu.StencilOperation.keep,
            },
            "stencil_back": {
                "compare": wgpu.CompareFunction.always,
                "fail_op": wgpu.StencilOperation.keep,
                "depth_fail_op": wgpu.StencilOperation.keep,
                "pass_op": wgpu.StencilOperation.keep,
            },
            "stencil_read_mask": 0,
            "stencil_write_mask": 0,
            "depth_bias": 0,
            "depth_bias_slope_scale": 0.0,
            "depth_bias_clamp": 0.0,
        },
    multisample=None,
    fragment={
        "module": shader,
        "entry_point": "fs_main",
        "targets": [
            {
                "format": render_texture_format,
                "blend": {
                    "alpha": (
                        wgpu.BlendFactor.one,
                        wgpu.BlendFactor.zero,
                        wgpu.BlendOperation.add,
                    ),
                    "color": (
                        wgpu.BlendFactor.one,
                        wgpu.BlendFactor.zero,
                        wgpu.BlendOperation.add,
                    ),
                },
            }
        ],
    },
) 

def draw_frame():  
    global proj  
    global view
    global _updateCamera
    
    texture = present_context.get_current_texture();
    textureWidth = texture.width; 
    textureHeight = texture.height; 
    
    # Update uniform transform 
    ratio = canvas._windowWidth/canvas._windowHeight
    near = 0.001
    far = 1000.0 

    proj = glm.transpose(glm.perspectiveLH(glm.radians(60), ratio, near, far))   
    view = _updateCamera
     
    uniform_data = np.array((
    np.array(proj),
    np.array(view),
    np.array(model),
    [1.0, 1.0, 1.0, 1.0],
    1.0,
    [1.0, 1.0, 1.0]
    ), dtype=uniform_dtype) 
    
    # Upload the uniform struct
    tmp_buffer = device.create_buffer_with_data(
        data=uniform_data, usage=wgpu.BufferUsage.COPY_SRC
    )

    command_encoder = device.create_command_encoder()
    command_encoder.copy_buffer_to_buffer(
        tmp_buffer, 0, uniform_buffer, 0, uniform_data.nbytes
    )
    
    depth_texture : wgpu.GPUTexture = device.create_texture(
            label="depth_texture",
            size=[textureWidth, textureHeight, 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.depth24plus,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT
        )

    depth_texture_view : wgpu.GPUTextureView = depth_texture.create_view(
        label="depth_texture_view",
        format=wgpu.TextureFormat.depth24plus,
        dimension="2d",
        aspect=wgpu.TextureAspect.depth_only,
        base_mip_level=0,
        mip_level_count=1,
        base_array_layer=0,
        array_layer_count=1,
    )

    current_texture_view = texture.create_view()
    render_pass = command_encoder.begin_render_pass( 
        color_attachments=[
            {
                "view": current_texture_view,
                "resolve_target": None,
                "clear_value": (0.1, 0.1, 0.1, 0),
                "load_op": wgpu.LoadOp.clear,
                "store_op": wgpu.StoreOp.store,
            }
        ],
        depth_stencil_attachment={
                "view": depth_texture_view,
                "depth_clear_value": 1.0,
                "depth_load_op": wgpu.LoadOp.clear,
                "depth_store_op": wgpu.StoreOp.store,
                "depth_read_only": False,
                "stencil_clear_value": 0,
                "stencil_load_op": wgpu.LoadOp.clear,
                "stencil_store_op": wgpu.StoreOp.store,
                "stencil_read_only": True,
            },
    )

    render_pass.set_pipeline(render_pipeline)
    render_pass.set_index_buffer(index_buffer, wgpu.IndexFormat.uint32)
    render_pass.set_vertex_buffer(slot=0, buffer=vertex_buffer) 
    render_pass.set_vertex_buffer(slot=1, buffer=color_buffer)
    for bind_group_id, bind_group in enumerate(bind_groups):
        render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)
    render_pass.draw_indexed(index_data.size, 1, 0, 0, 0)
    render_pass.end()

    device.queue.submit([command_encoder.finish()])

    canvas.request_draw()


canvas.request_draw(draw_frame)

running = True

while running:
    width = canvas._windowWidth
    height = canvas._windowHeight  
    wcenter = width / 2
    hcenter = height / 2 
    
    event = canvas.event_input_process();   
    if event: 
        if running:
            if glfw.get_key(canvas.gWindow, glfw.KEY_ESCAPE) == glfw.PRESS:  
                canvas._running = False
                running = False 

        if event.type == EventTypes.SCROLL:
                x = event.data["dx"]
                y = event.data["dy"]
                cameraHandling(x,y,width,height)
            
        if event.type == EventTypes.MOUSE_MOTION:
            buttons = event.data["buttons"]  
            
            if button_map[glfw.MOUSE_BUTTON_2] in canvas._pointer_buttons:
                x = np.floor(event.data["x"] - wcenter) 
                y = np.floor(event.data["y"] - hcenter) 
                cameraHandling(x, y, height, width)
        
    if canvas._need_draw:
        canvas.display()
        canvas.display_post()
# %%
