struct VertexInput {
    @location(0) a_vertices: vec3f,
    @location(1) a_normals: vec3f,
    @location(2) a_uvs: vec2f,
    @location(3) a_tangents: vec3f,
    @location(4) a_bitangents: vec3f
};
struct VertexOutput {
    @builtin(position) v_Position: vec4<f32>,
    @location(0) v_TexCoord : vec2<f32>,
    @location(1) v_TangentViewPos : vec3<f32>,
    @location(2) v_TangentFragPos : vec3<f32>,
    @location(3) v_TangentLightPos0 : vec3<f32>,
};

struct UniformData {
    viewMatrix: mat4x4f,
    projectionMatrix: mat4x4f, 
    modelMatrix: mat4x4f,
    objectColor: vec4f,
    viewPosition: vec4f,
    lightPositions: vec4f,
    lightColors: vec4f
};

@group(0) @binding(0) var<uniform> u_UniformData: UniformData;
@group(1) @binding(0) var u_AlbedoTexture: texture_2d<f32>;
@group(1) @binding(1) var u_AlbedoSampler: sampler;
@group(1) @binding(2) var u_NormalMap: texture_2d<f32>;
@group(1) @binding(3) var u_NormalSampler: sampler;
@group(1) @binding(4) var u_DisplacementMap: texture_2d<f32>;
@group(1) @binding(5) var u_DisplacementSampler: sampler;

@vertex
fn vs_main(
    @builtin(instance_index) ID: u32, 
    in: VertexInput
) -> VertexOutput {
    let modelMat3x3 = mat3x3f(
        u_UniformData.modelMatrix[0].xyz, 
        u_UniformData.modelMatrix[1].xyz, 
        u_UniformData.modelMatrix[2].xyz
    );
    var normalMatrix: mat3x3f = transpose(modelMat3x3);

    var T: vec3f = normalize(normalMatrix * in.a_tangents);
    var B: vec3f = normalize(normalMatrix * in.a_bitangents);
    var N: vec3f = normalize(normalMatrix * in.a_normals);

    // Re-orthogonalize T with respect to N
    T = normalize(T - dot(T, N) * N);

    var TBN: mat3x3f = transpose(mat3x3f(T, B, N));

    var out: VertexOutput;
    var mvp: mat4x4f = u_UniformData.projectionMatrix * u_UniformData.viewMatrix * u_UniformData.modelMatrix;
    out.v_Position = mvp * vec4<f32>(in.a_vertices, 1.0);
    out.v_TexCoord = in.a_uvs;
    out.v_TangentViewPos = TBN * u_UniformData.viewPosition.xyz;
    out.v_TangentFragPos = TBN * (u_UniformData.modelMatrix * vec4f(in.a_vertices, 1.0)).xyz;

    out.v_TangentLightPos0 = TBN * u_UniformData.lightPositions.xyz;

    return out;
}

const heightScale: f32 = 0.1;

fn ParallaxOcclusionMapping(texCoords: vec2f, viewDir: vec3f, fragDepth: ptr<function, f32>) -> vec2f
{
    // number of depth layers
    let minLayers: f32 = 8.0;
    let maxLayers: f32 = 32.0;
    var numLayers: f32 = mix(maxLayers, minLayers, abs(dot(vec3(0.0, 0.0, 1.0), viewDir)));
    // calculate the size of each layer
    var layerDepth: f32 = 1.0 / numLayers;
    // depth of current layer
    var currentLayerDepth: f32 = 0.0;
    // the amount to shift the texture coordinates per layer (from vector P)
    var P: vec2f = viewDir.xy / viewDir.z * heightScale; 
    var deltaTexCoords: vec2f = P / numLayers;
    // get initial values
    var currentTexCoords: vec2f = texCoords;
    var currentDepthMapValue: f32 = textureSample(u_DisplacementMap, u_DisplacementSampler, currentTexCoords).r;

    while (currentLayerDepth < currentDepthMapValue)
    {
        // shift texture coordinates along direction of P
        currentTexCoords -= deltaTexCoords;
        // get depthmap value at current texture coordinates
        currentDepthMapValue = textureSample(u_DisplacementMap, u_DisplacementSampler, currentTexCoords).r;  
        // get depth of next layer
        currentLayerDepth += layerDepth;  
    }
    
    // get texture coordinates before collision (reverse operations)
    var prevTexCoords: vec2f = currentTexCoords + deltaTexCoords;

    // get depth after and before collision for linear interpolation
    var afterDepth: f32 = currentDepthMapValue - currentLayerDepth;
    var beforeDepth: f32 = textureSample(u_DisplacementMap, u_DisplacementSampler, prevTexCoords).r - currentLayerDepth + layerDepth;
 
    // interpolation of texture coordinates
    var weight: f32 = afterDepth / (afterDepth - beforeDepth);
    var finalTexCoords: vec2f = prevTexCoords * weight + currentTexCoords * (1.0 - weight);
	*(fragDepth) = currentLayerDepth + beforeDepth * weight + afterDepth * (1.0 - weight);

    return finalTexCoords;
}

