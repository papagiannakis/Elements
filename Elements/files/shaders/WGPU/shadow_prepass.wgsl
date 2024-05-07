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

@vertex
fn vs_main( 
    @builtin(instance_index) ID: u32,
    @location(0) aPos: vec3f,
    @location(1) aNormal: vec3f
) -> Fragment { 

    var out: Fragment;
    
    var model = objects.model[ID]; 

    var lmvp = ubuffer.light_proj * ubuffer.light_view * model; 
    out.Position = lmvp * vec4f(aPos, 1.0); 
    out.pos = lmvp * vec4f(aPos, 1.0); 

    let n = normalize(aNormal); 
    out.normal = (model * vec4f(n, 0.0)).xyz; 

    return out;
} 

@fragment
fn fs_main(
    @location(0) normal: vec3f, 
    @location(1) pos: vec4f
) -> @location(0) vec4f {  

    var depth = pos.z/pos.w; 

    return vec4f(depth, depth, depth, 1.0);
}