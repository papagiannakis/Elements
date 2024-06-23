struct uniforms {
    projection: mat4x4f, 
    view: mat4x4f,
    model: mat4x4f
};

@group(0) @binding(0) var<uniform> ubuffer: uniforms;
@group(1) @binding(0) var myTexture: texture_2d<f32>;
@group(1) @binding(1) var mySampler: sampler;

struct VertexInput {
    @location(0) a_vertices: vec3f, 
    @location(1) a_uvs: vec2f,
}
struct VertexOutput {
    @builtin(position) Position: vec4<f32>,
    @location(0) v_tex: vec2<f32>,
    @location(1) v_position: vec3<f32> // Added to match the pipeline expectation
}; 

@vertex
fn vs_main( 
    in: VertexInput
) -> VertexOutput {

    var out: VertexOutput; 

    out.Position = ubuffer.projection * ubuffer.view * ubuffer.model * vec4<f32>(in.a_vertices, 1.0); 
    out.v_tex = in.a_uvs; 
    out.v_position = out.Position.xyz;
    return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
    return textureSample(myTexture, mySampler, in.v_tex); 
}