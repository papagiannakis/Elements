#version 410

in vec2 fragmentTexCoord;

out vec4 color;

uniform sampler2D ImageTexture;

void main()
{
    //vec2 flipped_texcoord = vec2(fragmentTexCoord.x, 1.0 - fragmentTexCoord.y);
    //color = texture(ImageTexture,flipped_texcoord);

    color = texture(ImageTexture,fragmentTexCoord);
}
