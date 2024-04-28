import wgpu

F32 = 4
I32 = 4

SHADER_TYPES = { 
    'vec2f' : 2,
    'vec3f' : 3,
    'vec4f' : 4,
    'vec4i' : 4,
    'mat4x4' : 16
} 

SHADER_TYPE_BUFFER_STRIDE = { 
    2 : wgpu.VertexFormat.float32x2,
    3 : wgpu.VertexFormat.float32x3,
    4 : wgpu.VertexFormat.float32x4,
}