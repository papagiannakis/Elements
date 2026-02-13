# Camera-Man Project

**Author:** Giorgos Vitsos (csd5369)
**Email:** csd5369@csd.uoc.gr

This project implements a dynamic, interactive camera system within a 3D environment using the **pyECSS** (Entity-Component-System) and **pyGLV** (OpenGL Wrapper) frameworks. It features a textured 3D Earth model and allows users to switch between smooth **Bezier curve** paths and circular **Orbit** paths while maintaining focus on a specific target.

---

## Project Structure

The project is divided into two main Python files, separating the **Scene Graph construction** from the **Camera Control logic**.

### 1. `cameraman_example.py` (The Scene Builder)
This is the main entry point of the application. It is responsible for setting up the 3D world and the rendering pipeline.

* **Scene Graph Initialization:** Sets up the `pyECSS` Scene and creates the entity hierarchy (`Root` -> `Sphere`).
* **Procedural Geometry:** Manually generates the vertices, indices, and UV coordinates for a sphere using mathematical constants (pi, sin, cos).
* **Texture Management:** Loads the `earth.jpg` texture and binds it to the sphere's shader.
* **Render Loop:** Manages the main application loop. Crucially, it delegates camera control to the logic module by calling `cam.run_camera()` every frame, passing the sphere's Transform and Shader components for updates.

### 2. `cameraman_logic.py` (The Camera Controller)
This file acts as the "brain" of the camera. It handles user input, graphical user interface (GUI) rendering, and the mathematical calculations for camera movement.

* **GUI System (`imgui`):** Renders the interactive control panels:
    * **Welcome Screen:** Initial start overlay.
    * **Main Options:** Select modes (Bezier vs. Orbit), reset positions, and adjust global animation speed.
    * **Path Editors:** Specialized windows to add/remove Bezier control points or adjust Orbit diameter/point count.
* **Path Generation Algorithms:**
    * **Bezier Curves:** Uses **De Casteljau's algorithm** (recursive linear interpolation) to calculate smooth paths between arbitrary 3D control points.
    * **Orbital Paths:** Calculates a closed loop of points around a target using parametric circle equations (`x = r * cos(theta)`, `z = r * sin(theta)`).
* **Camera Math:**
    * **Interpolation:** Linearly interpolates between path points based on the time variable `t`.
    * **LookAt Matrix:** Continually recalculates the **View Matrix** using `util.lookat()`. This ensures that no matter where the camera moves, it always points directly at the `target` (default: `0,0,0`).
    * **Uniform Updates:** Directly updates the `model`, `View`, and `Proj` uniform matrices in the active shader.

---

## Features

* **Dual Path Modes:**
    * **Bezier:** Define a custom path by adding, removing, and dragging control points in 3D space.
    * **Orbit:** Automatically generate a circular path around a target with adjustable diameter and resolution.
* **Smooth Animation:** Time-based interpolation ensures fluid movement along paths.
* **Real-time Texture Mapping:** Renders a procedurally generated sphere with UV-mapped textures.
* **Hot-Reloading State:** Reset logic allows users to restart animations or snap the camera back to origin without restarting the app.

---

## Requirements

* **Python 3.8+**
* **Dependencies:**
    * `numpy` (Matrix/Vector math)
    * `imgui` (Immediate Mode GUI)
    * `Elements` (pyECSS & pyGLV framework)
* **Assets:**
    * `earth.jpg` must be present in your configured `TEXTURE_DIR`.

---

## Integration with Other Examples

This camera system is modular and can be easily imported into other pyECSS/pyGLV scenes.

### 1. Import the Module
Include the logic file at the top of your script:

```python
import cameraman_logic as cam
```

### 2. Configure the Camera (Optional)

Before entering your main loop, you can use the provided setter functions to customize the camera's behavior for your specific scene.

| Function                         | Description                                                        | Example 
| `cam.set_target([x, y, z])`      | Sets the point the camera will look at (the center of the screen). | `cam.set_target([0, 5, 0])` 
| `cam.set_cam_pos([x, y, z])`     | Sets the initial position of the camera before animation starts.   | `cam.set_cam_pos([10, 10, 10])` 
| `cam.set_up([x, y, z])`          | Defines the "Up" vector for the camera (usually Y-up).             | `cam.set_up([0, 1, 0])` 
| `cam.set_control_points([List])` | Defines the initial list of points for the Bezier curve.           | `cam.set_control_points([[0,0,0], [5,5,5]])` 

### 3. Implement in Render Loop

Inside your main `while running:` loop, call `run_camera`. You must pass the **Transform component** of the object you are viewing (used for the Model matrix) and the **Shader** (used to update View/Projection matrices).

```python
# Setup before loop
cam.set_target([0.0, 0.0, 0.0])   # Look at origin
cam.set_cam_pos([0.0, 0.0, 10.0]) # Start 10 units back

while running:
    running = scene.render()
    
    # Run logic and update shader uniforms
    cam.run_camera(my_object_transform, my_shader)
    
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()