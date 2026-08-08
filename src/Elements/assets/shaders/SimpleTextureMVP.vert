#version 410

layout (location=0) in vec4 vPos;
layout (location=1) in vec2 vTexCoord;

out vec2 fragmentTexCoord;

uniform mat4 modelViewProj;

void main()
{
    gl_Position =  modelViewProj * vPos;
    fragmentTexCoord = vTexCoord;
}
