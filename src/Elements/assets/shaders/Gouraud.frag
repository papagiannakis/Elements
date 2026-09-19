#version 410

// Gouraud shading, fragment stage.
//
// There is nothing to do here: Gouraud.vert already solved the lighting equation at each vertex,
// and the rasteriser has linearly interpolated the resulting colours across the triangle. This
// shader just writes that interpolated colour out. Contrast with Phong.frag, which receives an
// interpolated *normal* and does the full lighting computation for every single fragment.

in vec4 vertexColor;

out vec4 outputColor;

void main()
{
    outputColor = vertexColor;
}
