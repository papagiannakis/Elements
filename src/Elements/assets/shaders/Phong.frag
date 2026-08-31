#version 410

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
//: How *tight* the specular highlight is (shininess, above, is how *strong* it is). Bigger means
//: a smaller, sharper highlight: 8 is a broad sheen, 32 a plastic highlight, 256+ a mirror glint.
//: Left unset it falls back to 32.0, the value this shader used to hard-code, so code written
//: before this was a uniform keeps rendering exactly as it did.
uniform float specularExponent;

void main()
{
    vec3 norm = normalize(normal);
    vec3 lightDir = normalize(lightPos - pos.xyz);
    vec3 viewDir = normalize(viewPos - pos.xyz);
    vec3 reflectDir = reflect(-lightDir, norm);


    // Ambient
    vec3 ambientProduct = ambientStr * ambientColor;
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
