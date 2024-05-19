/////////////////////////////////////////////////////
////////////////////VERTEX SHADER////////////////////
/////////////////////////////////////////////////////
#version 330

layout(location = 0) in vec3 inPosition;
layout(location = 1) in vec3 inNormal;
layout(location = 2) in vec2 inTexCoord;
layout(location = 3) in vec3 inTangent;
layout(location = 4) in vec3 inBitangent;

out vec2 texCoord;
out vec3 camDir;
out vec3 lightDir;
out float attenuation;

uniform mat4 viewMatrix;
uniform mat4 modelMatrix;
uniform mat4 projectionMatrix;
uniform mat3 normalMatrix;
uniform vec3 camPosIn;
uniform vec3 lightPosIn;

void main()
{
	vec3 N = normalize(normalMatrix * inNormal);
	vec3 T = normalize(normalMatrix * inTangent);
		 T = normalize(T - (dot(N, T) * N));
	vec3 B = normalize(normalMatrix * inBitangent);

	if (dot(cross(N, T), B) < 0.0)
		T = T * -1.0;

	mat3 TBNMatrix = transpose(mat3(T, B, N));

	vec3 position = vec3((viewMatrix * modelMatrix) * vec4(inPosition, 1.0)); //Vector is a position so W = 1.0. If it were a direction w = 0.0.
	camDir = TBNMatrix * (normalize(camPosIn - position));
	lightDir = TBNMatrix * (normalize(lightPosIn - position));
	texCoord = inTexCoord;

	float radius = 50.0;
	float dist = length(vec3((viewMatrix * modelMatrix) * vec4(lightPosIn, 1.0)) - position);
	attenuation = 1.0 / (1.0 + ((2.0 / radius) * dist) + ((1.0 / (radius * radius)) * (dist * dist)));

	gl_Position = (projectionMatrix * (viewMatrix * modelMatrix)) * vec4(inPosition, 1.0);
}

///////////////////////////////////////////////////////
////////////////////FRAGMENT SHADER////////////////////
///////////////////////////////////////////////////////
#version 330
precision mediump float;

in vec2 texCoord;
in vec3 camDir;
in vec3 lightDir;
in float attenuation;

layout (location = 0) out vec4 FragColour;

uniform sampler2D textureMap;
uniform sampler2D normalMap;
uniform sampler2D AOMap;
uniform sampler2D specMap;
uniform sampler2D roughMap;
uniform vec3 lightColour;

vec2 POM(vec3 camDir, vec2 texCoord, out float fragDepth)
{
	float samples = mix(30, 5, abs(dot(vec3(0.0, 0.0, 1.0), camDir)));
	float sampleDist = 1.0 / samples;
	float currentDepth = 0.0;

	vec2 offsetTexCoord = 0.1 * (camDir.xy / (camDir.z * samples));

	vec2 currentTexCoord = texCoord;
	float depthFromMesh = texture(normalMap, currentTexCoord).a;

	while(depthFromMesh > currentDepth)
	{
		currentDepth += sampleDist;
		currentTexCoord -= offsetTexCoord;
		depthFromMesh = texture(normalMap, currentTexCoord).a;
	}

	vec2 prevTexCoord = currentTexCoord + offsetTexCoord;

	float afterIntersection = depthFromMesh - currentDepth;
	float beforeIntersection = texture(normalMap, prevTexCoord).a - currentDepth + sampleDist;

	float ratio = afterIntersection / (afterIntersection - beforeIntersection);

	vec2 finalTexCoord = prevTexCoord * ratio + currentTexCoord * (1.0 - ratio);
	fragDepth = currentDepth + beforeIntersection * ratio + afterIntersection * (1.0 - ratio);

	return finalTexCoord;
}

float selfOcclusion(vec3 lightDir, vec2 texCoord, float initialDepth)
{
	float coefficient = 0.0;
	float occludedSamples = 0.0;
	float newCoefficient = 0.0;

	float samples = 30.0;//mix(30, 5, abs(dot(normal, lightDir)));
	float sampleDist = initialDepth / samples;
	vec2 offsetTexCoord = 0.1 * (lightDir.xy / (lightDir.z * samples));

	float currentDepth = initialDepth - sampleDist;
	vec2 currentTexCoord = texCoord + offsetTexCoord;
	float depthFromMesh = texture(normalMap, currentTexCoord).a;
	float steps = 1.0;

	while(currentDepth > 0.0)
	{
		if(depthFromMesh < currentDepth)
		{
			occludedSamples += 1.0;
			newCoefficient = (currentDepth - depthFromMesh) * (1.0 - steps / samples);
			coefficient = max(coefficient, newCoefficient);
		}
		currentDepth -= sampleDist;
		currentTexCoord += offsetTexCoord;
		depthFromMesh = texture(normalMap, currentTexCoord).a;
		steps += 1.0;
	}

	if(occludedSamples < 1.0)
		coefficient = 1.0;
	else
		coefficient = 1.0 - coefficient;

	return coefficient;
}

void main()
{
	float fragDepth = 0.0;
	
	vec2 offsetTexCoord = POM(camDir, texCoord, fragDepth);
	if (offsetTexCoord.x > 1.0 || offsetTexCoord.y > 1.0 || offsetTexCoord.x < 0.0 || offsetTexCoord.y < 0.0)
		discard;

	vec3 albedo = texture(textureMap, offsetTexCoord.xy).rgb;
	vec3 normals = normalize(texture(normalMap, offsetTexCoord.xy).rgb * 2.0 - 1.0);
	float roughness = texture(roughMap, offsetTexCoord.xy).r;
	float spec = texture(specMap, offsetTexCoord.xy).r;
	float AO = texture(AOMap, offsetTexCoord.xy).r;

	vec3 diffuse = vec3(0.0);
	vec3 specular = vec3(0.0);
	vec3 ambientColour = vec3(0.0);
	float occlusion = 0.0;

	for (int i = 0; i < 1; i++)
	{
		float radius = 50.0;

		vec3 halfAngle = normalize(camDir + lightDir);
		float NdotL = clamp(dot(normals, lightDir), 0.0, 1.0);
		float NdotH = clamp(dot(normals, halfAngle), 0.0, 1.0);

		float specularHighlight = pow(NdotH, 1.0 - roughness);
		vec3 S = spec * (lightColour * specularHighlight);
		vec3 D = (1.0 - roughness) * (lightColour * NdotL);

		occlusion += selfOcclusion(lightDir, offsetTexCoord, fragDepth);
		diffuse += D * attenuation;
		specular += S * attenuation;
		ambientColour += lightColour * attenuation;	
	}

	vec3 ambience = (0.01 * ambientColour) * AO;

	vec3 BlinnPhong = occlusion * (ambience + diffuse + specular);
	vec3 final = albedo * BlinnPhong;
	final = pow(final, vec3(1.0 / 2.2));
	FragColour = vec4(final, 1.0);
}