#version 410

// Debug / visualisation vertex shader, shared by both debug fragment shaders below.
// Draws a full-screen quad so the shadow map can be inspected directly.
layout (location = 0) in vec2 vPos;
layout (location = 1) in vec2 vTex;
out vec2 TexCoords;
void main() {
    gl_Position = vec4(vPos, 0.0, 1.0);
    TexCoords = vTex;
}
