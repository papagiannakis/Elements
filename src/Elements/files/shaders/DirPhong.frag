#version 410 core
out vec4 FragColor;
in vec4 FragPos;
in vec3 Normal;
in vec2 TexCoords;
in vec4 FragPosLightSpace;
in vec4 Color;

// Textures
uniform sampler2D ImageTexture;
uniform bool useTexture;

// Shadow Resources
uniform sampler2D shadowMap;

// Light & View
uniform vec3 lightPos;
uniform vec3 viewPos;
uniform vec3 lightColor;

// Settings
uniform int uHasShadow;     // 1 = Shadows Enabled
uniform int uSoftShadows;   // 1 = PCF Enabled
uniform float uPcfDisk;     // Radius of soft shadow sample
uniform int uDebugMode;     // 0=Normal, 1=DepthMap, 2=Comparison
uniform float uShadowBias;  // Threshold to prevent Shadow Acne

// Visualization Colors
uniform vec3 uLitColorViz;    // Color for lit areas in Debug Mode 2
uniform vec3 uShadowColorViz; // Color for shadow areas in Debug Mode 2

// Specular strength; falls back to 0.22 -- see the note in PointPhong.frag.
uniform float shininess;
//: How tight the specular highlight is. Falls back to 64.0, the value this shader used to
//: hard-code, so callers that do not set it render exactly as before.
uniform float specularExponent;

void main() {
    // Normalize Input Vectors (Interpolation de-normalizes them)
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(lightPos - FragPos.xyz);
    vec3 viewDir = normalize(viewPos - FragPos.xyz);
    vec3 reflectDir = reflect(-lightDir, norm);

    // Determine Material Color (Texture or Vertex Color)
    vec3 matColor = useTexture ? texture(ImageTexture, TexCoords).xyz : Color.rgb;

    // --- SHADOW CALCULATION --
    float shadow = 0.0;

    // How far is THIS pixel from the light?
    float currentDepth = 0.0;

    float closestDepth = 0.0;

    // Perspective Divide (convert to NDC -1..1)
    vec3 projCoords = FragPosLightSpace.xyz / FragPosLightSpace.w;
    // Transform to Texture Coordinates (0..1)
    projCoords = projCoords * 0.5 + 0.5;

    // Only calc shadow if the pixel is within the light's view frustum
    if (uHasShadow == 1 && projCoords.z <= 1.0) {
        currentDepth = projCoords.z;

        float bias = uShadowBias;

        if (uSoftShadows == 1) {
            // Percentage Closer Filtering (PCF)
            // We sample neighbors to smooth jagged edges.
            vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
            float radius = max(uPcfDisk, 1.0);
            for(int x = -1; x <= 1; ++x) {
                for(int y = -1; y <= 1; ++y) {
                    float pcfDepth = texture(shadowMap, projCoords.xy + vec2(x, y) * texelSize * radius).r;

                    // If currentDepth > pcfDepth, we are behind something (Shadow)
                    shadow += currentDepth - bias > pcfDepth ? 1.0 : 0.0;


                }
            }
            shadow /= 9.0; // Average the 9 samples
        } else {
            closestDepth = texture(shadowMap, projCoords.xy).r;
            shadow = currentDepth - bias > closestDepth ? 1.0 : 0.0;
        }
    }

    // --- VISUALIZATION ---

    // Fetch raw depth (unbiased)
    closestDepth = texture(shadowMap, projCoords.xy).r;

    // Light Depth View
    if (uDebugMode == 1) {
        if(projCoords.x < 0.0 || projCoords.x > 1.0 || projCoords.y < 0.0 || projCoords.y > 1.0) FragColor = vec4(0,0,0,1);
        else FragColor = vec4(vec3(closestDepth), 1.0);
        return;
    }

    // Shadow Comparison (Red/Green)
    if (uDebugMode == 2) {
        if (shadow > 0.0) FragColor = vec4(uShadowColorViz, 1.0); // Shadow
        else FragColor = vec4(uLitColorViz, 1.0); // Lit
        return;
    }

    // --- PHONG MODEL  ---

    // Ambient
    vec3 ambientProduct = 0.2 * matColor;

    // Diffuse
    float diffuseStr = max(dot(norm, lightDir), 0.0);
    vec3 diffuseProduct = diffuseStr * lightColor * matColor;

    vec3 halfwayDir = normalize(lightDir + viewDir);
    float specExp = specularExponent > 0.0 ? specularExponent : 64.0;
    float specularStr = pow(max(dot(norm, halfwayDir), 0.0), specExp);
    // No highlight on a face turned away from the light.
    float facingLight = step(0.0, dot(norm, lightDir));
    // Specular keeps the light's colour, not the surface's -- see PointPhong.frag.
    // Falls back to 0.22 -- see the note in PointPhong.frag on why not 0.5.
    float specStrength = shininess > 0.0 ? shininess : 0.22;
    vec3 specularProduct = facingLight * specStrength * specularStr * lightColor;


    // Final Composition
    // Ambient is always present. Diffuse & Specular are blocked by shadow.
    vec3 lightingParts = (diffuseProduct + specularProduct) * (1.0 - shadow);
    // Each term already carries the surface colour it should; multiplying by
    // matColor again here applied it twice over.
    vec3 result = ambientProduct + lightingParts;

    FragColor = vec4(result, 1.0);
}
