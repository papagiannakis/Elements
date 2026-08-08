#version 410
in vec4 pos;
in vec3 normal;
out vec4 outputColor;

uniform samplerCube environmentMap;
uniform vec3 tintColor;
uniform float tintStrength;
uniform vec3 viewPos;

void main() {
    vec3 N = normalize(normal);
    vec3 I = normalize(pos.xyz - viewPos); // Incident vector
    vec3 R = reflect(I, N);                // Reflection vector

    vec3 envColor = texture(environmentMap, R).rgb;
    vec3 finalColor = mix(envColor, envColor * tintColor, tintStrength);

    outputColor = vec4(finalColor, 1.0);
}
