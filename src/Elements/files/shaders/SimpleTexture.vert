#version 410

layout (location=0) in vec4 vPos;
layout (location=1) in vec2 vTexCoord;

out vec2 fragmentTexCoord;

uniform mat4 model;
uniform mat4 View;
uniform mat4 Proj;

void main()
{
    gl_Position =  Proj * View * model * vPos;
    fragmentTexCoord = vTexCoord;
}
