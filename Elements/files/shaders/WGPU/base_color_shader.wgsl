struct uniforms {
    projection: mat4x4f, 
    view: mat4x4f,
    model: mat4x4f,
    color: vec3f
};

@group(0) @binding(0) var<uniform> ubuffer: uniforms;

struct VertexInput {
    @location(0) a_vertices: vec3f, 
}
struct VertexOutput {
    @builtin(position) Position: vec4<f32>,
}; 

@vertex
fn vs_main( 
    in: VertexInput
) -> VertexOutput {

    var model = transpose(ubuffer.model);
    var view = transpose(ubuffer.view); 
    var projection = transpose(ubuffer.projection);

    var out: VertexOutput; 
    out.Position = projection * view * model * vec4<f32>(in.a_vertices, 1.0); 
    return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> { 
    return vec4f(ubuffer.color, 1.0);
}