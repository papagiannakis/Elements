#version 410

layout (location=0) in vec4 vPosition;
layout (location=1) in vec4 vColor;

out     vec4 color;
uniform mat4 modelViewProj;


void main()
{
    gl_Position = modelViewProj * vPosition;
    color = vColor;
}
