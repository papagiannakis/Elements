#version 410

// Shadow pass 1: geometry shader, point light.
//
// A point light emits in all directions, so one depth map is not enough -- it needs six, forming
// a cube around the light (top, bottom, left, right, front, back).
//
// Without a geometry shader you would ask the CPU to render the whole scene six separate times,
// changing the camera angle for each. That is slow.
//
// With this shader the scene is sent to the GPU once. It acts as a photocopier: it takes one
// triangle in, loops six times, rotates the triangle to face each cube face, and emits it to the
// matching layer of the cube-map texture. This is "layered rendering".
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
