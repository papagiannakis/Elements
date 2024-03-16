// Define a struct for uniform buffer
struct Locals {
    mvp : mat4x4<f32>,
}; 

@group(0) @binding(0) 
var<uniform> MVP : Locals;

// Define the vertex input struct
struct VertexInput {
    @location(0) vPosition : vec4<f32>,
    @location(1) vColor : vec4<f32>,
}; 
struct VertexOutput {   
    @location(0) color : vec4<f32>,
    @builtin(position) pos: vec4<f32>,
}

// Define the output color variable for the fragment shader 
struct FragOutput { 
    @location(0) color : vec4<f32>,
}

// Define the vertex shader 
@vertex
fn Vmain(in : VertexInput) -> VertexOutput {
    // Transform vertex position by modelViewProj matrix 
    var out : VertexOutput; 
    out.pos = MVP.mvp * in.vPosition; 
    out.color = in.vColor; 
    return out;
}

// Define the fragment shader 
@fragment
fn Fmain(in : VertexOutput) -> FragOutput {
    // Pass through the color received from the vertex shader 
    var out : FragOutput;
    out.color = in.color;
    return out;
}