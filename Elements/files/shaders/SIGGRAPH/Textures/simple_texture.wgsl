struct uniforms 
{ 
    proj: mat4x4f, 
    view: mat4x4f, 
    model: mat4x4f
};
@group(0)@binding(0) var<uniform> ubuffer : uniforms;


struct VertexOut 
{ 
    @builtin(position) Position: vec4f, 
    @location(0)       Color: vec4f,
    @location(1)       Uvs: vec2f, 
};

@vertex
fn vs_main( @location(0) inPos: vec3f, 
            @location(1) inClr: vec3f, 
            @location(2) inUv:  vec2f ) -> VertexOut 
{ 
    var mvp = ubuffer.proj * ubuffer.view * ubuffer.model;

    var out: VertexOut;
    out.Position = mvp * vec4f(inPos, 1.0);
    out.Uvs = inUv;
    out.Color = vec4f(inClr, 1.0);
    return out;
} 

@group(0)@binding(2) 
var mySampler: sampler; 

@group(0)@binding(1) 
var myTexture: texture_2d<f32>;  

@fragment
fn fs_main( @location(0) inClr: vec3f, 
            @location(1) inUv: vec2f ) -> @location(0) vec4f
{ 
    return textureSample(myTexture, mySampler, inUv); 
}