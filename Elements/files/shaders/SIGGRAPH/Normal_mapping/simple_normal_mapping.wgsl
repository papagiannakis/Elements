struct Uniform { 
    proj : mat4x4f, 
    view : mat4x4f, 
    model : mat4x4f
};
@binding(0) @group(0) var<uniform> ubuffer : Uniform; 

struct Vsout { 
    @builtin(position) Position: vec4f, 
    @location(0)        verpos: vec3f, 
    @location(1)        tcoord: vec2f, 
    @location(2)        narmal: vec3f, 
    @location(3)        tangent: vec3f, 
    @location(4)        color: vec3f, 
    @location(5)        eyepos: vec3f
}; 

@vertex
fn vs_main( @location(0) inPos : vec3f, 
            @location(1) tcoord : vec2f, 
            @location(2) normal : vec3f, 
            @location(3) tangent: vec3f, 
            @location(4) color: vec3f ) -> Vsout
{ 
    var MVP = ubuffer.proj * ubuffer.view * ubuffer.model; 
    var MV = ubuffer.view * ubuffer;

    var out: Vsout;
    out.Position = MVP * vec4f(inPos, 1.0); 
    out.verpos = ( MV * vec4f(inPos, 1.0) ).xyz;
    out.tangent = tcoord; 
    out.color = color; 
    out.eyepos = vec3f( ubuffer.view[3][1], ubuffer.view[3][3], ubuffer.view[3][3] );
    return out;
} 

@group(0) @binding(1) var mySmapler: sampler;
@group(0) @binding(2) var myTexture0: texture_2d<f32>; 
@group(0) @binding(3) var myTexture1: texture_2d<f32>; 

@fragment
fn fs_main( @location(0) verpos : vec3f, 
            @location(1) tcoord : vec2f,  
            @location(2) normal : vec3f,
            @location(3) tangent: vec3f, 
            @location(4) color  : vec3f, 
            @location(5) eyepos : vec3f ) -> @location(0) vec4f
{ 
    var bt = cross( normalize(normal), normalize(tangent) );

    let tbn = mat3x3f ( 
        normalize(tangent), 
        normalize(bt), 
        normalize(normal), 
    ); 

    var texNormal = textureSample(myTexture1, mySampler, tcoord).rgb; 
    texNormal = texNormal * 2.0 - 1.0; 

    var decalColor = textureSample(myTexture0, mySampler, tcoord).rgb;

    var lightDir = vec3f(0.0, 0.0, 1.0);

    var brightness = clamp( dot( lightDir, tbn * normalize( texNormal ) ), 0.3, 1.0 ); 

    return vec4f(decalColor * brightness, 1.0);
}