#version 410
in vec2 fragTexCoord;
in vec3 fragNormal;
in vec3 fragPos;

out vec4 outputColor;

uniform sampler2D texSampler;
uniform vec3  Lambientcolor;
uniform float Lambientstr;
uniform vec3  LviewPos;
uniform vec3  Lposition;
uniform vec3  Lcolor;
uniform float Lintensity;
//: How tight the specular highlight is. Falls back to 32.0, the value this shader used to
//: hard-code, so callers that do not set it render exactly as before.
uniform float specularExponent;

void main()
{
    vec4  texColor  = texture(texSampler, fragTexCoord);
    vec3  norm      = normalize(fragNormal);
    vec3  ambient   = Lambientstr * Lambientcolor * texColor.rgb;
    vec3  lightDir  = normalize(Lposition - fragPos);
    float diff      = max(dot(norm, lightDir), 0.0);
    vec3  diffuse   = diff * Lcolor * Lintensity * texColor.rgb;
    vec3  viewDir   = normalize(LviewPos - fragPos);
    vec3  reflDir   = reflect(-lightDir, norm);
    float specExp = specularExponent > 0.0 ? specularExponent : 32.0;
    float spec      = pow(max(dot(viewDir, reflDir), 0.0), specExp);
    vec3  specular  = 0.2 * spec * Lcolor * Lintensity;
    outputColor = vec4(ambient + diffuse + specular, texColor.a);
}
