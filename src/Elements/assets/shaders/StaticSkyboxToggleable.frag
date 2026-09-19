#version 410
out vec4 FragColor;
in vec3 TexCoords;
uniform samplerCube cubemap;
uniform float enabled;
void main() {
    if (enabled < 0.5) discard;
    FragColor = texture(cubemap, TexCoords);
}
