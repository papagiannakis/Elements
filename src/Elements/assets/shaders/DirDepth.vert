#version 410

// Shadow pass 1: depth-map generation, directional light (orthographic projection).
// In a standard render we output colour and normal. Here we ONLY care about position -- all the
// shadow map needs to know is "how far is this pixel?".
layout (location = 0) in vec4 vPosition;

// we use 'lightSpaceMatrix' instead of the Camera's 'projection * view'.
// This transforms the vertex as seen from the LIGHT'S point of view.
uniform mat4 lightSpaceMatrix;
uniform mat4 model;

void main() {
    // transform vertex to world space (model) then to light space.
    gl_Position = lightSpaceMatrix * model * vPosition;
}
