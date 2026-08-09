# Examples

Below you may find the description of the examples provided in this folder. In most examples with a rendered scene, 
you may move the camera using the mouse. Check [Mouse Controls](#mouse-controls) for more information.

## A.Showcase examples

A single combined demo that ties several techniques together.

  * [example_showcase.py](./A.Showcase/example_showcase.py): An extended version of the picking tutorial (click-to-orbit, lights, projection, shadows) with four extra swappable panels: an OBJ model gallery (Teapot/Cow/Teddy with smooth/flat shading), a cubemap skybox, a refractive "glass" object, and a reflective "mirror" object.

## B.Introductory examples

These examples are suitable for introduction to Computer Graphics and Elements.

  * [Example B1](./B.Introductory/example_B1_component_system.py): A plain example of a component and a system, without any rendering
  * [Example B2](./B.Introductory/example_B2_empty_window.py): A plain empty window rendered. Demonstrates the basic setup of a window and a renderer.
  * [Example B3](./B.Introductory/example_B3_empty_window_with_GUI.py): A plain empty window rendered with GUI enabled. You may change the background color via the GUI and check the FPS, as well as information on the openGL version and the renderer.
  * [Example B4](./B.Introductory/example_B4_simple_cube.py): A scene containing a cube. The camera is staticly defined within the code and the `lookAt` is used to create the projection matrix. 
  * [Example B5](./B.Introductory/example_B5_cube_free_fly.py): A scene containing a cube, and a terrain. 
  The camera can be altered via the GUI or the mouse. The Scenegraph is also shown in a separate GUI (read-only).
  * [Example B6](./B.Introductory/example_B6_lights_cube.py): A scene containing a cube, terrain, axes. Lights via 
  the Blinn-Phong algorithm. Camera can be altered via the GUI or the mouse. The Scenegraph is also shown in a separate GUI. 
  If *a single* TRS component (except the camera) is toggled in the Scenegraph, you may alter the TRS via the Translation/Rotation/Scale properties on top.
  * [Example B7](./B.Introductory/example_B7_import_objects.py): A scene with a teapot. Camera can be altered via the GUI or the mouse. The example demonstrated the import of objects from `.obj` files.
  * [Example B8](./B.Introductory/example_B8_shading_models.py): Six copies of one imported model in a 2x3 grid, comparing the three classic shading models side by side under an identical light, material and camera. Columns are Phong / Blinn-Phong / Gouraud; the front row uses flat (sharp) normals and the back row smooth normals. Phong and Blinn-Phong both shade per fragment and differ in a single line of the fragment shader; Gouraud shades per vertex and interpolates, so its highlights are faceted and can disappear between vertices. The default model is a deliberately coarse 252-triangle sphere, since a dense mesh cannot show Gouraud failing; change `MODEL` at the top of the file to load an `.obj` instead.
  * [Example B9](./B.Introductory/example_B9_shading_comparison.py): The same three shading models as B8, but interactive and one object at a time. An ImGui panel switches the Object, the Normals (smooth or flat) and the Shading (Phong / Blinn-Phong / Gouraud) independently, with the light, material and camera held fixed. Good for orbiting a single object while flipping one variable; B8 is the better side-by-side comparison.
  * [Example B10](./B.Introductory/example_B10_specular_grid.py): A materials chart of 16 identical spheres under identical light, varying only the two specular parameters: `specularExponent` across the columns (4, 16, 64, 256 — the highlight gets tighter) and `shininess` down the rows (0.2 to 1.0 — it gets brighter). Shows that the exponent sets the highlight's *size* while shininess only sets its *intensity*, despite the name. Each sphere gets its own light and viewer offset from its own centre, so position cannot be mistaken for a material difference. The red spheres get white highlights, because `Phong.frag` applies the surface colour to the ambient and diffuse terms only and leaves the specular the colour of the light — which is what non-metals actually do.
  
## C.Intermediate examples

Intermediate examples of textures (2D and Cubemaps), lights, and complete ECS.

  * [Example C1](./C.Intermediate/example_C1_camera_system.py): A scene using the camera system. The camera can be altered via the mouse or via the respective components of the Scenegraph, shown in a separate GUI. All components with a TRS component can be altered via this GUI, as long as *ONLY ONE* TRS component is toggled at a time.
  * [Example C2](./C.Intermediate/example_C2_textures.py) A scene with a textured cube. The camera can be altered via the mouse or the GUI. A read-only GUI shows the Scenegraph.
  * [Example C3](./C.Intermediate/example_C3_more_textures.py) The same textured-cube scene as above, but with the vertex shader written inline as a Python string (`vertex_source=`) instead of loaded from a file, and a different texture image.
  * [Example C4](./C.Intermediate/example_C4_textures_with_lights.py) A scene with a textured cube and lights. The camera can be altered via the mouse or the main GUI. The Scenegraph allows manipulation of one TRS component at a time (not the camera's though); set `want_to_rotate = False` in the code to stop the cube spinning and manipulate it via the GUI instead.
  * [Example C5](./C.Intermediate/example_C5_cube_mapping.py) A scene with textured cube and a cubemap texture. The camera can be altered via the mouse or the main GUI.  

## D.Advanced examples

Advanced examples for USD scenes, obj-importer and more.

  * [Example D1](./D.Advanced/example_D1_universal_importer_advanced_lighting.py) A scene with a complex model 
  imported. Demonstrates the ability to load complex `.obj` files.
  * [Example D2](./D.Advanced/example_D2_usd_scene.py) A scene with a GUI that allows to import a [USD](https://openusd.org/release/index.html) file. Upon loading the demo usd, three cubes shall appear.
  * [Example D3](./D.Advanced/example_D3_proper_resize.py) A window that is properly resized, resetting the 
  projection matrix, on each frame, based on the window aspect. 
  * [Example D4](./D.Advanced/example_D4_ecs_behavior.py) An example demonstrating how behavior can be embedded. Using the InsertAction or RemoveAction, we may check if a component got close or far away respectively from another designated component. In this example, if you translate the RemoveCube away from the terrain, you will complete the RemoveAction. To complete the InsertAction, you may translate the InsertCube close to the terrain.

## E.Extended examples

A larger, ungraded collection of self-contained demos and extension showcases, contributed over time. Unlike the numbered folders above these aren't meant to be followed in order.

  * [example_basic_shapes.py](./E.Extended/example_basic_shapes.py): A torus, cylinder, cube and sphere spawned as ready-made ECS entities via the `BasicShapes` module, stacked and lit with Blinn-Phong shading.
  * [example_beautification_screenshot.py](./E.Extended/example_beautification_screenshot.py): A cube, terrain and axes scene demonstrating GUI-driven camera movement alongside a read-only Scenegraph view.
  * [example_bezier.py](./E.Extended/example_bezier.py): An interactive Bezier curve over a terrain, with an ImGUI panel to add, remove and edit control nodes live.
  * [example_billboard_labels_scene.py](./E.Extended/example_billboard_labels_scene.py): A cube, terrain and axes scene with billboard labels that always face the camera.
  * [example_billboard_labels_shapes.py](./E.Extended/example_billboard_labels_shapes.py): Billboard labels attached to three shapes (two cubes and a sphere) while the camera auto-orbits.
  * [example_bsp.py](./E.Extended/example_bsp.py): Builds a Binary Space Partitioning tree over a set of triangles; the GUI lets you search a triangle ID and print the traversal path/tree structure to the terminal.
  * [example_cameraman.py](./E.Extended/example_cameraman.py): A virtual cameraman flies around a textured Earth sphere, following either a draggable Bezier curve or a circular orbit.
  * [example_cow.py](./E.Extended/example_cow.py): The Newell cow model with a GUI toggle between smooth/flat shading and a normals-as-color debug view.
  * [example_dummy_rotate.py](./E.Extended/example_dummy_rotate.py): A cube continuously rotated by a dedicated rotation component/system.
  * [example_environment_mapping_cow.py](./E.Extended/example_environment_mapping_cow.py): The cow model reflecting a cubemap skybox via environment mapping.
  * [example_environment_mapping_pigs.py](./E.Extended/example_environment_mapping_pigs.py): Three tinted pig models (Gold/Chrome/Blue) reflecting a cubemap skybox while floating and rotating.
  * [example_function_animation.py](./E.Extended/example_function_animation.py): A `RealFunction3D` surface animated in real time by feeding a time parameter into its expression.
  * [example_function_graph.py](./E.Extended/example_function_graph.py): A `RealFunction3D` surface plotting f(x, y); type a new expression in the GUI to regenerate it live.
  * [example_geometry_factory.py](./E.Extended/example_geometry_factory.py): The same stacked-shapes scene as `example_basic_shapes.py`, rebuilt on the newer `geometry_factory` module's raw mesh arrays instead of ready-made entities.
  * [example_gizmos.py](./E.Extended/example_gizmos.py): A teapot-on-table scene with translate/rotate/scale gizmos (T/R/S, TAB to switch object, 0 to reset).
  * [example_glfw.py](./E.Extended/example_glfw.py): The same textured-and-lit cube scene as `example_C4_textures_with_lights.py`, running on the GLFW backend instead of SDL2.
  * [example_gravity_collision_bb.py](./E.Extended/example_gravity_collision_bb.py): Gravity and axis-aligned-bounding-box collision between falling cubes and the floor; cubes stack once they land.
  * [example_marching.py](./E.Extended/example_marching.py): A `MarchingCubes` implicit surface generated from a user-editable f(x, y, z) expression.
  * [example_multi_lights_3cubes_flat.py](./E.Extended/example_multi_lights_3cubes_flat.py): Three cubes (per-vertex colored, solid color, textured) lit by multiple dynamically managed lights, with flat normal shading.
  * [example_multi_lights_3cubes_smooth.py](./E.Extended/example_multi_lights_3cubes_smooth.py): The same three-cube, multi-light scene as above, with smooth normal shading.
  * [example_multi_lights_spheres.py](./E.Extended/example_multi_lights_spheres.py): Two spheres, one flat- and one smooth-shaded, lit by multiple dynamically managed lights.
  * [example_normals_map_flat.py](./E.Extended/example_normals_map_flat.py): Tangent-space normal mapping on a UV-mapped cube with flat (non-averaged) per-face normals.
  * [example_normals_map_smooth.py](./E.Extended/example_normals_map_smooth.py): Tangent-space normal mapping on a UV-mapped cube with smooth (averaged) normals.
  * [example_object_picker.py](./E.Extended/example_object_picker.py): A teapot-on-table scene; click to select an object, then manipulate it with gizmos (T/R/S/D).
  * [example_object_picker_cubes.py](./E.Extended/example_object_picker_cubes.py): The same object-picker/gizmo interaction, over a field of randomly placed cubes.
  * [example_picking_buffer.py](./E.Extended/example_picking_buffer.py): A cube-and-terrain scene testing the picking-buffer System; clicked entity info prints to the console.
  * [example_picking_multiple_colorful.py](./E.Extended/example_picking_multiple_colorful.py): A picking demo with 10 cubes using colorful per-vertex shading.
  * [example_picking_multiple_cubes.py](./E.Extended/example_picking_multiple_cubes.py): A picking demo with 10 cubes of alternating sizes and unique colors.
  * [example_picking_shadows.py](./E.Extended/example_picking_shadows.py): A picking demo with cubes, spheres, cylinders, a cone and a textured cube, lit by a shadow-casting point light.
  * [example_picking_tutorial.py](./E.Extended/example_picking_tutorial.py): A tutorial picking demo: click any object to print its name/id and orbit the camera around it.
  * [example_plane_fitting.py](./E.Extended/example_plane_fitting.py): Fits a best-fit plane to an editable set of 3D control points via the "Fit Plane" GUI panel.
  * [example_plotting.py](./E.Extended/example_plotting.py): Plot a function in 2D or 3D from the GUI.
  * [example_sphere.py](./E.Extended/example_sphere.py): A procedurally generated, Earth-textured sphere demonstrating smooth/flat per-vertex normals and a normals-as-color debug view.
  * [example_subtitles.py](./E.Extended/example_subtitles.py): A cube with a billboard label that always faces the camera.
  * [example_usd_import.py](./E.Extended/example_usd_import.py): Import and save USD scenes via GUI buttons; the default USD file loads three yellow cubes.
  * [example_voronoi.py](./E.Extended/example_voronoi.py): Demonstrates the Voronoi diagram of a set of 2D points.

## Mouse Controls <a name="mouse-controls"></a>

If camera movement is enabled then you can change the camera settings as follows:

  * Right mouse button changes the camera position.
  * Ctrl + Right mouse button zooms in and out.
  * Shift + Right mouse button changes the target location.