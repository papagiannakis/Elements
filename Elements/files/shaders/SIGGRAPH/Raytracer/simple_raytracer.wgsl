struct vsout 
{ 
    @builtin(position) Position : vec4<f32>, 
    @location(0) uv : vec2<f32>
}; 

@vertex
fn vs_main( @builtin(vertex_index) VertexIndex : u32 ) -> vsout
{ 
    var s = 0.9;

    var pos = array<vec2<f32>, 4> 
    (
        vec2<f32>(-s, s),
        vec2<f32>(-s, -s),
        vec2<f32>(s, s),
        vec2<f32>(s, -s)
    );  

    s = 1.0;

    var uvs = array<vec2<f32>, 4> 
    (
        vec2<f32>(-s, s),
        vec2<f32>(-s, -s),
        vec2<f32>(s, s),
        vec2<f32>(s, -s)
    );   

    var ret : vsout;
    ret.Position = vec4<f32>(pos[VertexIndex], 0.0, 1.0);
    ret.uv = uvs[VertexIndex] * 0.5 + 0.5;
    return ret;
} 

struct hitdata 
{  
    rayLenght : f32,
    normal : vec3<f32>,
}; 

fn rayIntersectSphere(ray : vec3<f32>, dir : vec3<f32>, center : vec3<f32>, radius : f32) -> hitdata
{  
    var rc = ray - center; 
    var c = dot(rc, rc) - (radius * radius);
    var b = dot(dir, rc);
    var d = b * b - c;
    var t = -b - sqrt(abs(d));

    if (d < 0.0 || t < 0.0) 
    { 
        t = 0.0;
    } 

    var hit : hitdata; 
    var hitpos = ray + dir * t;
    hit.normal = normalize(hitpos - center);
    hit.rayLenght = t;
    return hit;
} 

fn background( rd:vec3<f32> ) -> vec3<f32>
{ 
    let sky = max(0.0, dot(rd, vec3<f32>(0.0, 0.2, -0.7)));
    return pow(sky, 1.0) * vec3<f32>(0.5, 0.6, 0.7);
} 

@fragment
fn fs_main( @location(0) uvs : vec2<f32> ) -> @location(0) vec4<f32>
{ 
    var uv = (-1 + 2.0 * uvs);
    var ro = vec3<f32>(0.0, 0.0, -6.0);
    var rd = normalize(vec3<f32>(uv, 1.0)); 
    var transmit = vec3<f32>(1.0);
    var light = vec3<f32>(0.0); 

    var epsilon = 0.001; 

    var bounceCount = 2.0;

    for (var i = 0.0; i < bounceCount; i = i + 1.0) 
    { 
        var data = rayIntersectSphere(ro, rd, vec3<f32>(0., 0., 0.), 3.5); 

        if (data.rayLenght > 0.0) 
        {
            transmit = transmit * 0.9; 
            var nml = data.normal;
            ro = ro + rd * data.rayLenght;
            rd = reflect(rd, nml);  
            ro = ro + rd * epsilon;
        } 
        else 
        { 
            light = light + transmit * background(rd);
            break;
        }
    } 

    return vec4<f32>(light, 1.0);
}