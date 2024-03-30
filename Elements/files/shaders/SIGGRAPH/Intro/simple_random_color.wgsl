struct vsout  
{ 
    @builtin(position) Position : vec4<f32>,
    @location(0) p : vec3<f32>
}; 


fn random(st:vec2<f32>) -> f32
{ 
    return fract(sin(dot(st.xy, vec2<f32>(12.9898,78.233)))*43758.5453123);
}


@vertex
fn vs_main( @builtin(vertex_index) VertexIndex : u32 ) -> vsout
{ 
    var pos : array<vec2<f32>, 3> = array<vec2<f32>, 3> 
    (
        vec2<f32>(0.0, 0.5),
        vec2<f32>(-0.5, -0.5),
        vec2<f32>(0.5, -0.5),
    ); 

    var out : vsout;
    out.Position = vec4<f32>(pos[VertexIndex], 0.0, 1.0);
    out.p = vec3<f32>(pos[VertexIndex], 0.0); 
    return out;
} 

@fragment
fn fs_main( @location(0) p : vec3<f32> ) -> @location(0) vec4<f32>
{ 
    var r = random( p.xy );
    var g = random( p.xy * 2.0 ); 
    var b = random( p.xy * 4.0 );  
    return vec4<f32>(r, g, b, 1.0);
}