struct uniforms {
    projection: mat4x4f, 
    view: mat4x4f,
    model: mat4x4f,
    view_pos: vec3f,
    light_pos: vec3f,
    light_color: vec3f,
    near_far: vec2f
};

@group(0) @binding(0) var<uniform> ubuffer: uniforms;
@group(1) @binding(0) var diffuse_texture: texture_2d<f32>;
@group(1) @binding(1) var diffuse_sampler: sampler;  
@group(1) @binding(2) var normal_texture: texture_2d<f32>; 
@group(1) @binding(3) var normal_sampler: sampler; 

struct VertexInput {
    @location(0) a_vertices: vec3f, 
    @location(1) a_uvs: vec2f,
    @location(2) a_normals: vec3f,
    @location(3) a_tangents: vec3f,
    @location(4) a_bitangents: vec3f
}
struct VertexOutput {
    @builtin(position) Position: vec4f, 
    @location(0) frag_pos: vec3f,
    @location(1) uv: vec2f, 
    @location(2) T: vec3f,
    @location(3) B: vec3f,
    @location(4) N: vec3f,
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

    let T = normalize((model * vec4f(in.a_tangents, 0.0)).xyz);
    let B = normalize((model * vec4f(in.a_bitangents, 0.0)).xyz);
    let N = normalize((model * vec4f(in.a_normals, 0.0)).xyz);
    // let TBN = transpose(mat3x3f(T, B, N));

    let frag_pos = (model * vec4f(in.a_vertices, 1.0)).xyz;
    let camera_view_proj = projection * view;
    let pos_from_cam = camera_view_proj * vec4f(frag_pos, 1.0); 

    out.Position = pos_from_cam;
    out.frag_pos = frag_pos;
    out.uv = in.a_uvs; 
    out.T = T;
    out.B = B;
    out.N = N;

    return out;
}  

@fragment
fn fs_main(
    in: VertexOutput
) -> FragOutput { 
    var out: FragOutput;  

    let TBN = transpose(mat3x3f(in.T, in.B, in.N));

    let color = textureSample(diffuse_texture, diffuse_sampler, in.uv).rgb; 
    var normal = textureSample(normal_texture, normal_sampler, in.uv).rgb; 
    normal = normalize(normal * 2.0 - 1.0);
    // let normal = normalize(in.frag_norm);
    let light_color = ubuffer.light_color;
    let light_pos = ubuffer.light_pos; 
    let view_pos = ubuffer.view_pos;

    let ambient = 0.2 * light_color;

    let light_dir = TBN * normalize(light_pos - in.frag_pos); 
    let diff = max(dot(light_dir, normal), 0.0); 
    let diffuse = diff * light_color;

    let view_dir = TBN * normalize(view_pos - in.frag_pos);
    let hafway_dir = normalize(light_dir + view_dir);
    let spec = pow(max(dot(normal, hafway_dir), 0.0), 64.0);
    let specular = spec * light_color; 

    let lighting = (ambient + diffuse + specular) * color;  

    out.depth = LinearizeDepth(in.Position.z, ubuffer.near_far.x, ubuffer.near_far.y); 
    out.color = vec4f(lighting, 1.0);
    return out;
}