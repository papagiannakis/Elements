# Camera-Man Project

**Author:** Giorgos Vitsos (csd5369)
**Email:** csd5369@csd.uoc.gr

This project implements a dynamic camera system within a 3D environment using the Elements **pyECSS** and **pyGLV** framework. It allows users to define camera paths via Bezier curves or circular orbits to visualize a textured 3D sphere (Earth).

---

## Features

* Smooth camera animation along **Bezier curves** or **orbit paths**.
* Real-time 3D rendering of a sphere with **texture mapping**.
* Interactive GUI to:

  * Start, reset, and select camera paths.
  * Adjust camera position and animation speed.
  * Add, remove, and modify Bezier curve control points.
  * Customize orbit diameter and number of points.

---

## Requirements

* Python 3.8+
* Dependencies:

  * `numpy`
  * `imgui` (PyImGui)
  * `pyGLV` (Graphics and GUI library)
  * `pyECSS` (Entity-Component-System framework)
  * OpenGL (version 4+)
* Texture file: `earth.jpg` in the `TEXTURE_DIR` directory.

---


## Usage

Run the main Python script:

```bash
python cameraman.py
```

### Controls via GUI:

* **Start:** Begins camera animation along the selected path.
* **Reset:** Resets camera position and animation variables.
* **Bezier / Orbit:** Choose camera path type.
* **Animation Speed:** Adjust speed of camera motion.
* **Bezier Path GUI:** Add or remove control points and modify their positions.
* **Orbit GUI:** Set diameter and number of orbit points.

