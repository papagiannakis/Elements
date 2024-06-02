struct Uniforms { 
    proj: mat4x4f, 
    view: mat4x4f,
    light_proj: mat4x4f, 
    light_view: mat4x4f, 
    light_pos: vec4f,
    cam_pos: vec4f
};

struct ModelData { 
    model: array<mat4x4f>
};   

struct ModelTIData { 
    model_ti: array<mat4x4f>
};

struct Fragment { 
    @builtin(position) Position: vec4f,
    @location(0) fragPos: vec3f,  
    @location(1) normal: vec3f,
    @location(2) fragPosLight: vec4f, 
    @location(3) deffuseUV: vec2f
}

@binding(0) @group(0) var<uniform> ubuffer: Uniforms;
@binding(1) @group(0) var<storage, read> models: array<mat4x4f>;
@binding(2) @group(0) var<storage, read> models_ti: array<mat4x4f>;
@binding(0) @group(1) var myTexture: texture_2d<f32>;
@binding(1) @group(1) var shadowMap: texture_depth_2d; 
@binding(2) @group(1) var shadowSampler: sampler_comparison; 
@binding(3) @group(1) var mySampler: sampler; 

const ShadowDepthTextureSize = 2048;
const near_plane = 0.1;
const far_plane = 500.0;

@vertex
fn vs_main(
    @builtin(instance_index) ID: u32,
    @location(0) a_pos: vec3f,
    @location(1) a_normal: vec3f,
    @location(2) a_uv: vec2f
) -> Fragment { 

    var model = models[ID]; 
    var model_ti = models_ti[ID];
    var lmvp = ubuffer.light_proj * ubuffer.light_view * model;
    var mvp = ubuffer.proj * ubuffer.view * model;  

    var out: Fragment;
    out.fragPos = (model * vec4(a_pos, 1.0)).xyz; 
    out.normal = (model_ti * vec4f(a_normal, 1.0)).xyz; 
    out.fragPosLight = lmvp * vec4f(a_pos, 1.0);
    out.deffuseUV = a_uv;
    out.Position = mvp * vec4(a_pos, 1.0);
    return out;
}  

fn linearizeDepth(depth: f32) -> f32 {
    let z: f32 = depth * 2.0 - 1.0; // Back to NDC
    return (2.0 * near_plane * far_plane) / (far_plane + near_plane - z * (far_plane - near_plane));
}

fn ShadowCalculation(
    fragPosLight: vec4f,
) -> f32 { 
    var projCoord = fragPosLight.xyz / fragPosLight.w; 
    var uv = vec2f(0.0, 0.0); 

    uv = projCoord.xy * vec2f(0.5, -0.5) + vec2f(0.5, 0.5); 

    var visibility = 0.0;
    let oneOverShadowDepthTextureSize = 1 / f32(ShadowDepthTextureSize);
    for (var y = -1; y <= 1; y++) {
        for (var x = -1; x <= 1; x++) {
            let offset = vec2f(vec2(x, y)) * oneOverShadowDepthTextureSize;
            visibility += textureSampleCompare(
                shadowMap, shadowSampler,
                uv.xy + offset, projCoord.z - 0.0001
            );
        }
    }
    visibility /= 9.0;  

    return visibility; 
}

@fragment
fn fs_main(
    @location(0) fragPos: vec3f,
    @location(1) normal: vec3f, 
    @location(2) fragPosLight: vec4f,
    @location(3) deffuseUV: vec2f
) -> @location(0) vec4f { 

    var color = textureSample(myTexture, mySampler, deffuseUV); 
    var norm = normalize(normal); 
    var lightColor = vec3f(1.0, 1.0, 1.0);

    var ambient = 0.05 * lightColor;

    var lightDir = normalize((ubuffer.light_pos).xyz - fragPos); 
    var diff = max(dot(lightDir, norm), 0.0);
    var diffuse = diff * lightColor; 

    var viewDir = normalize((ubuffer.cam_pos).xyz - fragPos);
    var spec = 0.0;
    var halfwaydir = normalize(lightDir + viewDir);
    spec = pow(max(dot(norm, halfwaydir), 0.0), 64.0); 
    var specular = spec * lightColor; 

    var shadow = ShadowCalculation(fragPosLight); 
    var lighting = (ambient + shadow * (diffuse + specular)) * color.xyz;  
    return vec4f(lighting, 1.0); 
}