#version 450

layout (location=0) in vec4 vPosition;
layout (location=1) in vec4 vColor;

out vec4 color; 

layout (binding = 0) uniform struct uni { 
    mat4 proj; 
    mat4 view; 
    mat4 model; 
    vec4 clr; 
    float time;
};

void main()
{
    gl_Position = proj * view * model * vPosition;  // Access members without prefixing 'uni'
    color = vColor * clr;  // Access members without prefixing 'uni'
}
