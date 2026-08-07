#version 410

layout (location=0) in vec4 vPosition;
layout (location=1) in vec4 vNormal;

out vec3 position;
out vec3 normal;

uniform mat4 modelViewProj;
uniform mat4 model;

void main()
{
    gl_Position = modelViewProj * vPosition;
    position = (model * vPosition).xyz;
    normal = mat3(transpose(inverse(model))) * vNormal.xyz;
    normal = normalize(normal);
}
