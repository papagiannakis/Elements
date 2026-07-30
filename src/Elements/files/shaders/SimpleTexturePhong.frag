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
//uniform vec3 matColor;

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
    float specularStr = pow(max(dot(viewDir, reflectDir), 0.0), 32);

    vec4 tex = texture(ImageTexture,fragmentTexCoord);

    vec3 specularProduct = shininess * specularStr * tex.xyz;

    vec3 result = (ambientProduct + (diffuseProduct + specularProduct) * lightIntensity) * tex.xyz;
    outputColor = vec4(result, 1);
}
