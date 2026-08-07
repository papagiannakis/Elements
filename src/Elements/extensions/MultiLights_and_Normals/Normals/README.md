Normal Mapping on a Textured Cube, Flat vs Smooth Normals
by VISKADOURAKIS EMMANOUIL (csd5368@csd.uoc.gr), SAVVIDIS ALEXANDROS (csd5002@csd.uoc.gr)

The Normals module contains:

example_normals_map_flat.py: flat normals per face (hard edges)
example_normals_map_smooth.py: smooth normals (averaged over shared positions)

These examples show the same textured cube (albedo + normal map), but with a different way of computing normals: flat vs smooth.
In both examples the lighting is Phong with multiple lights, and there is an ImGUI panel to control normal mapping/albedo/debug normals.

Both examples have:

A cube with 24 vertices (4 per face) so that each face has correct UVs.

Normal map calculations where tangents/bitangents are computed from triangles + UVs, with handedness (tangent.w) and an orthonormal TBN in the vertex shader.

Textures for albedo and normal map.

Shaders (the same for both):

PHONG_NORMALS_v2.vert 

PHONG_NORMALS_v2.frag



sources:
https://learnopengl.com/Advanced-Lighting/Normal-Mapping
https://ogldev.org/www/tutorial26/tutorial26.html
https://www.opengl-tutorial.org/intermediate-tutorials/tutorial-13-normal-mapping/#handedness
https://www.youtube.com/watch?v=4FaWLgsctqY
