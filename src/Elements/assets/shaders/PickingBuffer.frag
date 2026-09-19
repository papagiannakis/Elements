#version 410
uniform vec3 objectIDColor;
out vec4 FragColor;
void main() {
    FragColor = vec4(objectIDColor, 1.0);
}
