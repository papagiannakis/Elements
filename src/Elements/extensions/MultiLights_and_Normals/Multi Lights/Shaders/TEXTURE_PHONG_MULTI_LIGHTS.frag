#version 410
#define MAX_LIGHTS 50 // max number of lights 

// Custom fragment shader for TEXTURED objects
// input: an array of lights
// each light has position, color, intensity
// calculates ambient, diffuse, specular for each light

// Light properties
struct Light {
    float type;        // 0 = Point, 1 = Directional, 2 = Spot (stored as float for compatibility)
    vec3 position;   // Point & Spot
    vec3 direction;  // Directional & Spot
    vec3 color;
    float intensity;
    float cutoff;    // Μονο για Spot (γωνια κωνου)
};


out vec4 color;

in vec4 pos;
in vec3 normal;
in vec2 fragmentTexCoord;

// Camera 
uniform vec3 viewPos;

// Ambient
uniform vec3 ambientColor;
uniform float ambientStrength;

// Lights
uniform float numLights;
uniform Light lights[MAX_LIGHTS];

// Attenuation constant
uniform float k;
uniform float d;

// Material
uniform float shininess;
uniform sampler2D ImageTexture;


void main()
{
    
    vec3 norm = normalize(normal);
    vec3 tex = texture(ImageTexture, fragmentTexCoord).xyz;
    vec3 viewDir = normalize(viewPos - pos.xyz);
    vec3 result = vec3(0.0, 0.0, 0.0);

    int n = int(numLights);
    if (n > MAX_LIGHTS) n = MAX_LIGHTS;

    for(int i = 0; i < n; i++)
    {
        vec3 lightDir;

        // Choose direction based on light type
        // Directional lights: lightDir from direction, distance from position for attenuation
        // Point/Spot lights: lightDir from position
        if (int(lights[i].type) == 1) {
            lightDir = normalize(-lights[i].direction); // directional light uses direction
        } else {
            lightDir = normalize(lights[i].position - pos.xyz); // point/spot lights
        }
        
        // Check if spot light is within cutoff cone
        if (int(lights[i].type) == 2) {
            float angle = acos(dot(normalize(lights[i].direction), -lightDir));
            if (angle > radians(lights[i].cutoff)) {
                continue; // Fragment outside spot light cone, skip this light
            }
        }

        // Attenuation, distance-based (quadratic falloff for all light types)
        float attenuation = 1.0;
        if (int(lights[i].type) != 1) { // not directional
            float distance = length(lights[i].position - pos.xyz);
            attenuation = 1.0 / (1.0 + k * distance + d * distance * distance);
        }

        // Diffuse
        float diffuseStr = max(dot(norm, lightDir), 0.0);
        vec3 diffuseProd = diffuseStr * lights[i].color;

        // Specular
        vec3 specularProd = vec3(0.0);
        if (diffuseStr > 0.0)
        {
            vec3 reflectDir = reflect(-lightDir, norm);  
            float specularStr = pow(max(dot(viewDir, reflectDir), 0.0), 32.0);
            //specularProd = shininess * specularStr; 
            specularProd = shininess * specularStr * lights[i].color;
        }

        result += (diffuseProd + specularProd) * lights[i].intensity * attenuation;
    }

    vec3 ambientProd = ambientStrength * ambientColor;
    vec3 finalColor = (ambientProd + result) * tex;
    color = vec4(finalColor, 1.0);

}