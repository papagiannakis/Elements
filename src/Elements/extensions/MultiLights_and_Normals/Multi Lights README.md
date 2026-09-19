Multiple Lights 
by VISKADOURAKIS EMMANOUIL (csd5368@csd.uoc.gr), SAVVIDIS ALEXANDROS (csd5002@csd.uoc.gr)

The Multi Lights module contains:

example_multi_lights_3cubes_flat.py
example_multi_lights_3cubes_smooth.py
example_multi_lights_spheres.py

These examples show Phong lighting with multiple lights, and the difference between flat vs smooth normal shading on different objects.
They use multiple lights (Point/Directional/Spot) that can be controlled dynamically from ImGUI (e.g. add/remove lights, change light intensity/color/position, animation). 


The shaders are split into:

solid/per-vertex color shaders: (PHONG_MULTI_LIGHTS), and 

texture shaders: (TEXTURE_PHONG_MULTI_LIGHTS)



a) example_multi_lights_3cubes_flat.py: 3 cubes with flat normal shading, multiple lights, ImGUI control.

3 cubes with the same geometry, but different base color:

Cube 1: Per-vertex colors (color per vertex)

Cube 2: Solid material color (a single fixed material color)

Cube 3: Textured (albedo/texture)

The normals are flat, so each face has "hard" lighting with no smooth transition between faces.

Shaders:
For the per-vertex and solid cube: PHONG_MULTI_LIGHTS.vert/.frag

Supports either vertex-color or solid-color (via the uniform is_solid_color and a materialColor). 

For the textured cube: TEXTURE_PHONG_MULTI_LIGHTS.vert/.frag



b) example_multi_lights_3cubes_smooth.py: 3 cubes with smooth normal shading, multiple lights, ImGUI control.

Same scene as a): 3 cubes (vertex-color, solid color, textured)

The difference is that the normals are smooth (averaged per shared vertex position), so the specular/diffuse lighting runs smoothly across the object.

On a cube, using smooth normals gives a "more spherical" lighting behavior (NOT REALISTIC for cubes), so the edges are lost and the shape appears to curve.

Shaders: The same as a)




c) example_multi_lights_spheres.py: 2 solid-color spheres, one flat and one smooth, multiple lights, ImGUI control.

2 spheres with solid material color, where one is rendered with flat shading and the other with smooth shading.

Since a sphere needs smooth normals to look correct, here the difference becomes more apparent:

flat: faceted/low-poly look

smooth: correct continuous highlight

Shaders:

Uses PHONG_MULTI_LIGHTS.vert/.frag for material-based color (with is_solid_color = 1 and a materialColor).
