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

    var frag_pos = textureLoad(g_position_texture, pos_texel, 0).xyz;
    var frag_norm = textureLoad(g_normal_texture, pos_texel, 0).xyz;
    var frag_color = textureLoad(g_color_texture, pos_texel, 0).xyz; 
    var frag_occlusion = textureLoad(ssao_texture, pos_texel, 0).x; 

    let color = frag_color;
    let normal = normalize(frag_norm);
    let light_color = vec3f(1.0, 1.0, 0.85);
    let light_pos = ubuffer.light_pos; 
    let view_pos = ubuffer.view_pos;

    let ambient = 0.4 * light_color * frag_occlusion;

    let light_dir = normalize(light_pos - frag_pos); 
    let diff = max(dot(light_dir, normal), 0.0); 
    let diffuse = diff * light_color;

    let view_dir = normalize(view_pos - frag_pos);
    let hafway_dir = normalize(light_dir + view_dir);
    let spec = pow(max(dot(normal, hafway_dir), 0.0), 64.0);
    let specular = spec * light_color; 

    let lighting = (ambient + diffuse + specular) * color;  

    out.depth = textureLoad(g_normal_texture, pos_texel, 0).a; 
    out.color = vec4f(lighting, 1.0);
    return out;
}