#version 410 
layout (location = 0) in vec4 vPosition;
layout (location = 1) in vec4 vColor;
layout (location = 2) in vec4 vNormal;
layout (location = 3) in vec2 vTexCoord; 

out vec4 FragPos;
out vec3 Normal;
out vec2 TexCoords;
out vec4 Color;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

void main() {
    FragPos = model * vPosition;
    Normal = transpose(inverse(mat3(model))) * vNormal.xyz;
    TexCoords = vTexCoord;
    Color = vColor;
    gl_Position = projection * view * FragPos;
}
