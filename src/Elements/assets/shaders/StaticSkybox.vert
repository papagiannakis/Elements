#version 410

layout (location = 0) in vec4 vPos;

out vec3 TexCoords;

uniform mat4 Proj;
uniform mat4 View;

void main()
{
    mat4 viewPos = mat4(mat3(View)); //removes Translation
    gl_Position = Proj * viewPos * vPos;

    //gl_Position = Proj * View * vPos; // with Translation

    TexCoords = vPos.xyz;
}
