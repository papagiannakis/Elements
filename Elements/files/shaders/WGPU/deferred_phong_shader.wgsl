struct uniforms {
    view_pos: vec3f,
    light_pos: vec3f, 
    screen_size: vec2f,
    near_far: vec2f
};

@group(0) @binding(0) var<uniform> ubuffer:     uniforms;
@group(1) @binding(0) var g_position_texture:   texture_2d<f32>;
@group(1) @binding(1) var g_normal_texture:     texture_2d<f32>;
@group(1) @binding(2) var g_color_texture:      texture_2d<f32>;
@group(1) @binding(3) var ssao_texture:         texture_2d<f32>;

struct VertexOutput { 
    @builtin(position) Position: vec4<f32>,
    @location(0) uv: vec2<f32>
}
struct FragOutput { 
    @builtin(frag_depth) depth: f32,
    @location(0) color: vec4f
};

@fragment
fn fs_main(
    in: VertexOutput
) -> FragOutput { 
    var out: FragOutput;

    var pos_coord = in.uv * ubuffer.screen_size; 
    // var pos_texel = vec2u(u32(pos_coord.x), u32(pos_coord.y)); 
    var pos_texel = vec2u(pos_coord);  

    let light_color = vec3f(1.0, 1.0, 0.8);

    var near = ubuffer.near_far.x;
    var far = ubuffer.near_far.y;

    var frag_pos = textureLoad(g_position_texture, pos_texel, 0).xyz;
    var frag_norm = textureLoad(g_normal_texture, pos_texel, 0).xyz;
    var frag_color = textureLoad(g_color_texture, pos_texel, 0).xyz; 
    var frag_occlusion = textureLoad(ssao_texture, pos_texel, 0).x; 

    var lighting = frag_color * frag_occlusion * 0.6;
    // var lighting = frag_color * 0.3;
    var view_dir = normalize(ubuffer.view_pos - frag_pos); 

    var light_dir = normalize(ubuffer.light_pos - frag_pos);
    var diffuse = max(dot(frag_norm, light_dir), 0.0) * frag_color * light_color;

    lighting = lighting + diffuse;

    out.depth = textureLoad(g_normal_texture, pos_texel, 0).a; 
    out.color = vec4f(lighting, 1.0);
    return out;
}