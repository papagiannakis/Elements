#version 410
out vec4 FragColor;
in vec2 TexCoords;

uniform sampler2D depthMap;

void main() {
    float depthValue = texture(depthMap, TexCoords).r;
    // contrast stretch, to enhance visibility
    float contrast = pow(depthValue, 4.0);
    FragColor = vec4(vec3(contrast), 1.0);
}
