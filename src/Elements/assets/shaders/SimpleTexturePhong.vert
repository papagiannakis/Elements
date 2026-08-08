#version 410

layout (location=0) in vec4 vPos;
layout (location=1) in vec4 vNormal;
layout (location=2) in vec2 vTexCoord;

out vec2 fragmentTexCoord;
out vec4 pos;
out vec3 normal;

uniform mat4 model;
uniform mat4 View;
uniform mat4 Proj;

void main()
{
    gl_Position =  Proj * View * model * vPos;
    pos = model * vPos;
    fragmentTexCoord = vTexCoord;
    normal = mat3(transpose(inverse(model))) * vNormal.xyz;
}
