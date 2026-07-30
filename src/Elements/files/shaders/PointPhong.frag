#version 410 
out vec4 FragColor;
in vec4 FragPos;
in vec3 Normal;
in vec2 TexCoords;
in vec4 Color;

uniform sampler2D ImageTexture;
uniform bool useTexture;

// Point lights use a Cube Map (3D Texture)
uniform samplerCube shadowMap;

uniform vec3 lightPos;
uniform vec3 viewPos;
uniform vec3 lightColor;
uniform float far_plane;

uniform int uHasShadow;
uniform int uSoftShadows;
uniform float uPcfDisk;
uniform int uDebugMode;
uniform float uShadowBias;

uniform vec3 uLitColorViz;
uniform vec3 uShadowColorViz;

// --- PCF OFFSET ARRAY ---
// These are 20 pre-defined directions relative to the center.
// We use them to peek at neighboring pixels in the shadow map to average the result.
vec3 gridSamplingDisk[20] = vec3[](
   vec3(1, 1, 1), vec3( 1, -1, 1), vec3(-1, -1, 1), vec3(-1, 1, 1),
   vec3(1, 1, -1), vec3( 1, -1, -1), vec3(-1, -1, -1), vec3(-1, 1, -1),
   vec3(1, 1, 0), vec3( 1, -1, 0), vec3(-1, -1, 0), vec3(-1, 1, 0),
   vec3(1, 0, 1), vec3(-1, 0, 1), vec3( 1, 0, -1), vec3(-1, 0, -1),
   vec3(0, 1, 1), vec3( 0, -1, 1), vec3( 0, -1, -1), vec3( 0, 1, -1));


void main() {           
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(lightPos - FragPos.xyz);
    vec3 viewDir = normalize(viewPos - FragPos.xyz);
    vec3 reflectDir = reflect(-lightDir, norm);

    vec3 matColor = useTexture ? texture(ImageTexture, TexCoords).rgb : Color.rgb;

    // Shadow Calculation
    vec3 fragToLight = FragPos.xyz - lightPos;

    // How far is THIS pixel from the light?
    float currentDepth = length(fragToLight);

    float bias = uShadowBias; 
    float shadow = 0.0;
    float closestDepthRaw = 0.0;

    if (uHasShadow == 1) {
        if (uSoftShadows == 1) {
        // Soft Shadows: Average 20 samples from the cube map
        // Instead of testing just 1 point, we test 20 points around the vector.
        // This blurs the edge of the shadow.

            int samples = 20;

            // The further away the pixel is, the larger the sampling radius should be.

            float diskRadius = (1.0 + (currentDepth / far_plane)) / 25.0; 
            diskRadius *= max(uPcfDisk, 0.1);
            for(int i = 0; i < samples; ++i) {
                // Sample the cube map with an offset
                float val = texture(shadowMap, fragToLight + gridSamplingDisk[i] * diskRadius).r;
                val *= far_plane; // Remap [0,1] to [0, far_plane]

                // The Comparison: Is my depth > stored depth?
                if(currentDepth - bias > val) shadow += 1.0;
            }
            shadow /= float(samples); // Average the results (e.g., if 10/20 are blocked, shadow is 0.5
        } else {
        // Hard Shadows 
            float val = texture(shadowMap, fragToLight).r;
            val *= far_plane;
            if(currentDepth - bias > val) shadow = 1.0;
        }
    }

    // Raw depth for visualizer
    closestDepthRaw = texture(shadowMap, fragToLight).r;

    if (uDebugMode == 1) {
        //float contrastDepth = pow(closestDepthRaw, 0.15);
        FragColor = vec4(vec3(closestDepthRaw), 1.0); 
        return;
    }
    if (uDebugMode == 2) {
        if (shadow > 0.0) FragColor = vec4(uShadowColorViz, 1.0);
        else FragColor = vec4(uLitColorViz, 1.0);
        return;
    }

    // PHONG MODEL
    // Ambient
    vec3 ambientProduct = 0.1 * matColor;

    // Diffuse
    float diffuseStr = max(dot(norm, lightDir), 0.0);
    vec3 diffuseProduct = diffuseStr * lightColor;

    // Specular

    // Blinn-Phong uses the "Halfway" vector (Light + View)
    vec3 halfwayDir = normalize(lightDir + viewDir);  
    float specularStr = pow(max(dot(norm, halfwayDir), 0.0), 64.0);
    vec3 specularProduct = 0.5 * specularStr * matColor;

    // Final Composition
    vec3 lightingParts = (diffuseProduct + specularProduct) * (1.0 - shadow);
    vec3 result = (ambientProduct + lightingParts) * matColor;

    FragColor = vec4(result, 1.0);
}
