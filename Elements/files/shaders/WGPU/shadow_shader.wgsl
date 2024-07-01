struct uniforms {
    projection: mat4x4f, 
    view: mat4x4f,
    model: mat4x4f,
    light_view: mat4x4f, 
    light_proj: mat4x4f,
    light_pos: vec3f,
};

@group(0) @binding(0) var<uniform> ubuffer: uniforms;
@group(1) @binding(0) var albedo_texture: texture_2d<f32>;
@group(1) @binding(1) var albedo_sampler: sampler;
@group(1) @binding(2) var shadow_texture: texture_depth_2d;
@group(1) @binding(3) var shadow_sampler: sampler_comparison;

struct VertexInput {
    @location(0) a_vertices: vec3f, 
    @location(1) a_uvs: vec2f,
    @location(2) a_normals: vec3f
}
struct VertexOutput {
    @builtin(position) Position: vec4f, 
    @location(0) shadow_pos: vec3f,
    @location(1) frag_pos: vec3f, 
    @location(2) frag_norm: vec3f,
    @location(3) uv: vec2f
}; 

@vertex
fn vs_main( 
    in: VertexInput
) -> VertexOutput {

    var model = transpose(ubuffer.model);
    var view = transpose(ubuffer.view); 
    var projection = transpose(ubuffer.projection); 
    var light_view = transpose(ubuffer.light_view);
    var light_proj = transpose(ubuffer.light_proj);

    var light_view_proj = light_proj * light_view;
    var camera_view_proj = projection * view;

    var out: VertexOutput;  

    let pos_from_light = light_view_proj * model * vec4f(in.a_vertices, 1.0);
    out.shadow_pos = vec3f(
        pos_from_light.xy * vec2f(0.5, -0.5) + vec2f(0.5),
        pos_from_light.z
    );

    out.Position = camera_view_proj * model * vec4f(in.a_vertices, 1.0);
    out.frag_pos = out.Position.xyz;
    out.frag_norm = in.a_normals; 
    out.uv = in.a_uvs;

    return out;
} 

fn shadow_visibility(
    shadow_pos: vec3f
) -> f32 { 
    var visibility = 0.0; 
    let shadowDepthTextureSize = 1024.0;
    let oneOverShadowDepthTextureSize = 1.0 / shadowDepthTextureSize;
    for (var y = -1; y <= 1; y++) {
        for (var x = -1; x <= 1; x++) {
            let offset = vec2f(vec2(x, y)) * oneOverShadowDepthTextureSize;

            visibility += textureSampleCompare(
                shadow_texture, shadow_sampler,
                shadow_pos.xy + offset, shadow_pos.z - 0.007
            );
        }
    }
    visibility /= 9.0; 
    return visibility;
}

@fragment
fn fs_main(
    in: VertexOutput
) -> @location(0) vec4<f32> { 

    var light_pos = ubuffer.light_pos; 
    var albedo = textureSample(albedo_texture, albedo_sampler, in.uv).xyz;
    var ambientFactor = 0.2;

    var visibility = shadow_visibility(in.shadow_pos);

    let lambertFactor = max(dot(normalize(light_pos - in.frag_pos), normalize(in.frag_norm)), 0.0);
    let lightingFactor = min(ambientFactor + visibility * lambertFactor, 1.0); 


    return vec4(lightingFactor * albedo, 1.0);
}