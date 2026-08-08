#version 410
#define MAX_LIGHTS 4

struct Light {
    float type;     // 0 = point, 1 = directional, 2 = spot
    vec3 position;  // point & spot
    vec3 direction; // directional & spot
    vec3 color;
    float intensity;
    float cutoff;   // spot only, half-angle in degrees
};

out vec4 FragColor;
in vec4 FragPos;
in vec3 Normal;
in vec2 TexCoords;
in vec4 Color;

uniform sampler2D ImageTexture;
uniform bool useTexture;

// Shadows: only ever sampled for lights[0], and only while it's a Point light.
uniform samplerCube shadowMap;
uniform float far_plane;
uniform int uHasShadow;
uniform int uSoftShadows;
uniform float uPcfDisk;
uniform float uShadowBias;

uniform vec3 viewPos;
uniform float numLights;
uniform Light lights[MAX_LIGHTS];
//: How tight the specular highlight is. Falls back to 64.0, the value this shader used to
//: hard-code, so callers that do not set it render exactly as before.
uniform float specularExponent;

vec3 gridSamplingDisk[20] = vec3[](
   vec3(1, 1, 1), vec3( 1, -1, 1), vec3(-1, -1, 1), vec3(-1, 1, 1),
   vec3(1, 1, -1), vec3( 1, -1, -1), vec3(-1, -1, -1), vec3(-1, 1, -1),
   vec3(1, 1, 0), vec3( 1, -1, 0), vec3(-1, -1, 0), vec3(-1, 1, 0),
   vec3(1, 0, 1), vec3(-1, 0, 1), vec3( 1, 0, -1), vec3(-1, 0, -1),
   vec3(0, 1, 1), vec3( 0, -1, 1), vec3( 0, -1, -1), vec3( 0, 1, -1));

float computeShadow(vec3 lightPos) {
    if (uHasShadow == 0) return 0.0;

    vec3 fragToLight = FragPos.xyz - lightPos;
    float currentDepth = length(fragToLight);
    float shadow = 0.0;

    if (uSoftShadows == 1) {
        int samples = 20;
        float diskRadius = (1.0 + (currentDepth / far_plane)) / 25.0;
        diskRadius *= max(uPcfDisk, 0.1);
        for (int i = 0; i < samples; ++i) {
            float val = texture(shadowMap, fragToLight + gridSamplingDisk[i] * diskRadius).r * far_plane;
            if (currentDepth - uShadowBias > val) shadow += 1.0;
        }
        shadow /= float(samples);
    } else {
        float val = texture(shadowMap, fragToLight).r * far_plane;
        if (currentDepth - uShadowBias > val) shadow = 1.0;
    }
    return shadow;
}

void main() {
    vec3 norm = normalize(Normal);
    vec3 viewDir = normalize(viewPos - FragPos.xyz);
    vec3 matColor = useTexture ? texture(ImageTexture, TexCoords).rgb : Color.rgb;

    vec3 result = vec3(0.0);
    int n = clamp(int(numLights), 0, MAX_LIGHTS);

    for (int i = 0; i < n; i++) {
        int type = int(lights[i].type);
        vec3 lightDir;
        if (type == 1) {
            lightDir = normalize(-lights[i].direction);        // directional: parallel rays
        } else {
            lightDir = normalize(lights[i].position - FragPos.xyz); // point & spot
        }

        if (type == 2) {
            // outside the spotlight's cone?
            float angle = degrees(acos(clamp(dot(normalize(lights[i].direction), -lightDir), -1.0, 1.0)));
            if (angle > lights[i].cutoff) continue;
        }

        float diffuseStr = max(dot(norm, lightDir), 0.0);
        vec3 diffuseProd = diffuseStr * lights[i].color * matColor;

        vec3 halfwayDir = normalize(lightDir + viewDir);
        float specExp = specularExponent > 0.0 ? specularExponent : 64.0;
        float specularStr = pow(max(dot(norm, halfwayDir), 0.0), specExp);
        // Specular keeps the light's colour and takes no matColor -- see PointPhong.frag.
        float facingLight = step(0.0, dot(norm, lightDir));
        vec3 specularProd = facingLight * 0.5 * specularStr * lights[i].color;

        // Only the primary (index 0) Point light casts shadows in this simplified engine.
        float shadow = (i == 0 && type == 0) ? computeShadow(lights[i].position) : 0.0;

        result += (diffuseProd + specularProd) * lights[i].intensity * (1.0 - shadow);
    }

    vec3 ambientProd = 0.1 * matColor;
    // result already carries matColor on its diffuse term; the specular deliberately does not.
    FragColor = vec4(ambientProd + result, 1.0);
}
