#version 410 core
layout (location = 0) in vec2 aLocal;
layout (location = 1) in vec2 aUV;

uniform mat4 View;
uniform mat4 Proj;
uniform vec3 center;
uniform vec3 camRight;
uniform vec3 camUp;
uniform vec3 size;

out vec2 vUV;

void main() {
    vec3 worldPos = center+ camRight *(aLocal.x *size.x)
                  + camUp    *(aLocal.y *size.y);
    gl_Position= Proj* View *vec4(worldPos, 1.0);
    vUV=aUV;
}
