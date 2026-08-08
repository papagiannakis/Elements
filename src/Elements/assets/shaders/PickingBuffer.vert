#version 410
layout(location = 0) in vec4 vPosition;
uniform mat4 modelViewProj;
void main() {
    gl_Position = modelViewProj * vPosition;
}
