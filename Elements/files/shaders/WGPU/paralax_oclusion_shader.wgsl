struct Uniforms {
    proj: mat4x4f,
    view: mat4x4f,
    view_pos: vec4f,
    light_pos: vec4f
};

struct ModelData {
    model: array<mat4x4f>
} 

struct NormalData { 
    normal: array<mat4x4f>
}

// struct Fragment {
//     @builtin(position) Position: vec4f,
//     @location(0) frag_pos: vec3f,
//     @location(1) tex_coords: vec2f,
//     @location(2) tangent_light_pos: vec3f,
//     @location(3) tangent_view_pos: vec3f,
//     @location(4) tangent_frag_pos: vec3f
// } 

struct Fragment { 
    @builtin(position) Position: vec4f, 
    @location(0) tex_coords: vec2f,
    @location(1) cam_dir: vec3f, 
    @location(2) light_dir: vec3f,
    @location(3) attenuation: f32
} 

struct POM_out { 
    tex: vec2f,
    depth: f32
}

@binding(0) @group(0) var<uniform> ubuffer: Uniforms;
@binding(1) @group(0) var<storage, read> models: ModelData; 
@binding(2) @group(0) var<storage, read> normals: NormalData;

@binding(0) @group(1) var diffuse_texture: texture_2d<f32>;
@binding(1) @group(1) var normal_texture: texture_2d<f32>;
@binding(2) @group(1) var spec_texture: texture_2d<f32>;
@binding(3) @group(1) var filter_sampler: sampler;

fn Mat3x3(
    in: mat4x4f
) -> mat3x3f {

    return mat3x3f(
        in[0].xyz,
        in[1].xyz,
        in[2].xyz
    );
}

// fn simpleParallaxMapping(
//     tex_coords: vec2f,
//     view_dir: vec3f
// ) -> vec2f {

//     var height = textureSample(bump_texture, filter_sampler, tex_coords).r;
//     var p = view_dir.xy / view_dir.z * (height * height_scale);

//     return vec2f(tex_coords - p);
// }

fn POM( 
    cam_dir: vec3f, 
    tex_coords: vec2f, 
) -> POM_out { 

    var out: POM_out;
    out.depth = 0.0; 

    var samples = mix(30.0, 5.0, abs(dot(vec3f(0.0, 0.0, 1.0), cam_dir))); 
    // var samples = 30.0;
    var sample_dist = 1.0 / samples;
    var curr_depth = 0.0; 

    var offset_tex_coord = 0.1 * (cam_dir.xy / (cam_dir.z * samples)); 

    var current_tex_coords = tex_coords;
    var depth_from_mesh = textureSample(normal_texture, filter_sampler, current_tex_coords.xy).a; 

    while(depth_from_mesh > curr_depth) 
    { 
        curr_depth = curr_depth + 1.0;
        current_tex_coords = current_tex_coords - offset_tex_coord;
        depth_from_mesh = textureSample(normal_texture, filter_sampler, current_tex_coords.xy).a;
    } 

    var prev_tex_coords = current_tex_coords + offset_tex_coord; 

    var after_intersection = depth_from_mesh - curr_depth;
    var before_intersection = textureSample(normal_texture, filter_sampler, prev_tex_coords.xy).a - curr_depth + sample_dist; 

    var ratio = after_intersection / (after_intersection - before_intersection); 

    var final_tex = prev_tex_coords * ratio + current_tex_coords * (1.0 - ratio);
    var frag_depth = curr_depth + before_intersection * ratio + after_intersection * (1.0 - ratio); 

    out.depth = frag_depth;
    out.tex = final_tex; 

    return out;
} 

