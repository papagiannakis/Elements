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

@group(0) @binding(0) var<uniform> ubuffer: uniforms;
@group(1) @binding(0) var albedo_texture: texture_2d<f32>;
@group(1) @binding(1) var albedo_sampler: sampler; 

struct VertexInput {
    @location(0) a_vertices: vec3f, 
    @location(1) a_uvs: vec2f,
    @location(2) a_normals: vec3f
}
struct VertexOutput {
    @builtin(position) Position: vec4f, 
    @location(0) frag_pos_light_space: vec4f,
    @location(1) frag_pos: vec3f, 
    @location(2) frag_norm: vec3f,
    @location(3) uv: vec2f
};
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

@vertex
fn vs_main( 
    in: VertexInput
) -> VertexOutput {

    var out: VertexOutput;   

    var model = transpose(ubuffer.model);
    var view = transpose(ubuffer.view); 
    var projection = transpose(ubuffer.projection); 
    var light_view = transpose(ubuffer.light_view);
    var light_proj = transpose(ubuffer.light_proj);

    let frag_pos = (model * vec4f(in.a_vertices, 1.0)).xyz;
    let normal = transpose(inverse_mat3(mat4to3(model))) * in.a_normals;
    let light_view_proj = light_proj * light_view;
    let camera_view_proj = projection * view;
    let pos_from_light = light_view_proj * vec4f(frag_pos, 1.0); 
    let pos_from_cam = camera_view_proj * vec4f(frag_pos, 1.0);

    out.Position = pos_from_cam;
    out.frag_pos = frag_pos;
    out.frag_norm = normal;  
    out.uv = in.a_uvs;
    out.frag_pos_light_space = pos_from_light;

    return out;
}  

@fragment
fn fs_main(
    in: VertexOutput
) -> FragOutput { 
    var out: FragOutput;

    let color = textureSample(albedo_texture, albedo_sampler, in.uv).rgb;
    let normal = normalize(in.frag_norm);
    let light_color = vec3f(1.0);
    let light_pos = ubuffer.light_pos; 
    let view_pos = ubuffer.view_pos;

    let ambient = 0.2 * light_color;

    let light_dir = normalize(light_pos - in.frag_pos); 
    let diff = max(dot(light_dir, normal), 0.0); 
    let diffuse = diff * light_color;

    let view_dir = normalize(view_pos - in.frag_pos);
    let hafway_dir = normalize(light_dir + view_dir);
    let spec = pow(max(dot(normal, hafway_dir), 0.0), 64.0);
    let specular = spec * light_color; 

    let lighting = (ambient + diffuse + specular) * color;  

    out.depth = LinearizeDepth(in.Position.z, ubuffer.near_far.x, ubuffer.near_far.y); 
    out.color = vec4f(lighting, 1.0);
    return out;
}