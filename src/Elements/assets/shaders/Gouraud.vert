#version 410

// Gouraud shading, vertex stage.
//
// Compare with Phong.vert: that one only *forwards* the world position and normal, leaving the
// lighting to Phong.frag, which runs once per fragment. Here the whole lighting equation is
// solved once per *vertex* and only the resulting colour is handed on, so the rasteriser
// interpolates a finished colour rather than a normal.
//
// That is the entire difference between Gouraud and Phong shading, and it is much cheaper: a
// typical mesh has far fewer vertices than covered pixels. The cost is accuracy -- a specular
// highlight smaller than a triangle falls between the vertices and simply disappears, and the
// ones that survive show up as faceted blotches with visible edges along the triangles. The
// coarser the mesh, the worse it gets.

layout (location=0) in vec4 vPosition;
layout (location=1) in vec4 vColor;
layout (location=2) in vec4 vNormal;

out vec4 vertexColor;

uniform mat4 modelViewProj;
uniform mat4 model;

// Phong products
uniform vec3 ambientColor;
uniform float ambientStr;

// Lighting
uniform vec3 viewPos;
uniform vec3 lightPos;
uniform vec3 lightColor;
uniform float lightIntensity;

// Material
uniform float shininess;
//: How *tight* the specular highlight is (shininess, above, is how *strong* it is). Same uniform,
//: same meaning, same 32.0 fallback as Phong.frag -- so feeding both the same value leaves *where*
//: the lighting is evaluated (per vertex here, per fragment there) as the only difference.
//:
//: Raising it is what exposes Gouraud's weakness: the tighter the highlight, the more likely it
//: is to fall between two vertices and never be computed at all.
uniform float specularExponent;

void main()
{
    gl_Position = modelViewProj * vPosition;

    // Identical maths to Phong.frag -- just run here, per vertex, instead of there, per fragment.
    vec4 worldPos = model * vPosition;
    vec3 norm = normalize(mat3(transpose(inverse(model))) * vNormal.xyz);
    vec3 lightDir = normalize(lightPos - worldPos.xyz);
    vec3 viewDir = normalize(viewPos - worldPos.xyz);
    vec3 reflectDir = reflect(-lightDir, norm);

    // Ambient
    vec3 ambientProduct = ambientStr * ambientColor;
    // Diffuse
    float diffuseStr = max(dot(norm, lightDir), 0.0);
    vec3 diffuseProduct = diffuseStr * lightColor;
    // Specular
    float specExp = specularExponent > 0.0 ? specularExponent : 32.0;
    float specularStr = pow(max(dot(viewDir, reflectDir), 0.0), specExp);
    // No highlight on a face turned away from the light.
    float facingLight = step(0.0, dot(norm, lightDir));
    vec3 specularProduct = facingLight * shininess * specularStr * lightColor;

    // Surface colour on the ambient/diffuse terms only; the specular keeps the light's colour.
    // Same composition as Phong.frag -- see the longer note there.
    vec3 result = (ambientProduct + diffuseProduct * lightIntensity) * vColor.xyz
                + specularProduct * lightIntensity;
    vertexColor = vec4(result, 1.0);
}
