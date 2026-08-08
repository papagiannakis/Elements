#version 410

// Shadow pass 1: depth-map generation, point light.
// Unlike the directional case, the linear distance to the light is computed manually here.
in vec4 FragPos;

uniform vec3 lightPos;
uniform float far_plane;

void main() {
    float lightDistance = length(FragPos.xyz - lightPos);
    // map to [0,1] range by dividing by far_plane
    lightDistance = lightDistance / far_plane;
    gl_FragDepth = lightDistance;
}
