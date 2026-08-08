#version 410

layout (location=0) in vec4 vPos;

out vec3 TexCoords;

uniform mat4 model;
uniform mat4 View;
uniform mat4 Proj;

void main()
{
    gl_Position = Proj * View * model * vPos;
    TexCoords = vPos.xyz;
}
