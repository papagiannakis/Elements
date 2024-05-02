struct Unirform { 
    proj: mat4x4f,
    view: mat4x4f, 
    lightColor: vec4f, 
    lightPos: vec4f, 
    camPos: vec4f
};

struct ObjectData { 
    model: array<mat4x4f>
}; 

struct Fragment { 
    @builtin(position) Position: vec4f,
    @location(0) tex: vec2f, 
    @location(1) normal: vec3f, 
    @location(2) currentPos: vec3f
};

@binding(0) @group(0) var<uniform> ubuffer: Unirform;
@binding(1) @group(0) var<storage, read> objects: ObjectData;
@binding(0) @group(1) var myTexture: texture_2d<f32>;
@binding(1) @group(1) var mySampler: sampler; 

@vertex
fn vs_main(
    @builtin(instance_index) ID: u32,
    @location(0) aVertex: vec3f, 
    @location(1) aTex: vec2f,
    @location(2) aNormal: vec3f
) -> Fragment {  

    var model = objects.model[ID]; 
    var ctrn = (model * vec4f(aVertex, 1.0)).xyz; 

    var out: Fragment;
    out.Position = ubuffer.proj * ubuffer.view * model * vec4f(aVertex, 1.0); 
    out.tex = aTex;
    out.normal = aNormal;
    out.currentPos = ctrn;
    return out;
}

@fragment
fn fs_main(
    @location(0) tex: vec2f, 
    @location(1) normal: vec3f, 
    @location(2) currentPos: vec3f
) -> @location(0) vec4f { 

    var color = vec4f(1.0, 1.0, 1.0, 1.0);
    var lightVec = ubuffer.lightPos.xyz - currentPos;

    var dist = length(lightVec);
    var a = 0.005;
    var b = 0.0005;
    var inten = 1.0 / (a * dist * dist + b * dist + 1.0); 

    var ambient = 0.2; 

    var norm = normalize(normal);
    var lightDir = normalize(lightVec);
    var diffuse = max(dot(norm, lightDir), 0.0); 

    var specular = 0.0; 
    if (diffuse != 0.0) { 
        var specularLight = 0.05;
        var viewDirection  = normalize(ubuffer.camPos.xyz - currentPos); 
        var halfWay = normalize(viewDirection + lightDir); 
        var specAmount = pow(max(dot(norm, halfWay), 1.0), 16.0); 
        specular = specAmount * specularLight;
    } 

    // return (textureSample(myTexture, mySampler, tex) * (diffuse * inten + ambient) + textureSample(myTexture, mySampler, tex).r * specular * inten) * ubuffer.lightColor; 
    return (color * (diffuse * inten + ambient) + color.r * specular * inten) * ubuffer.lightColor; 
}