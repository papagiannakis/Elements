#version 410

in vec4 color;
out vec4 outputColor;

void main()
{
    outputColor = color;
    //outputColor = vec4(0.1, 0.1, 0.1, 1);
}