fn self_occlusion(
    ligh_dir: vec3f,
    tex_coords: vec2f, 
    initial_depth: f32
) -> f32 { 

    var coefficient = 0.0; 
    var occlusion_samples = 0.0;
    var new_coefficient = 0.0;

    var samples = 30.0;
    var sample_dist = initial_depth / samples;
    var offset_tex_coord = 0.1 * (ligh_dir.xy / (ligh_dir.z * samples)); 

    var curr_depth = initial_depth - sample_dist;
    var current_tex_coords = tex_coords + offset_tex_coord;
    var depth_from_mesh = textureSample(normal_texture, filter_sampler, current_tex_coords.xy).a; 
    var steps = 1.0; 

    while (curr_depth > 0.0) 
    { 
        if (depth_from_mesh < curr_depth) 
        { 
            occlusion_samples = occlusion_samples + 1.0;
            new_coefficient = (curr_depth - depth_from_mesh) * (1.0 - steps / samples); 
            coefficient = max(coefficient, new_coefficient);
        } 

        curr_depth = curr_depth - sample_dist;
        current_tex_coords = current_tex_coords + offset_tex_coord; 
        depth_from_mesh = textureSample(normal_texture, filter_sampler, current_tex_coords.xy).a; 
        steps = steps + 1.0;
    } 

    if (occlusion_samples < 1.0) 
    { 
        coefficient = 1.0;
    } 
    else  
    { 
        coefficient = 1.0 - coefficient;
    } 

    return coefficient;
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
    var norm_mat = Mat3x3(normals.normal[ID]);

    // var T = normalize(Mat3x3(model) * a_tangent);
    // var B = normalize(Mat3x3(model) * a_bitangent);
    // var N = normalize(Mat3x3(model) * a_normal);
    // var TBN = transpose(mat3x3f(T, B, N));
    // // var TBN = mat3x3f(T, B, N); 

    var N = normalize(norm_mat * a_normal); 
    var T = normalize(norm_mat * a_tangent);
    T = normalize(T - (dot(N, T) * N));
    var B = normalize(norm_mat * a_bitangent);

    if (dot(cross(N, T), B) < 0.0) 
    { 
        T = T * (-1.0);
    } 

    var TBN = transpose(mat3x3f(T, B, N)); 

    var position = ((ubuffer.view * model) * vec4f(a_pos, 1.0)).xyz; 
    var radius = 50.0; 
    var dist = length(((ubuffer.view * model) * ubuffer.light_pos).xyz - position);

    var out: Fragment; 
    out.cam_dir = TBN * (normalize(ubuffer.view_pos.xyz - position)); 
    out.light_dir = TBN * (normalize(ubuffer.light_pos.xyz - position)); 
    out.tex_coords = a_tex;
    out.attenuation = 1.0 / (1.0 + ((2.0 / radius) * dist) + ((1.0 / (radius * radius)) * (dist * dist))); 

    out.Position = (ubuffer.proj * (ubuffer.view * model)) * vec4f(a_pos, 1.0);
    return out;
}

@fragment
fn fs_main(
    @location(0) tex_coords: vec2f,
    @location(1) cam_dir: vec3f, 
    @location(2) light_dir: vec3f,
    @location(3) attenuation: f32
) -> @location(0) vec4f {
 
    // var offset_tex_coord = POM(cam_dir, tex_coords, frag_depth);   
    var parallax = POM(cam_dir, tex_coords); 
    var frag_depth = parallax.depth;
    var offset_tex_coord = parallax.tex;
    var light_color = vec3f(1.0, 1.0, 1.0);

    if (offset_tex_coord.x > 1.0 || offset_tex_coord.y > 1.0 || offset_tex_coord.x < 0.0 || offset_tex_coord.y < 0.0) 
    { 
        discard;
    } 

    var albedo = textureSample(diffuse_texture, filter_sampler, offset_tex_coord.xy).rgb;
    var normals = normalize(textureSample(normal_texture, filter_sampler, offset_tex_coord.xy).rgb * 2.0 - 1.0); 
    var spec = textureSample(spec_texture, filter_sampler, offset_tex_coord.xy).r; 

    var AO = 0.9; 
    var roughness = 0.7;  

    var diffuse = vec3f(0.0);
    var specular = vec3f(0.0); 
    var ambient = vec3f(0.0);
    var occlusion = 0.0; 

    for (var i = 0; i < 1; i = i + 1) 
    { 
        var half_angle = normalize(cam_dir + light_dir); 
        var n_dot_l = clamp(dot(normals, light_dir), 0.0, 1.0);
        var n_dot_h = clamp(dot(normals, half_angle), 0.0, 1.0); 

        var specular_highlight = pow(n_dot_h, 1.0 - roughness); 
        var S = spec * (light_color * specular_highlight); 
        var D = (1.0 - roughness) * (light_color * n_dot_l); 

        occlusion = occlusion + self_occlusion(light_dir, offset_tex_coord, frag_depth);
        diffuse = diffuse + (D * attenuation); 
        specular = specular + (S * attenuation); 
        ambient = ambient + (light_color * attenuation);
    } 

    var ambience = (0.01 * ambient) * AO; 

    var Blinn_Phong = occlusion * (ambience + diffuse + specular); 
    var final_color = albedo * Blinn_Phong; 
    //final_color = pow(final_color, vec3f(1.0 / 2.2)); 
    return vec4f(final_color, 1.0);
}