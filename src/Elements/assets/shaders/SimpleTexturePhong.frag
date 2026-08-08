#version 410

in vec2 fragmentTexCoord;
in vec4 pos;
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
//: a smaller, sharper highlight. Left unset it falls back to 32.0, the value this shader used to
//: hard-code, so code written before this was a uniform keeps rendering exactly as it did.
uniform float specularExponent;

uniform sampler2D ImageTexture;

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

    vec4 tex = texture(ImageTexture,fragmentTexCoord);

    // No highlight on a face turned away from the light.
    float facingLight = step(0.0, dot(norm, lightDir));
    vec3 specularProduct = facingLight * shininess * specularStr * lightColor;

    // The texture colours the ambient/diffuse terms only; the specular keeps the light's colour,
    // so a textured surface still gets a white highlight. Same composition as Phong.frag.
    vec3 result = (ambientProduct + diffuseProduct * lightIntensity) * tex.xyz
                + specularProduct * lightIntensity;
    outputColor = vec4(result, 1);
}
