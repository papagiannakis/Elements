struct Camera {
   forwards: vec4f,
   right: vec4f,
   up: vec4f 
}

@group(0) @binding(0) var<uniform> camera: Camera;
@group(1) @binding(0) var skyTexture: texture_cube<f32>;
@group(1) @binding(1) var skySampler: sampler;

struct VertexOutput {
    @builtin(position) Position : vec4<f32>,
    @location(0) direction : vec3<f32>,
}

// const positions = array<vec2<f32>, 6>(
//     vec2<f32>( 1.0,  1.0),
//     vec2<f32>( 1.0, -1.0),
//     vec2<f32>(-1.0, -1.0),
//     vec2<f32>( 1.0,  1.0),
//     vec2<f32>(-1.0, -1.0),
//     vec2<f32>(-1.0,  1.0)
// );

@vertex
fn vs_main( 
    @location(0) aVertex: vec2f
) -> VertexOutput {

    var output : VertexOutput;
    output.Position = vec4f(aVertex, 1.0, 1.0);
    var x: f32 = -aVertex.x;
    var y: f32 = -aVertex.y;

    output.direction = normalize(camera.forwards.xyz + x * camera.right.xyz + y * camera.up.xyz); 
    return output;
}

@fragment
fn fs_main(
    @location(0) direction : vec3<f32>
) -> @location(0) vec4<f32> { 

    return textureSample(skyTexture, skySampler, direction);
}