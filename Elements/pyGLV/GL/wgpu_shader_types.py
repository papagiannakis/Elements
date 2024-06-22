import wgpu

F32 = 4
I32 = 4

SHADER_TYPES = { 
    'vec2f' : 4 * F32, 
    'vec2i' : 4 * I32, 
    'vec3f' : 4 * F32, 
    'vec3i' : 4 * I32,
    'vec4f' : 4 * F32,
    'vec4i' : 4 * I32,
    'mat4x4f' : 16 * F32,
    'mat4x4i' : 16 * I32,
    'array<vec2f>' : 4 * F32, 
    'array<vec2i>' : 4 * I32, 
    'array<vec3f>' : 4 * F32, 
    'array<vec3i>' : 4 * I32,
    'array<vec4f>' : 4 * F32,
    'array<vec4i>' : 4 * I32,
    'array<mat4x4f>' : 16 * F32,
    'array<mat4x4i>' : 16 * I32, 
    'i32' : 4 * I32, 
    'f32' : 4 * F32 
} 

SHADER_ATTRIBUTE_STRIDE = { 
    'vec2f' :wgpu.VertexFormat.float32x2,
    'vec2i' : wgpu.VertexFormat.uint32x2,
    'vec3f' : wgpu.VertexFormat.float32x3,
    'vec3i' : wgpu.VertexFormat.uint32x3,
    'vec4f' : wgpu.VertexFormat.float32x4,
    'vec4i' : wgpu.VertexFormat.uint32x4
} 

SHADER_ATTRIBUTE_TYPES = { 
    'vec2f' : 2 * F32,
    'vec2i' : 2 * I32,
    'vec3f' : 3 * F32,
    'vec3i' : 3 * I32,
    'vec4f' :4 * F32,
    'vec4i' :4* I32, 
} 