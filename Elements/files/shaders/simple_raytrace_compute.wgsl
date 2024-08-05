@group(0)@binding(0) var color_buffer: texture_storage_2d<rgb8unorm, write>;

@compute @workgroup_size(1,1,1)
fn main(@builtin(global_invocation_id) GlobalInvocationID: vec3<u32>)
{
    let screen_pos : vec3<i32> = vec3<i32>(i32(GlobalInvocationID.x), i32(GlobalInvocationID.y));

    var pixel_color : vec3<f32> = vec3<f32>(0.0, 0.0, 0.0);


    textureStorage(color_buffer, screen_pos, vec4<f32>(pixel_color, 1.0));
}