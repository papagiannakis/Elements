#version 410
layout (location = 0) in vec4 vPos;
layout (location = 1) in vec4 vColor;
layout (location = 2) in vec4 vNormal;

out vec4 pos;
out vec4 frag_color;
out vec3 normal;

uniform mat4 model;
uniform mat4 View;
uniform mat4 Proj;

void main()
{
    gl_Position =  Proj * View * model * vPos;    
    pos = model * vPos;
    frag_color = vColor;
    normal = mat3(transpose(inverse(model))) * vNormal.xyz;
}