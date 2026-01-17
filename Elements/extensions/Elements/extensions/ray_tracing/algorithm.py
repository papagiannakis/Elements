import numpy as np
from OpenGL.GL import *

# Vertex Shader
VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec2 aPos;
out vec2 TexCoords;
void main() {
    TexCoords = aPos * 0.5 + 0.5;
    gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0);
}
"""

# Fragment Shader (Ambient Occlusion Ray Tracing)
FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;
in vec2 TexCoords;
uniform vec2 resolution;
uniform vec3 camPos;
uniform vec3 camDir;
uniform float iTime; 
#define MAX_SPHERES 100
uniform vec4 spheres[MAX_SPHERES];
uniform vec3 sphereColors[MAX_SPHERES];
uniform int sphereCount;
#define AO_MAX_DIST 3.0 
#define MAX_RAY_DIST 1000.0
#define HIT_TOLERANCE 0.001
#define AMBIENT_INTENSITY 1.2

float intersectSphere(vec3 ro, vec3 rd, vec4 sphere) {
    vec3 oc = ro - sphere.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sphere.w * sphere.w;
    float disc = b*b - c; 
    if (disc < 0.0) return -1.0;
    float q = sqrt(disc);
    float t0 = -b - q;
    float t1 = -b + q;
    if (t0 > HIT_TOLERANCE) return t0;
    if (t1 > HIT_TOLERANCE) return t1;
    return -1.0;
}

float calculateAO(vec3 p, vec3 n) {
    float occ = 0.0;
    float totalWeight = 0.0;
    for(int i = 0; i < sphereCount; i++) {
        vec3 center = spheres[i].xyz;
        float radius = spheres[i].w;
        vec3 dir = center - p;
        float dist = length(dir);
        if(dist < AO_MAX_DIST + radius) {
            vec3 n_dir = dir / dist; 
            float surfaceDist = max(0.0, dist - radius);
            float NdotD = dot(n, n_dir); 
            float influence = 1.0 - (surfaceDist / AO_MAX_DIST);
            influence = clamp(influence, 0.0, 1.0);
            if (NdotD > 0.01) {
                occ += influence * NdotD * NdotD; 
            }
            totalWeight += 1.0; 
        }
    }
    if (totalWeight > 0.0) occ /= totalWeight;
    return 1.0 - clamp(occ * 4.0, 0.0, 1.0); 
}

void main() {
    vec2 uv = (TexCoords - 0.5) * 2.0;
    uv.x *= resolution.x / resolution.y;
    vec3 ro = camPos;
    vec3 forward = normalize(camDir);
    vec3 right = normalize(cross(forward, vec3(0.0, 1.0, 0.0)));
    vec3 up = cross(right, forward);
    vec3 rd = normalize(forward + uv.x * right + uv.y * up);
    float minT = MAX_RAY_DIST;
    int hitIndex = -1;
    for(int i = 0; i < sphereCount; i++) {
        float t = intersectSphere(ro, rd, spheres[i]);
        if(t > HIT_TOLERANCE && t < minT) {
            minT = t;
            hitIndex = i;
        }
    }
    vec3 col = vec3(0.1, 0.1, 0.15);
    if(hitIndex != -1) {
        vec3 p = ro + rd * minT; 
        vec3 n = normalize(p - spheres[hitIndex].xyz); 
        float ao = calculateAO(p, n);
        vec3 objColor = sphereColors[hitIndex];
        float min_ambient = 0.05;
        float lightFactor = min_ambient + (AMBIENT_INTENSITY - min_ambient) * ao;
        col = objColor * lightFactor;
        col = clamp(col, 0.0, 1.0);
    }
    FragColor = vec4(col, 1.0);
}
"""

def compile_shader(source, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        raise RuntimeError(glGetShaderInfoLog(shader).decode('utf-8'))
    return shader

def create_raytracing_program():
    vertex = compile_shader(VERTEX_SHADER, GL_VERTEX_SHADER)
    fragment = compile_shader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
    program = glCreateProgram()
    glAttachShader(program, vertex)
    glAttachShader(program, fragment)
    glLinkProgram(program)
    return program
