#version 410
layout (location = 0) in vec4 vPosition;
uniform mat4 model;
void main() {
    gl_Position = model * vPosition;
}
