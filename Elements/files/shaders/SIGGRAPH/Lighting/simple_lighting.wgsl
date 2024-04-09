struct uniforms 
{ 
    proj : mat4x4f, 
    view : mat4x4f, 
    model : mat4x4f
};
@binding(0)@group(0) var<uniform> ubuffer : uniforms; 

struct VertexOut
{ 
    @builtin(position) Position: vec4f, 
    @location(0) color: vec3f,
    @location(1) normal: vec3f, 
    @location(2) uvs: vec2f
};

fn calcUV ( p: vec3f ) -> vec2f
{ 
    let norm = normalize( p );

    let PI : f32 = 3.1415926f;

    let u = (( atan2(norm.x, norm.z) / PI ) + 1.0f) * 0.5f; 
    let v = ( asin(norm.y) / PI ) + 0.5f; 

    return vec2f(u, v);
} 

@vertex 
fn vs_main( @location(0) inPos: vec3f, 
            @location(1) inClr: vec3f, 
            @location(2) inNorm: vec3f ) -> VertexOut
{ 
    let mvp = ubuffer.proj * ubuffer.view * ubuffer.model;

    var out : VertexOut;
    out.Position = mvp * ubuffer.model * vec4f( inPos, 1.0 );
    out.uvs = calcUV( inPos );
    out.normal = inNorm;
    out.color = inClr;
    return out;
}

@group(0)@binding(2) var u_sampler: sampler; 
@group(0)@binding(1) var u_texture: texture_2d<f32>; 

@fragment
fn fs_main( @location(0) inClr: vec3f, 
            @location(1) inNrom: vec3f, 
            @location(2) inUvs: vec2f ) -> @location(0) vec4f 
{ 
    let texCol = textureSample(u_texture, u_sampler, inUvs);

    let dir = vec3f(0.0, 1.0, 0.0);

    let illum = abs( dot(dir, inNrom) );

    return vec4f( texCol.xyz * illum, 1.0 );
}