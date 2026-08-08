#version 410

// Shadow pass 1: depth-map generation, point light (perspective projection).
layout (location = 0) in vec4 vPosition;
uniform mat4 model;
void main() {
    gl_Position = model * vPosition;
}
