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
uniform vec3 matColor;

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
    vec3 specularProduct = shininess * specularStr * color.xyz;

    vec3 result = (ambientProduct + (diffuseProduct + specularProduct) * lightIntensity) * color.xyz;
    outputColor = vec4(result, 1);
}
