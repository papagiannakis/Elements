struct Uniforms { 
    proj: mat4x4f, 
    view: mat4x4f, 
    light_view: mat4x4f,
    light_proj: mat4x4f
};

struct ObjectData { 
    model: array<mat4x4f>
}; 

struct Fragment { 
    @builtin(position) Position: vec4f, 
    @location(0) normal: vec3f,
    @location(1) pos: vec4f
};

@binding(0) @group(0) var<uniform> ubuffer: Uniforms; 
@binding(1) @group(0) var<storage, read> objects: ObjectData;  

const near_plane = 0.1;
const far_plane = 500.0;

fn linearizeDepth(depth: f32) -> f32 {
    let z: f32 = depth * 2.0 - 1.0; // Back to NDC
    return (2.0 * near_plane * far_plane) / (far_plane + near_plane - z * (far_plane - near_plane));
} 

@vertex
fn vs_main( 
    @builtin(instance_index) ID: u32,
    @location(0) aPos: vec3f,
    @location(1) aNormal: vec3f
) -> Fragment { 

    var out: Fragment;
    
    var model = objects.model[ID]; 

    var lmvp = ubuffer.light_proj * ubuffer.light_view * model; 
    let n = normalize(aNormal); 
    // out.Position = lmvp * vec4f(aPos, 1.0); 
    out.pos = lmvp * vec4f(aPos, 1.0); 
    out.normal = (model * vec4f(n, 0.0)).xyz; 

    out.Position = out.pos; 
    return out;
} 

@fragment
fn fs_main(
    @location(0) normal: vec3f, 
    @location(1) pos: vec4f
) -> @location(0) vec4f {  

    var depth = pos.z/pos.w; 

    return vec4f(depth, depth, depth, depth);
}