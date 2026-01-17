# Ray Tracing with Ambient Occlusion

## Description
This extension implements a GPU-based Ray Tracing algorithm focused on **Ambient Occlusion (AO)**. Instead of traditional point-light shading, it calculates contact shadows based on the proximity of spheres to each other and the floor plane, creating a high-contrast, soft-shadow effect.

## Contributors
* **Zisis Orfanidis** (csd4704@csd.uoc.gr)
* **Xristos Zaxarias** (csd4877@csd.uoc.gr)

## Usage instructions
1. Ensure you have `glfw`, `PyOpenGL`, and `numpy` installed.
2. Navigate to `Elements/extensions/ray_tracing/`.
3. Run the example using:
   ```bash
   python example.py
