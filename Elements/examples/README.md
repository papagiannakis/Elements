# Examples

Below you may find the description of the examples provided in this folder. In most examples with a rendered scene, 
you may move the camera using the mouse. Check [Mouse Controls](#mouse-controls) for more information.

## 1.Introductory examples

These examples are suitable for introduction to Computer Graphics and Elements.

  * [Example 0](./1.Introductory/example_0_ComponentSystem.py): A plain example of a component and a system, without any rendering
  * [Example 1](./1.Introductory/example_1_empty_window.py): A plain empty window rendered. Demonstrates the basic setup of a window and a renderer.
  * [Example 2](./1.Introductory/example_2_empty_window_with_GUI.py): A plain empty window rendered with GUI enabled. You may change the background color via the GUI and check the FPS, as well as information on the openGL version and the renderer.
  * [Example 3](./1.Introductory/example_3_cube_lookAt.py): A scene containing a cube. The camera is staticly defined within the code and the `lookAt` is used to create the projection matrix. 
  * [Example 4](./1.Introductory/example_4_cube_axes_terrain.py): A scene containing a cube, and a terrain. 
  The camera can be altered via the GUI or the mouse. The ECSS graph is also shown in a separate GUI (read-only).
  * [Example 5](./1.Introductory/example_5_lights_cube.py): A scene containing a cube, terrain, axes. Lights via 
  the Blinn-Phong algorithm. Camera can be altered via the GUI or the mouse. The ECSS graph is also shown in a separate GUI. 
  If *a single* TRS component (except the camera) is toggled in the ECSS graph, you may alter the TRS via the Translation/Rotation/Scale properties on top.
  * [Example 6](./1.Introductory/example_6_import_objects.py): A scene with a teapot. Camera can be altered via the GUI or the mouse. The example demonstrated the import of objects from `.obj` files.
  
## 2.Intermediate examples

Intermediate examples of textures (2D and Cubemaps), lights, and complete ECS.

  * [Example 7](./2.Intermediate/example_7_cameraSystem.py): A scene using the camera system. The camera can be altered via the mouse or via the respective components of the ECSS graph, shown in a separate GUI. All components with a TRS component can be altered via this GUI, as long as *ONLY ONE* TRS component is toggled at a time.
  * [Example 8](./2.Intermediate/example_8_textures.py) A scene with a textured cube. The camera can be altered via the mouse or the GUI. A read-only GUI shows the ECSS graph.
  * [Example 9](./2.Intermediate/example_9_textures_with_lights.py) A scene with a textured cube and lights. The camera can be altered via the mouse or the main GUI. The ECSS graph allows manipulation of one TRS component at a time (not the camera's though); if line 230 is commented out instead of line 232, manipulating the cube via the GUI will also be enabled.
  * [Example 10](./2.Intermediate/example_10_cube_mapping.py) A scene with textured cube and a cubemap texture. The camera can be altered via the mouse or the main GUI.  

## 3.Advanced examples

Advanced examples for USD scenes, obj-importer and more.

  * [Example 11](./3.Advanced/example_11_universal_importer_advanced_lighting.py) A scene with a complex model 
  imported. Demonstrates the ability to load complex `.obj` files.
  * [Example 12](./3.Advanced/example_12_usd_scene.py) A scene with a GUI that allows to import a [USD](https://openusd.org/release/index.html) file. Upon loading the demo usd, three cubes shall appear.
  * [Example 13](./3.Advanced/example_13_proper_resize.py) A window that is properly resized, resetting the 
  projection matrix, on each frame, based on the window aspect. 
  * [Example 14](./3.Advanced/example_14_ECS_behavior.py) An example demonstrating how behavior can be embedded. Using the InsertAction or RemoveAction, we may check if a component got close or far away respectively from another designated component. In this example, if you translate the RemoveCube away from the terrain, you will complete the RemoveAction. To complete the InsertAction, you may translate the InsertCube close to the terrain.


## 4.Experimental examples

Cutting-edge examples demonstrating advanced functionality.

Note that some of the Experimental examples may require the installation of additional packages, especially the ones
involving Machine/Deep learning (e.g. PyTorch, PyTorch Geometric, etc.). The following commands may be used to install them

```
pip install matplotlib torch
pip install pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv torch_geometric  --find-links https://data.pyg.org/whl/torch-1.12.0+cpu.html
```

Some examples require a CUDA enabled Windows machine to run them. 


## Mouse Controls <a name="mouse-controls"></a>

If camera movement is enabled then you can change the camera settings as follows:

  * Right mouse button changes the camera position.
  * Ctrl + Right mouse button zooms in and out.
  * Shift + Right mouse button changes the target location.