#version 410
out vec4 FragColor;
in vec2 TexCoords;

uniform samplerCube depthMap;

void main() {
    vec2 uv = TexCoords;
    // Map 0..1 UVs to a 4x3 Grid
    // x: 0..4, y: 0..3
    float col = floor(uv.x * 4.0);
    float row = floor(uv.y * 3.0);

    // Local UV coordinates inside each grid cell (0..1)
    vec2 subUV = vec2(fract(uv.x * 4.0), fract(uv.y * 3.0));
    // Map subUV to -1..1 range for direction calculation
    vec2 boxUV = subUV * 2.0 - 1.0;

    vec3 dir = vec3(0.0);
    bool valid = false;

    // Row 1 (Middle): The horizontal strip
    if (row == 1.0) {
        if (col == 0.0) {
            // Left Face (-X)
            dir = vec3(-1.0, -boxUV.y, boxUV.x);
            valid = true;
        }
        else if (col == 1.0) {
            // Front Face (+Z)
            dir = vec3(boxUV.x, -boxUV.y, 1.0);
            valid = true;
        }
        else if (col == 2.0) {
            // Right Face (+X)
            dir = vec3(1.0, -boxUV.y, -boxUV.x);
            valid = true;
        }
        else if (col == 3.0) {
            // Back Face (-Z)
            dir = vec3(-boxUV.x, -boxUV.y, -1.0);
            valid = true;
        }
    }
    // Vertical Strip (Top/Bottom) aligned with Front Face (+Z) which is col 1
    if (col == 1.0) {
        if (row == 2.0) {
            // Top Face (+Y)
            dir = vec3(boxUV.x, 1.0, boxUV.y);
            valid = true;
        }
        if (row == 0.0) {
            // Bottom Face (-Y)
            dir = vec3(boxUV.x, -1.0, -boxUV.y);
            valid = true;
        }
    }

    if (!valid) {
        // Draw Dark Grey for empty spaces in the cross
        FragColor = vec4(0.1, 0.1, 0.1, 1.0);
        return;
    }

    float depthValue = texture(depthMap, normalize(dir)).r;

    // contrast stretch, to enhance visibility
    float display = 1.0 - depthValue;
    display = pow(display, 15.0);

    FragColor = vec4(vec3(display), 1.0);

}
