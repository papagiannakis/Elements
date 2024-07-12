struct uniforms {
    projection: mat4x4f, 
    view: mat4x4f,
    model: mat4x4f,
    view_pos: vec3f,
    light_view: mat4x4f, 
    light_proj: mat4x4f,
    light_pos: vec3f,
    near_far: vec2f
};

@group(0) @binding(0) var<uniform> ubuffer:     uniforms;
@group(1) @binding(0) var g_position_texture:   texture_2d<f32>;
@group(1) @binding(1) var g_position_sampler:   sampler;
@group(1) @binding(2) var g_normal_texture:     texture_2d<f32>;
@group(1) @binding(3) var g_normal_sampler:     sampler;
@group(1) @binding(4) var g_color_texture:      texture_2d<f32>;
@group(1) @binding(5) var g_color_sampler:      sampler;
@group(1) @binding(6) var shadow_texture:       texture_depth_2d;
@group(1) @binding(7) var shadow_sampler:       sampler;

struct VertexOutput { 
    @builtin(position) Position: vec4<f32>,
    @location(0) uv: vec2<f32>
}
struct FragOutput { 
    @builtin(frag_depth) depth: f32,
    @location(0) color: vec4f
};

fn mat4to3(m: mat4x4f) -> mat3x3f {
    var newMat: mat3x3f;

    newMat[0][0] = m[0][0];
    newMat[0][1] = m[0][1];
    newMat[0][2] = m[0][2];
    newMat[1][0] = m[1][0];
    newMat[1][1] = m[1][1];
    newMat[1][2] = m[1][2];
    newMat[2][0] = m[2][0];
    newMat[2][1] = m[2][1];
    newMat[2][2] = m[2][2];

    return newMat;
}

fn inverse_mat3(m: mat3x3f) -> mat3x3f {
    let m00 = m[0][0];
    let m01 = m[0][1];
    let m02 = m[0][2];
    let m10 = m[1][0];
    let m11 = m[1][1];
    let m12 = m[1][2];
    let m20 = m[2][0];
    let m21 = m[2][1];
    let m22 = m[2][2];

    let b01 =  m22 * m11 - m12 * m21;
    let b11 = -m22 * m10 + m12 * m20;
    let b21 =  m21 * m10 - m11 * m20;

    let invDet = 1.0 / (m00 * b01 + m01 * b11 + m02 * b21);

    var newDst: mat3x3f;
    newDst[0][0] = b01 * invDet;
    newDst[0][1] = (-m22 * m01 + m02 * m21) * invDet;
    newDst[0][2] = ( m12 * m01 - m02 * m11) * invDet;
    newDst[1][0] = b11 * invDet;
    newDst[1][1] = ( m22 * m00 - m02 * m20) * invDet;
    newDst[1][2] = (-m12 * m00 + m02 * m10) * invDet;
    newDst[2][0] = b21 * invDet;
    newDst[2][1] = (-m21 * m00 + m01 * m20) * invDet;
    newDst[2][2] = ( m11 * m00 - m01 * m10) * invDet;

    return newDst;
}

fn LinearizeDepth( 
    depth: f32,
    near: f32,
    far: f32,
) -> f32 {   

    let zNdc = 2 * depth - 1; 
    let zEye = (2 * far * near) / ((far + near) - zNdc * (far - near)); 
    let linearDepth = (zEye - near) / (far - near);
    return linearDepth;
}

fn ShadowCalculation(
    fragPosLightSpace: vec4f,
    bias: f32
) -> f32 { 
    // Perform perspective divide 
    // Transform to [0,1] range
    var projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;  
    var UVCoords = projCoords.xy * vec2f(0.5, -0.5) + vec2f(0.5, 0.5);
    // Get closest depth value from light's perspective (using [0,1] range fragPosLight as coords)
    var closestDepth: f32 = textureSample(shadow_texture, shadow_sampler, UVCoords);
    // Get depth of current fragment from light's perspective
    let currentDepth: f32 = LinearizeDepth(projCoords.z, 0.01, 500.0);
    // Check whether current frag pos is in shadow
    let near_far = ubuffer.near_far;

    var visibility = 0.0;
    let oneOverShadowDepthTextureSize = 1.0 / 2048.0;
    for (var y = -1; y <= 1; y++) {
        for (var x = -1; x <= 1; x++) {
        let offset = vec2f(vec2(x, y)) * oneOverShadowDepthTextureSize;
            // Get closest depth value from light's perspective (using [0,1] range fragPosLight as coords)
            var closestDepth: f32 = textureSample(shadow_texture, shadow_sampler, UVCoords + offset);
            // Get depth of current fragment from light's perspective
            let currentDepth: f32 = LinearizeDepth(projCoords.z, near_far.x, near_far.y);
            // Check whether current frag pos is in shadow 
            if (currentDepth - bias > closestDepth) { 
                visibility += 1.0; 
            }
        }
    }
    visibility /= 9.0; 
    
    return visibility;
}

@fragment
fn fs_main(
    in: VertexOutput
) -> FragOutput {
    var uv = in.uv;

    var model = transpose(ubuffer.model);
    var view = transpose(ubuffer.view); 
    var projection = transpose(ubuffer.projection); 
    var light_view = transpose(ubuffer.light_view);
    var light_proj = transpose(ubuffer.light_proj); 
    var near = ubuffer.near_far.x;
    var far = ubuffer.near_far.y;

    var frag_pos = textureSample(g_position_texture, g_position_sampler, uv).xyz;
    var frag_norm = textureSample(g_normal_texture, g_normal_sampler, uv).xyz;
    var frag_color = textureSample(g_color_texture, g_color_sampler, uv).xyz;
    var frag_pos_from_light = light_proj * light_view * vec4f(frag_pos, 1.0);

    var out: FragOutput;

    let normal = normalize(transpose(inverse_mat3(mat4to3(ubuffer.model))) * frag_norm);
    let light_color = vec3f(1.0);
    let light_pos = ubuffer.light_pos; 
    let view_pos = ubuffer.view_pos;

    let ambient = 0.2 * light_color;

    let light_dir = normalize(light_pos - frag_pos); 
    let diff = max(dot(light_dir, normal), 0.0); 
    let diffuse = diff * light_color;

    let view_dir = normalize(view_pos - frag_pos);
    let hafway_dir = normalize(light_dir + view_dir);
    let spec = pow(max(dot(normal, hafway_dir), 0.0), 64.0);
    let specular = spec * light_color; 

    let bias = max(0.0005 * (1.0 - dot(normal, light_dir)), 0.00001);
    let shadow = ShadowCalculation(frag_pos_from_light, bias);
    let lighting = (ambient + (1.0 - shadow) * (diffuse + specular)) * frag_color;  

    out.depth = textureSample(g_normal_texture, g_normal_sampler, uv).a; 
    out.color = vec4f(lighting, 1.0);
    return out;
}