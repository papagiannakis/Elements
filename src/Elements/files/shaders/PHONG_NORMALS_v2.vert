#version 410
// Vertex shader with normal mapping support
layout (location = 0) in vec4 vPos;
layout (location = 1) in vec4 vColor;
layout (location = 2) in vec4 vNormal;
layout (location = 3) in vec2 vTexCoord;
layout (location = 4) in vec4 vTangent;
layout (location = 5) in vec4 vBitangent;   //deprecaetd

out vec4 pos;
out vec3 normal;
out vec2 texCoord;
out mat3 TBN;

uniform mat4 model;
uniform mat4 View;
uniform mat4 Proj;

void main()
{  
    gl_Position =  Proj * View * model * vPos;
    pos = model * vPos;
    
    // Transform to world space (normal matrix)
    mat3 normalMat = mat3(transpose(inverse(model)));

    vec3 N = normalize(normalMat * vNormal.xyz);    
    vec3 T = normalize(normalMat * vTangent.xyz);

    // Gram-Schmidt, make T orthogonal to N
    T = normalize(T - N * dot(N, T));

    // Reconstruct B to guarantee orthogonality.
    // vTangent.w = handedness (+1 or -1)
    vec3 B = normalize(cross(N, T)) * vTangent.w;

    TBN = mat3(T, B, N);

    normal = N;
    texCoord = vTexCoord;

}

