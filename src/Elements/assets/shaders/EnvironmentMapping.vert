#version 410
layout (location=0) in vec4 vPosition;
layout (location=1) in vec4 vColor;
layout (location=2) in vec4 vNormal;

out vec4 pos;
out vec3 normal;

uniform mat4 modelViewProj;
uniform mat4 model;

void main() {
    gl_Position = modelViewProj * vPosition;
    pos = model * vPosition;
    // Calculate normal in world space
    normal = mat3(transpose(inverse(model))) * vNormal.xyz;
}
