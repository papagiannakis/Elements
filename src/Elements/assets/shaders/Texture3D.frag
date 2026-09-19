#version 410

in vec3 TexCoords;

out vec4 FragColor;

uniform samplerCube cubemap; 

void main()
{             
    FragColor = texture(cubemap, TexCoords);
}
