struct Uniforms { 
    proj        :mat4x4f,
    view        :mat4x4f,
    model       :mat4x4f, 
    lightView   :mat4x4f,
    lightProj   :mat4x4f
};
@binding(0)@group(0) var<uniform> u_buffer: Uniforms; 

struct VSout { 
    @builtin(position) Position: vec4f,
    @location(0)       normal: vec3f, 
    @location(1)       pos: vec4f
}; 

@vertex
fn vs_main(@location(0) normal: vec3f, 
            @location(1) inPos: vec3f) -> VSout
{ 
    var out: VSout;

    var lmvp = u_buffer.lightProj * u_buffer.lightView * u_buffer.model; 

    out.Position = lmvp * vec4f(inPos, 1.0);
    out.pos = lmvp * vec4f(inPos, 1.0); 

    let n = normalize( normal ); 
    out.normal = ( u_buffer.model * vec4f(n, 0.0) ).xyz;

    return out;
} 

struct GFXTextureOutput { 
    @location(0) tex0 : vec4f
}; 

@fragment
fn fs_main( @location(0) normal: vec3f,
            @location(1) pos: vec4f ) -> GFXTextureOutput 
{ 
    var depth = pos.z / pos.w;

    var out: GFXTextureOutput;
    out.tex0 = vec4f( depth, depth, depth, 1.0 );
    return out;
}