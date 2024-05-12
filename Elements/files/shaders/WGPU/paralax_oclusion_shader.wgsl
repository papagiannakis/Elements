struct Uniforms {
    proj: mat4x4f,
    view: mat4x4f,
    view_pos: vec4f,
    light_pos: vec4f
};

struct ModelData {
    model: array<mat4x4f>
}

struct Fragment {
    @builtin(position) Position: vec4f,
    @location(0) frag_pos: vec3f,
    @location(1) tex_coords: vec2f,
    @location(2) tangent_light_pos: vec3f,
    @location(3) tangent_view_pos: vec3f,
    @location(4) tangent_frag_pos: vec3f
}

@binding(0) @group(0) var<uniform> ubuffer: Uniforms;
@binding(1) @group(0) var<storage, read> models: ModelData;

@binding(0) @group(1) var diffuse_texture: texture_2d<f32>;
@binding(1) @group(1) var bump_texture: texture_2d<f32>;
@binding(2) @group(1) var normal_texture: texture_2d<f32>;
@binding(3) @group(1) var filter_sampler: sampler;

const height_scale = 0.5;

fn Mat3x3(
    in: mat4x4f
) -> mat3x3f {

    return mat3x3f(
        in[0].xyz,
        in[1].xyz,
        in[2].xyz
    );
}

fn simpleParallaxMapping(
    tex_coords: vec2f,
    view_dir: vec3f
) -> vec2f {

    var height = textureSample(bump_texture, filter_sampler, tex_coords).r;
    var p = view_dir.xy / view_dir.z * (height * height_scale);

    return vec2f(tex_coords - p);
}

fn ParallaxMapping(
    tex_coords: vec2f,
    view_dir: vec3f
) -> vec2f {

    var min_layers = 8.0;
    var max_layers = 32.0;

    var num_layers = mix(max_layers, min_layers, abs(dot(vec3f(0.0, 0.0, 1.0), view_dir)));
    var layer_depth = 1.0 / num_layers;

    var curr_layer_depth = 0.0;

    var p = view_dir.xy / view_dir.z * height_scale;
    var delta_tex_coords = p / num_layers;

    var curr_tex = tex_coords;
    var curr_depth_map_value = textureSample(bump_texture, filter_sampler, curr_tex).r;

    while(curr_layer_depth < curr_depth_map_value) {
        curr_tex = curr_tex - delta_tex_coords;
        curr_depth_map_value = textureSample(bump_texture, filter_sampler, curr_tex).r;
        curr_layer_depth = curr_layer_depth + layer_depth;
    }

    var prev_tex_coords = curr_tex + delta_tex_coords;

    var after_depth = curr_depth_map_value - curr_layer_depth;
    var before_depth = textureSample(bump_texture, filter_sampler, prev_tex_coords).r - curr_layer_depth + layer_depth;

    var weight = after_depth / (after_depth - before_depth);
    var final_tex = prev_tex_coords * weight + curr_tex * (1.0 - weight);

    return final_tex;
}

@vertex
fn vs_main(
    @builtin(instance_index) ID: u32,
    @location(0) a_pos: vec3f,
    @location(1) a_normal: vec3f,
    @location(2) a_tex: vec2f,
    @location(3) a_tangent: vec3f,
    @location(4) a_bitangent: vec3f
) -> Fragment {

    var model = models.model[ID];
    var T = normalize(Mat3x3(model) * a_tangent);
    var B = normalize(Mat3x3(model) * a_bitangent);
    var N = normalize(Mat3x3(model) * a_normal);
    var TBN = transpose(mat3x3f(T, B, N));
    // var TBN = mat3x3f(T, B, N);

    var out: Fragment;
    out.frag_pos = (model * vec4f(a_pos, 1.0)).xyz;
    out.tex_coords = a_tex;
    out.tangent_light_pos = TBN * ubuffer.light_pos.xyz;
    out.tangent_view_pos = TBN * ubuffer.view_pos.xyz;
    out.tangent_frag_pos = TBN * out.frag_pos;

    out.Position = ubuffer.proj * ubuffer.view * model * vec4f(a_pos, 1.0);
    return out;
}

@fragment
fn fs_main(
    @location(0) frag_pos: vec3f,
    @location(1) tex_coords: vec2f,
    @location(2) tangent_light_pos: vec3f,
    @location(3) tangent_view_pos: vec3f,
    @location(4) tangent_frag_pos: vec3f
) -> @location(0) vec4f {

    var view_dir = normalize(tangent_view_pos - tangent_frag_pos);

    var tex = simpleParallaxMapping(tex_coords, view_dir);
    // if (tex.x > 1.0 || tex.y > 1.0 || tex.x < 0.0 || tex.y < 0.0) {
    //     tex = tex_coords;
    // }

    var normal = textureSample(normal_texture, filter_sampler, tex).rgb;
    normal = normalize(normal * 2.0 - 1.0);

    var color = textureSample(diffuse_texture, filter_sampler, tex).rgb;

    var ambient = 0.1 * color;

    var ligh_dir = normalize(tangent_light_pos - tangent_frag_pos);
    var diff = max(dot(ligh_dir, normal), 0.0);
    var diffuse = diff * color;

    var reflec_dir = normalize(tangent_light_pos - tangent_frag_pos);
    var half_way_dir = normalize(ligh_dir + view_dir);
    var spec = pow(max(dot(normal, half_way_dir), 0.0), 32.0);

    var specular = vec3f(0.2) * spec;

    return vec4f((ambient + diffuse + specular), 1.0);
}