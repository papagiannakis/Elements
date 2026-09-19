#version 410 core
in vec2 vUV;
out vec4 FragColor;

uniform sampler2D uTex;

void main() {
    vec4 texel =texture(uTex, vUV);
    if (texel.a < 0.1) discard;
    FragColor= texel;
}