fn SelfOcclusion(lightDir: vec3f, texCoord: vec2f, initialDepth: f32) -> f32
{
	var coefficient: f32 = 0.0;
	var occludedSamples: f32 = 0.0;
	var newCoefficient: f32 = 0.0;
 
	var samples: f32 = 30.0;
	var sampleDist: f32 = initialDepth / samples;
	var offsetTexCoord: vec2f = 0.1 * (lightDir.xy / (lightDir.z * samples));
 
	var currentDepth: f32 = initialDepth - sampleDist;
	var currentTexCoord: vec2f = texCoord + offsetTexCoord;
	var depthFromMesh: f32 = textureSample(u_NormalMap, u_NormalSampler, currentTexCoord).a;
	var steps: f32 = 1.0;
 
	while (currentDepth > 0.0)
	{
		if (depthFromMesh < currentDepth)
		{
			occludedSamples += 1.0;
			newCoefficient = (currentDepth - depthFromMesh) * (1.0 - steps / samples);
			coefficient = max(coefficient, newCoefficient);
		}
		currentDepth -= sampleDist;
		currentTexCoord += offsetTexCoord;
		depthFromMesh = textureSample(u_NormalMap, u_NormalSampler, currentTexCoord).a;
		steps += 1.0;
	}
 
	if (occludedSamples < 1.0) {
		coefficient = 1.0;
	} else {
		coefficient = 1.0 - coefficient;
    }

	return coefficient;
}

@fragment
fn fs_main(
    in: VertexOutput
) -> @location(0) vec4<f32> {
    var fragDepth: f32 = 0.0;
    var camDir: vec3<f32> = normalize(in.v_TangentViewPos - in.v_TangentFragPos);
    var offsetTexCoord: vec2f = ParallaxOcclusionMapping(in.v_TexCoord, camDir, &(fragDepth));

    if (offsetTexCoord.x > 1.0 || offsetTexCoord.y > 1.0 || offsetTexCoord.x < 0.0 || offsetTexCoord.y < 0.0) {
    	discard;
    }

    var textureColor: vec4<f32> = textureSample(u_AlbedoTexture, u_AlbedoSampler, offsetTexCoord);

    var normal: vec3f = textureSample(u_NormalMap, u_NormalSampler, offsetTexCoord).rgb;

    normal = normalize(normal);
    var diffuse: vec3<f32> = vec3<f32>(0.0);
    var specular: vec3<f32> = vec3<f32>(0.0);
    var ambient: vec3<f32> = vec3<f32>(0.0);

    var ambientCoefficient: f32 = 0.1;
    var u_Glossiness: f32 = 3.0;
    var occlusion: f32 = 0.0;

    var tangentLightPos: vec3f = in.v_TangentLightPos0;

    // ambient
    ambient = ambient + u_UniformData.lightColors.rgb * 0.5;

    // diffuse
    var lightDir: vec3<f32> = normalize(tangentLightPos - in.v_TangentFragPos);
    var diff: f32 = max(dot(lightDir, normal), 0.0);
    var D: vec3<f32> = diff * u_UniformData.lightColors.rgb * 0.5;
    diffuse = diffuse + D;

    // specular
    var halfwayDir: vec3<f32> = normalize(lightDir + camDir);
    var spec: f32 = pow(max(dot(normal, halfwayDir), 0.0), 32.0) * u_Glossiness;
    var S: vec3<f32> = u_UniformData.lightColors.rgb * spec * 0.5;
    specular = specular + S;

    occlusion += SelfOcclusion(tangentLightPos, offsetTexCoord, fragDepth);

    ambient = ambientCoefficient * ambient;

    var BlinnPhong: vec3<f32> = occlusion * (ambient + diffuse + specular);
    var finalColor: vec3<f32> = textureColor.rgb * BlinnPhong;
    finalColor = pow(finalColor, vec3<f32>(1.0 / 1.2));

    // gamma correct
    let physicalColor = pow(finalColor * u_UniformData.objectColor.rgb, vec3<f32>(2.2));
    
    return vec4f(physicalColor.r, physicalColor.g, physicalColor.b, textureColor.a);
}