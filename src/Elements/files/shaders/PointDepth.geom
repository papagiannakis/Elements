#version 410
layout (triangles) in;
layout (triangle_strip, max_vertices=18) out;

uniform mat4 shadowMatrices[6]; // The 6 View Matrices of the Light

out vec4 FragPos; // Passed to Fragment shader to calc distance

void main() {
    for(int face = 0; face < 6; ++face) {
        gl_Layer = face; // built in variable, selects which Cubemap face to draw to
        for(int i = 0; i < 3; ++i) {
            FragPos = gl_in[i].gl_Position;
            gl_Position = shadowMatrices[face] * FragPos;
            EmitVertex();
        }
        EndPrimitive();
    }
}
