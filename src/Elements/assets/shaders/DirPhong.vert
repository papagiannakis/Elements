#version 410

// Shadow pass 2: scene rendering, directional light.
// A standard vertex shader, except that it also computes FragPosLightSpace so the fragment stage
// can look the fragment up in the shadow map.
layout (location = 0) in vec4 vPosition;
layout (location = 1) in vec4 vColor;
layout (location = 2) in vec4 vNormal;
layout (location = 3) in vec2 vTexCoord;

out vec4 FragPos;
out vec3 Normal;
out vec2 TexCoords;

// This tells the Fragment Shader where this pixel
// lands on the Shadow Map texture we created in Pass 1.
out vec4 FragPosLightSpace;
out vec4 Color;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;
uniform mat4 lightSpaceMatrix; // passed again to calculate shadow coordinates

void main() {
    FragPos = model * vPosition; // world position
    Normal = transpose(inverse(mat3(model))) * vNormal.xyz; // normal scaling
    TexCoords = vTexCoord;
    Color = vColor;

    // where this vertex is inside the Light's View
    FragPosLightSpace = lightSpaceMatrix * FragPos;

    // camera position
    gl_Position = projection * view * FragPos;
}
