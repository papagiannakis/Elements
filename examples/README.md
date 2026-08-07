# Examples

Below you may find the description of the examples provided in this folder. In most examples with a rendered scene, 
you may move the camera using the mouse. Check [Mouse Controls](#mouse-controls) for more information.

## 0.Showcase examples

A single combined demo that ties several techniques together.

  * [example_showcase.py](./0.Showcase/example_showcase.py): An extended version of the picking tutorial (click-to-orbit, lights, projection, shadows) with four extra swappable panels: an OBJ model gallery (Teapot/Cow/Teddy with smooth/flat shading), a cubemap skybox, a refractive "glass" object, and a reflective "mirror" object.

## 1.Introductory examples

These examples are suitable for introduction to Computer Graphics and Elements.

  * [Example 0](./1.Introductory/example_0_component_system.py): A plain example of a component and a system, without any rendering
  * [Example 1](./1.Introductory/example_1_empty_window.py): A plain empty window rendered. Demonstrates the basic setup of a window and a renderer.
  * [Example 2](./1.Introductory/example_2_empty_window_with_GUI.py): A plain empty window rendered with GUI enabled. You may change the background color via the GUI and check the FPS, as well as information on the openGL version and the renderer.
  * [Example 3](./1.Introductory/example_3_cube_lookat.py): A scene containing a cube. The camera is staticly defined within the code and the `lookAt` is used to create the projection matrix. 
  * [Example 4](./1.Introductory/example_4_cube_axes_terrain.py): A scene containing a cube, and a terrain. 
  The camera can be altered via the GUI or the mouse. The Scenegraph is also shown in a separate GUI (read-only).
  * [Example 5](./1.Introductory/example_5_lights_cube.py): A scene containing a cube, terrain, axes. Lights via 
  the Blinn-Phong algorithm. Camera can be altered via the GUI or the mouse. The Scenegraph is also shown in a separate GUI. 
  If *a single* TRS component (except the camera) is toggled in the Scenegraph, you may alter the TRS via the Translation/Rotation/Scale properties on top.
  * [Example 6](./1.Introductory/example_6_import_objects.py): A scene with a teapot. Camera can be altered via the GUI or the mouse. The example demonstrated the import of objects from `.obj` files.
  
## 2.Intermediate examples

Intermediate examples of textures (2D and Cubemaps), lights, and complete ECS.

  * [Example 7](./2.Intermediate/example_7_camera_system.py): A scene using the camera system. The camera can be altered via the mouse or via the respective components of the Scenegraph, shown in a separate GUI. All components with a TRS component can be altered via this GUI, as long as *ONLY ONE* TRS component is toggled at a time.
  * [Example 8](./2.Intermediate/example_8_textures.py) A scene with a textured cube. The camera can be altered via the mouse or the GUI. A read-only GUI shows the Scenegraph.
  * [Example 9](./2.Intermediate/example_9_textures_with_lights.py) A scene with a textured cube and lights. The camera can be altered via the mouse or the main GUI. The Scenegraph allows manipulation of one TRS component at a time (not the camera's though); if line 230 is commented out instead of line 232, manipulating the cube via the GUI will also be enabled.
  * [Example 10](./2.Intermediate/example_10_cube_mapping.py) A scene with textured cube and a cubemap texture. The camera can be altered via the mouse or the main GUI.  

## 3.Advanced examples

Advanced examples for USD scenes, obj-importer and more.

  * [Example 11](./3.Advanced/example_11_universal_importer_advanced_lighting.py) A scene with a complex model 
  imported. Demonstrates the ability to load complex `.obj` files.
  * [Example 12](./3.Advanced/example_12_usd_scene.py) A scene with a GUI that allows to import a [USD](https://openusd.org/release/index.html) file. Upon loading the demo usd, three cubes shall appear.
  * [Example 13](./3.Advanced/example_13_proper_resize.py) A window that is properly resized, resetting the 
  projection matrix, on each frame, based on the window aspect. 
  * [Example 14](./3.Advanced/example_14_ecs_behavior.py) An example demonstrating how behavior can be embedded. Using the InsertAction or RemoveAction, we may check if a component got close or far away respectively from another designated component. In this example, if you translate the RemoveCube away from the terrain, you will complete the RemoveAction. To complete the InsertAction, you may translate the InsertCube close to the terrain.

## 4.Extended examples

A larger, ungraded collection of self-contained demos and extension showcases, contributed over time. Unlike the numbered folders above these aren't meant to be followed in order.

  * [example_basic_shapes.py](./4.Extended/example_basic_shapes.py): A torus, cylinder, cube and sphere spawned as ready-made ECS entities via the `BasicShapes` module, stacked and lit with Blinn-Phong shading.
  * [example_beautification_screenshot.py](./4.Extended/example_beautification_screenshot.py): A cube, terrain and axes scene demonstrating GUI-driven camera movement alongside a read-only Scenegraph view.
  * [example_bezier.py](./4.Extended/example_bezier.py): An interactive Bezier curve over a terrain, with an ImGUI panel to add, remove and edit control nodes live.
  * [example_billboard_labels_scene.py](./4.Extended/example_billboard_labels_scene.py): A cube, terrain and axes scene with billboard labels that always face the camera.
  * [example_billboard_labels_shapes.py](./4.Extended/example_billboard_labels_shapes.py): Billboard labels attached to three shapes (two cubes and a sphere) while the camera auto-orbits.
  * [example_bsp.py](./4.Extended/example_bsp.py): Builds a Binary Space Partitioning tree over a set of triangles; the GUI lets you search a triangle ID and print the traversal path/tree structure to the terminal.
  * [example_cameraman.py](./4.Extended/example_cameraman.py): A virtual cameraman flies around a textured Earth sphere, following either a draggable Bezier curve or a circular orbit.
  * [example_cow.py](./4.Extended/example_cow.py): The Newell cow model with a GUI toggle between smooth/flat shading and a normals-as-color debug view.
  * [example_dummy_rotate.py](./4.Extended/example_dummy_rotate.py): A cube continuously rotated by a dedicated rotation component/system.
  * [example_environment_mapping_cow.py](./4.Extended/example_environment_mapping_cow.py): The cow model reflecting a cubemap skybox via environment mapping.
  * [example_environment_mapping_pigs.py](./4.Extended/example_environment_mapping_pigs.py): Three tinted pig models (Gold/Chrome/Blue) reflecting a cubemap skybox while floating and rotating.
  * [example_function_animation.py](./4.Extended/example_function_animation.py): A `RealFunction3D` surface animated in real time by feeding a time parameter into its expression.
  * [example_function_graph.py](./4.Extended/example_function_graph.py): A `RealFunction3D` surface plotting f(x, y); type a new expression in the GUI to regenerate it live.
  * [example_geometry_factory.py](./4.Extended/example_geometry_factory.py): The same stacked-shapes scene as `example_basic_shapes.py`, rebuilt on the newer `geometry_factory` module's raw mesh arrays instead of ready-made entities.
  * [example_gizmos.py](./4.Extended/example_gizmos.py): A teapot-on-table scene with translate/rotate/scale gizmos (T/R/S, TAB to switch object, 0 to reset).
  * [example_gravity_collision_bb.py](./4.Extended/example_gravity_collision_bb.py): Gravity and axis-aligned-bounding-box collision between falling cubes and the floor; cubes stack once they land.
  * [example_marching.py](./4.Extended/example_marching.py): A `MarchingCubes` implicit surface generated from a user-editable f(x, y, z) expression.
  * [example_multi_lights_3cubes_flat.py](./4.Extended/example_multi_lights_3cubes_flat.py): Three cubes (per-vertex colored, solid color, textured) lit by multiple dynamically managed lights, with flat normal shading.
  * [example_multi_lights_3cubes_smooth.py](./4.Extended/example_multi_lights_3cubes_smooth.py): The same three-cube, multi-light scene as above, with smooth normal shading.
  * [example_multi_lights_spheres.py](./4.Extended/example_multi_lights_spheres.py): Two spheres, one flat- and one smooth-shaded, lit by multiple dynamically managed lights.
  * [example_normals_map_flat.py](./4.Extended/example_normals_map_flat.py): Tangent-space normal mapping on a UV-mapped cube with flat (non-averaged) per-face normals.
  * [example_normals_map_smooth.py](./4.Extended/example_normals_map_smooth.py): Tangent-space normal mapping on a UV-mapped cube with smooth (averaged) normals.
  * [example_object_picker.py](./4.Extended/example_object_picker.py): A teapot-on-table scene; click to select an object, then manipulate it with gizmos (T/R/S/D).
  * [example_object_picker_cubes.py](./4.Extended/example_object_picker_cubes.py): The same object-picker/gizmo interaction, over a field of randomly placed cubes.
  * [example_picking_buffer.py](./4.Extended/example_picking_buffer.py): A cube-and-terrain scene testing the picking-buffer System; clicked entity info prints to the console.
  * [example_picking_multiple_colorful.py](./4.Extended/example_picking_multiple_colorful.py): A picking demo with 10 cubes using colorful per-vertex shading.
  * [example_picking_multiple_cubes.py](./4.Extended/example_picking_multiple_cubes.py): A picking demo with 10 cubes of alternating sizes and unique colors.
  * [example_picking_shadows.py](./4.Extended/example_picking_shadows.py): A picking demo with cubes, spheres, cylinders, a cone and a textured cube, lit by a shadow-casting point light.
  * [example_picking_tutorial.py](./4.Extended/example_picking_tutorial.py): A tutorial picking demo: click any object to print its name/id and orbit the camera around it.
  * [example_plane_fitting.py](./4.Extended/example_plane_fitting.py): Fits a best-fit plane to an editable set of 3D control points via the "Fit Plane" GUI panel.
  * [example_plotting.py](./4.Extended/example_plotting.py): Plot a function in 2D or 3D from the GUI.
  * [example_sphere.py](./4.Extended/example_sphere.py): A procedurally generated, Earth-textured sphere demonstrating smooth/flat per-vertex normals and a normals-as-color debug view.
  * [example_subtitles.py](./4.Extended/example_subtitles.py): A cube with a billboard label that always faces the camera.
  * [example_usd_import.py](./4.Extended/example_usd_import.py): Import and save USD scenes via GUI buttons; the default USD file loads three yellow cubes.
  * [example_voronoi.py](./4.Extended/example_voronoi.py): Demonstrates the Voronoi diagram of a set of 2D points.

## Mouse Controls <a name="mouse-controls"></a>

If camera movement is enabled then you can change the camera settings as follows:

  * Right mouse button changes the camera position.
  * Ctrl + Right mouse button zooms in and out.
  * Shift + Right mouse button changes the target location.