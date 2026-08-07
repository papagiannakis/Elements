#version 410 core

// Output color
out vec4 FragColor;

// Inputs from vertex shader (Standard.vert)
in vec3 WorldPos;      // Fragment position in world space
in vec3 Normal;        // Surface normal in world space

// Uniforms
uniform vec3 camPos;         // Camera position for calculating view direction
uniform float u_Ratio;       // Refractive index ratio (n1/n2, e.g., air/glass = 1.0/1.52)
uniform samplerCube cubemap; // Environment cubemap for reflection/refraction

void main() {
    // Calculate incident ray: direction from camera to fragment
    vec3 I = normalize(WorldPos - camPos);

    // Normalize the interpolated normal
    vec3 N = normalize(Normal);

    // Ensure normal always faces the camera (handles back-facing polygons)
    // If dot product is positive, normal points away from camera
    if (dot(N, I) > 0.0) {
        N = -N;  // Flip normal to face camera
    }

    // Apply Snell's law: calculate refracted ray direction
    // refract(I, N, eta) returns the refraction vector
    // eta = ratio of indices of refraction (n1/n2)
    vec3 R = refract(I, N, u_Ratio);

    // Handle total internal reflection
    // When refraction is impossible (returns zero vector), use reflection instead
    // This occurs when light tries to exit a denser medium at too steep an angle
    if (length(R) < 0.01) {
        R = reflect(I, N);  // Fallback to mirror reflection
    }

    // Sample the environment cubemap using refracted direction
    vec3 color = texture(cubemap, R).rgb;

    // Apply subtle blue tint to simulate glass appearance
    vec3 glassTint = vec3(0.85, 0.92, 1.0);  // Light blue tint
    color = mix(color, glassTint, 0.12);      // Blend 12% tint

    // Output final color with full opacity
    FragColor = vec4(color, 1.0);
}
