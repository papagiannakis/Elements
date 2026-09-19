#version 410

// Phong.frag's plain point light, extended to understand Directional/Spot too -- used by
// showcase_helpers.py's ObjGallery, so its model reacts to the showcase's LightManager the same
// way SceneBuilder's objects (ShowcaseMultiLight.frag) do, instead of always lighting as if the
// primary light were an omnidirectional point light regardless of its actual type.

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
//: 0 = point, 1 = directional, 2 = spot -- see ShowcaseMultiLight.frag, which every SceneBuilder
//: object is lit by.
uniform float lightType;
uniform vec3 lightDirection;  // directional & spot
uniform float lightCutoff;    // spot only, half-angle in degrees

// Material
uniform float shininess;
//: How *tight* the specular highlight is (shininess, above, is how *strong* it is). Bigger means
//: a smaller, sharper highlight: 8 is a broad sheen, 32 a plastic highlight, 256+ a mirror glint.
//: Left unset it falls back to 32.0, matching Phong.frag's hard-coded default.
uniform float specularExponent;

void main()
{
    vec3 norm = normalize(normal);
    vec3 viewDir = normalize(viewPos - pos.xyz);

    // Ambient: stays lit even outside a spot's cone, same as ShowcaseMultiLight.frag, so nothing
    // ever goes fully black just for standing outside the beam.
    vec3 ambientProduct = ambientStr * ambientColor;

    int type = int(lightType);
    vec3 lightDir = type == 1 ? normalize(-lightDirection) : normalize(lightPos - pos.xyz);
    if (type == 2) {
        // outside the spotlight's cone?
        float angle = degrees(acos(clamp(dot(normalize(lightDirection), -lightDir), -1.0, 1.0)));
        if (angle > lightCutoff) {
            outputColor = vec4(ambientProduct * color.xyz, 1);
            return;
        }
    }

    vec3 reflectDir = reflect(-lightDir, norm);

    // Diffuse
    float diffuseStr = max(dot(norm, lightDir), 0.0);
    vec3 diffuseProduct = diffuseStr * lightColor;
    // Specular
    float specExp = specularExponent > 0.0 ? specularExponent : 32.0;
    float specularStr = pow(max(dot(viewDir, reflectDir), 0.0), specExp);
    // No highlight on a face turned away from the light: reflectDir can still point at the viewer
    // when the light is behind the surface, which would otherwise leak a highlight onto the dark side.
    float facingLight = step(0.0, dot(norm, lightDir));
    vec3 specularProduct = facingLight * shininess * specularStr * lightColor;

    // Ambient and diffuse are light that entered the material and picked up its colour, so they
    // are multiplied by the surface colour. The specular lobe reflects straight off the surface
    // without entering it, so it keeps the *light's* colour and gets no surface colour at all --
    // that is why a red plastic ball under a white lamp has a white highlight. Only conductors
    // (gold, copper) tint their highlights. Note the specular is deliberately outside the
    // "* color.xyz" below; folding it in would apply the surface colour to it twice over.
    vec3 result = (ambientProduct + diffuseProduct * lightIntensity) * color.xyz
                + specularProduct * lightIntensity;
    outputColor = vec4(result, 1);
}
