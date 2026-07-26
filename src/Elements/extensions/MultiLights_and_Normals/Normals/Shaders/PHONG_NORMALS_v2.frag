#version 410
#define MAX_LIGHTS 50 // max number of lights

// Custom fragment shader
// Fragment shader with normal mapping

// Light properties
struct Light {
    float type;
    vec3 position;
    vec3 direction;
    vec3 color;
    float intensity;
    float cutoff;
};


out vec4 color;

in vec4 pos;
in vec3 normal;
in vec2 texCoord;
in mat3 TBN;

// Camera 
uniform vec3 viewPos;

// Ambient
uniform vec3 ambientColor;
uniform float ambientStrength;

// Lights
uniform float numLights;
uniform Light lights[MAX_LIGHTS];

// Attenuation constant
uniform float k;
uniform float d;

// Material
uniform vec3 materialColor;
uniform float shininess;
uniform sampler2D normalMap;
uniform sampler2D albedoMap;
uniform float useAlbedoMap;
uniform float useNormalMap;
uniform float normalStrength;
uniform float debugNormal;

void main()
{
    
    // Sample normal from texture if enabled
    vec3 norm;
    vec3 diffuseSum = vec3(0.0);
    vec3 specSum = vec3(0.0);

    if (useNormalMap > 0.5) {
        vec3 sampledNormal = texture(normalMap, texCoord).rgb;
        // Convert from [0,1] to [-1,1]
        sampledNormal = normalize(sampledNormal * 2.0 - 1.0);
        // Apply normal strength
        sampledNormal.xy *= normalStrength;
        sampledNormal = normalize(sampledNormal);

        // Transform from tangent space to world space using TBN
        norm = normalize(TBN * sampledNormal);
    } else {
        norm = normalize(normal);
    }


    // Debug normal view
    if (debugNormal > 0.5) {
        vec3 dbg = normalize(norm) * 0.5 + 0.5;
        color = vec4(dbg, 1.0);
        return;
    }

    // Albedo (diffuse) selection: use texture if enabled, otherwise materialColor
    vec3 surfaceColor = materialColor;
    if (useAlbedoMap > 0.5) {
        surfaceColor = texture(albedoMap, texCoord).rgb;
    }
    
    vec3 fragPos3D = pos.xyz;
    vec3 viewDir = normalize(viewPos - fragPos3D);
    
    vec3 result = vec3(0.0, 0.0, 0.0);
    for(int i = 0; i < int(numLights); i++)
    {
        vec3 lightDir;

        if (int(lights[i].type) == 1) {
            lightDir = normalize(-lights[i].direction);
        } else {
            lightDir = normalize(lights[i].position - fragPos3D);
        }
        
        float attenuation = 1.0;
        if (int(lights[i].type) != 1) { // point/spot only
            float distance = length(lights[i].position - fragPos3D);
            attenuation = 1.0 / (1.0 + k * distance + d * distance * distance);
        }

        if (int(lights[i].type) == 2) {
            float angle = acos(dot(normalize(lights[i].direction), -lightDir));
            if (angle > radians(lights[i].cutoff)) {
                continue;
            }
        }

        float diff = max(dot(norm, lightDir), 0.0);
        vec3 diffuse = diff * lights[i].color;

        vec3 specular = vec3(0.0);

        if (diff > 0.0)
        {
            vec3 reflectDir = reflect(-lightDir, norm);  
            float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32.0);
            specular = shininess * spec * lights[i].color;
        }

        diffuseSum += diffuse * lights[i].intensity * attenuation;
        specSum += specular * lights[i].intensity * attenuation;
    }

    vec3 ambientProd = ambientStrength * ambientColor;
    // vec3 finalColor = (ambientProd + result) * surfaceColor;
    vec3 finalColor = (ambientProd + diffuseSum) * surfaceColor + specSum;

    finalColor = clamp(finalColor, 0.0, 1.0);
    color = vec4(finalColor, 1.0);
}
