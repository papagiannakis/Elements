struct VertexOut 
{ 
    @builtin(position) Position: vec4<f32>, 
    @location(0)       Color: vec4<f32>
}

struct uniforms 
{ 
    proj: mat4x4f, 
    view: mat4x4f, 
    model: mat4x4f
} 

@group(0)@binding(0) 
var<uniform> u_uniforms: uniforms;

@vertex
fn vs_main(@location(0) in_pos: vec3<f32>,
            @location(1) in_color: vec3<f32>) -> VertexOut
{ 
    var pos = u_uniforms.proj * u_uniforms.view * u_uniforms.model * vec4f(in_pos, 1.0);

    var out: VertexOut; 
    out.Position = vec4f(pos);
    out.Color = vec4f(in_color, 1.0); 
    return out;
} 

@fragment
fn fs_main(@location(0) in_color: vec4<f32>) -> @location(0) vec4<f32> 
{ 
    return vec4<f32>(in_color);
}