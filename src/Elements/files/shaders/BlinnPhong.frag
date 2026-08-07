#version 410

// Blinn-Phong shading. Pairs with Phong.vert -- the vertex stage is *identical* to plain Phong,
// which is the point: Phong and Blinn-Phong differ in exactly one line of the fragment shader
// (see halfwayDir below). Both evaluate the lighting per fragment.

in vec4 pos;
in vec4 color;
in vec3 normal;

out vec4 outputColor;

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
//: same meaning, as in Phong.frag -- and left unset it falls back to the same 32.0.
//:
//: Note that feeding Phong.frag and this shader the *same* exponent does not give the same
//: highlight: the angle Blinn-Phong measures (normal vs halfway vector) is roughly half the angle
//: Phong measures (viewer vs reflected ray), so at an equal exponent Blinn-Phong's highlight comes
//: out visibly wider. Give this shader about 4x Phong's exponent to match them -- that
//: equivalence, for less work per fragment, is the usual reason to prefer Blinn-Phong.
uniform float specularExponent;

void main()
{
    vec3 norm = normalize(normal);
    vec3 lightDir = normalize(lightPos - pos.xyz);
    vec3 viewDir = normalize(viewPos - pos.xyz);

    // >>> The one line that differs from Phong.frag <<<
    // Phong.frag reflects the light ray about the normal and compares it to the viewer:
    //     reflectDir = reflect(-lightDir, norm);   specular = dot(viewDir, reflectDir)
    // Blinn-Phong instead builds the vector halfway between the light and the viewer and
    // compares *that* to the normal. It needs no reflect() and, unlike Phong, never loses the
    // highlight at grazing angles (where dot(viewDir, reflectDir) can go negative).
    vec3 halfwayDir = normalize(lightDir + viewDir);

    // Ambient
    vec3 ambientProduct = ambientStr * ambientColor;
    // Diffuse
    float diffuseStr = max(dot(norm, lightDir), 0.0);
    vec3 diffuseProduct = diffuseStr * lightColor;
    // Specular
    float specExp = specularExponent > 0.0 ? specularExponent : 32.0;
    float specularStr = pow(max(dot(norm, halfwayDir), 0.0), specExp);
    // No highlight on a face turned away from the light -- dot(norm, halfwayDir) can still be
    // positive when the light is behind the surface.
    float facingLight = step(0.0, dot(norm, lightDir));
    vec3 specularProduct = facingLight * shininess * specularStr * lightColor;

    // Surface colour on the ambient/diffuse terms only; the specular keeps the light's colour.
    // Same composition as Phong.frag -- see the longer note there.
    vec3 result = (ambientProduct + diffuseProduct * lightIntensity) * color.xyz
                + specularProduct * lightIntensity;
    outputColor = vec4(result, 1);
}
