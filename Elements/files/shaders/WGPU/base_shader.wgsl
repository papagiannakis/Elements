struct uniforms {
    projection: mat4x4f, 
    view: mat4x4f,
    model: mat4x4f,
    near_far: vec2f
};

@group(0) @binding(0) var<uniform> ubuffer: uniforms;
@group(1) @binding(0) var diffuse_texture: texture_2d<f32>;
@group(1) @binding(1) var diffuse_sampler: sampler;

struct VertexInput {
    @location(0) a_vertices: vec3f, 
    @location(1) a_uvs: vec2f,
}
struct VertexOutput {
    @builtin(position) Position: vec4<f32>,
    @location(0) v_tex: vec2<f32>,
    @location(1) v_position: vec3<f32> // Added to match the pipeline expectation
};
struct FragOutput { 
    @builtin(frag_depth) depth: f32,
    @location(0) color: vec4f
} 

fn LinearizeDepth( 
    depth: f32,
    near: f32,
    far: f32,
) -> f32 {   

    let zNdc = 2 * depth - 1; 
    let zEye = (2 * far * near) / ((far + near) - zNdc * (far - near)); 
    let linearDepth = (zEye - near) / (far - near);
    return linearDepth;
}

@vertex
fn vs_main( 
    in: VertexInput
) -> VertexOutput {

    var model = transpose(ubuffer.model);
    var view = transpose(ubuffer.view); 
    var projection = transpose(ubuffer.projection);

    var out: VertexOutput; 
    out.Position = projection * view * model * vec4<f32>(in.a_vertices, 1.0); 
    out.v_tex = in.a_uvs; 
    out.v_position = out.Position.xyz;
    return out;
}

@fragment
fn fs_main(
    in: VertexOutput
) -> FragOutput { 

    var out: FragOutput; 
    out.depth = LinearizeDepth(in.Position.z, ubuffer.near_far.x, ubuffer.near_far.y);
    out.color = textureSample(diffuse_texture, diffuse_sampler, in.v_tex);
    return out; 
}