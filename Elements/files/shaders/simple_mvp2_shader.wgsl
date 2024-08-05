struct VertexInput {
    @location(0) a_position : vec3f,
    @location(1) a_color : vec4f
};
struct VertexOutput {
    @builtin(position) v_position: vec4f,
    @location(0) v_color : vec4f
};

struct Uniforms {
    projectionMatrix: mat4x4f,
    viewMatrix: mat4x4f,
    modelMatrix: mat4x4f,
    color: vec4f,
    time: f32,
};

@group(0) @binding(0) var<uniform> u_Uniforms: Uniforms;

@vertex
fn vs_main(in: VertexInput) -> VertexOutput {
    var out: VertexOutput;
	out.v_position = u_Uniforms.projectionMatrix * u_Uniforms.viewMatrix * u_Uniforms.modelMatrix * vec4f(in.a_position, 1.0);
	out.v_color = in.a_color * u_Uniforms.color;
	return out;
}

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4f {
	// Gamma-correction
	let corrected_color = pow(in.v_color.rgb, vec3f(2.2));
	return vec4f(corrected_color, in.v_color.a);
}