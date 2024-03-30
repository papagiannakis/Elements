#version 450

in vec4 color;
out vec4 outputColor;

void main() { 
    float gamma_correct = pow(color.rgb, vec3(2.2));
    outputColor = vec4(gamma_correct.rgb, color.a);
}