#version 410

uniform vec3 colour_front;
uniform vec3 colour_back;
uniform vec3 view_pos;

uniform float specular_strength;
//: How tight the specular highlight is. Falls back to 32.0, the value this shader used to
//: hard-code, so callers that do not set it render exactly as before.
uniform float specularExponent;

in vec3 position;
in vec3 normal;

out vec4 outputColor;

void main()
{
	vec3 lighting_dir = vec3(-0.71f, 0.71f, 0.0f);
	vec3 view_dir = normalize(view_pos - position);
    vec3 reflectDir = reflect(-lighting_dir, normal);

	float diffuseStr = (dot(normal, lighting_dir) + 2) / 3;
	float specExp = specularExponent > 0.0 ? specularExponent : 32.0;
	float specularStr = pow(max(dot(view_dir, reflectDir), 0.0), specExp) * specular_strength;
	float ambientStr = 0.2f;
	float lightIntensity = 0.7f;

	float factor = ambientStr + (diffuseStr + specularStr) * lightIntensity; // (pow(dot(lighting_dir, normal), 5) + 1) / 2;

	if (dot(normal, view_dir) >= 0) {
		outputColor = vec4(colour_front - normal * 0.07f, 1.0f);
	}
	else {
		outputColor = vec4(colour_back - normal * 0.07f, 1.0f);
	}

	outputColor *= factor;

	// outputColor = vec4(normal, 1.f);
}
