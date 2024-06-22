struct uniforms {
    projection: mat4x4f, 
    view: mat4x4f,
};

struct models_storage {
    model: array<mat4x4f> 
};

@group(0) @binding(0) var<uniform> ubuffer: uniforms;
@group(0) @binding(1) var<storage, read> models: models_storage;
@group(1) @binding(0) var myTexture: texture_2d<f32>;
@group(1) @binding(1) var mySampler: sampler;

struct VertexInput { 
    @location(0) a_vertices: vec3f, 
    @location(1) a_uvs: vec2f,
    @location(2) a_indices: vec3f,
}
struct VertexOutput {
    @builtin(position) Position: vec4<f32>,
    @location(0) v_tex: vec2<f32>
}; 

@vertex
fn vs_main(
    @builtin(instance_index) ID: u32,
    in: VertexInput
) -> VertexOutput {

    var out: VertexOutput; 

    var model = models.model[ID];
    out.v_tex = in.a_uvs;

    out.Position = ubuffer.projection * ubuffer.view * model * vec4<f32>(in.a_vertices, 1.0); 
    return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
    return textureSample(myTexture, mySampler, in.v_tex); 
}