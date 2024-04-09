struct VertexOut 
{ 
    @builtin(position) Position: vec4<f32>, 
    @location(0)       pos: vec3<f32>, 
    @location(1)       normal: vec3<f32>, 
}

struct uniforms 
{ 
    proj: mat4x4f, 
    view: mat4x4f,
    model: mat4x4f,   
    timestep: f32,
} 

@group(0)@binding(0) 
var<uniform> u_uniforms: uniforms; 

fn getPos(pp: vec3f, t: f32) -> vec3f 
{ 
    var ret = vec3f( pp.x, 0.0, pp.z );
    ret.y = sin( pp.x * 3.0 + t * 2.0 ) * sin( pp.x * 1.0 + t ) * 0.3 + 
            cos( pp.z * 1.5 + t ) * 0.3 - 
            sin( pp.x * 0.6 + t * 3.0 ) * 0.05 - 
            sin( pp.z * 0.5 + t * 3.0 ) * 0.05;  
    
    return ret;
} 

@vertex
fn vs_main( @location(0) inPos : vec3<f32> ) -> VertexOut 
{
    var p0 = getPos( inPos, u_uniforms.timestep );
    var p2 = getPos( inPos + vec3<f32>(0.0, 0.0, 0.01), u_uniforms.timestep );
    var p1 = getPos( inPos + vec3<f32>(0.01, 0.0, 0.0 ), u_uniforms.timestep ); 

    var normal=cross( p1-p0, p2-p0 ); normal = normalize( normal ); 
    normal = normalize( normal );
    
    var mvp = u_uniforms.proj * u_uniforms.view * u_uniforms.model;

    var out: VertexOut;
    out.Position = mvp * vec4<f32>( p0, 1.0);
    out.pos = p0;  
    out.normal = normal;  
    return out;
}; 


@fragment
fn fs_main( @location(0) pos : vec3f, 
            @location(1) normal : vec3f ) -> @location(0) vec4f 
{ 
    let lightdir = normalize( vec3f(0.0, -0.5, 1.0) );
    let diffuse = clamp( dot(normal, lightdir), 0.0, 1.0 ); 
    return vec4f( 0.0, 0.0,  0.5 + diffuse, 1.0 );
}