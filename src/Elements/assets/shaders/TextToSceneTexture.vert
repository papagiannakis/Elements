#version 410
layout (location=0) in vec4 vPos;
layout (location=1) in vec2 vTexCoord;
layout (location=2) in vec3 vNormal;

out vec2 fragTexCoord;
out vec3 fragNormal;
out vec3 fragPos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 proj;

void main()
{
    vec4 worldPos = model * vPos;
    fragPos = worldPos.xyz;
    fragNormal = mat3(transpose(inverse(model))) * vNormal;
    fragTexCoord = vTexCoord;
    gl_Position = proj * view * worldPos;
}
