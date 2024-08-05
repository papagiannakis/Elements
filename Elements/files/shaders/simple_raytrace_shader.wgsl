@group(0)@binding(0) var screen_sampler : sampler;
@group(0)@binding(1) var color_buffer : texture_2d<f32>;

struct VertexOutput
{ 
    @builtin(position) Position: vec4<f32>,
    @location(0) TexCoord: vec2<f32>,
} 

@vertex
fn vs_main(@builtin(vertex_indtex) VertexIndex: u32) -> VertexOutput
{ 
    let positions = array<vec2<f32>, 6>
    (
        vec2<f32>(1.0, 1.0),
        vec2<f32>(1.0, -1.0),
        vec2<f32>(-1.0, -1.0),
        vec2<f32>(1.0, 1.0),
        vec2<f32>(-1.0, -1.0),
        vec2<f32>(-1.0, 1.0),
    ) 

    let texCoord = array<vec2<f32>, 6>
    (
        vec2<f32>(1.0, 0.0),
        vec2<f32>(1.0, 1.0),
        vec2<f32>(0.0, 1.0),
        vec2<f32>(1.0, 0.0),
        vec2<f32>(0.0, 1.0),
        vec2<f32>(0.0, 0.0),
    ) 

    var output: VertexOutput;
    output.Position = vec4<f32>(positions[VertexIndex], 0.0, 0.1);
    output.TexCoord = texCoord[VertexIndex];
    return output;
} 

@fragment
fn fs_main(@location(0) TexCoord: vec<f32>) -> @location(0) vec4<f32>
{ 
    return textureSample(color_buffer, screen_sampler, TexCoord);
}
