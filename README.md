# Welcome to project Elements!

[![Documentation](https://readthedocs.org/projects/elementsproject/badge/)](http://ElementsProject.readthedocs.io/en/latest/)
[![Project's GitHub Page](https://github.com/papagiannakis/Elements/actions/workflows/pages/pages-build-deployment/badge.svg?branch=github_page)](https://papagiannakis.github.io/Elements)
[![arXiv](https://img.shields.io/badge/arXiv-2302.07691-b31b1b.svg)](https://arxiv.org/abs/2302.07691)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)



https://user-images.githubusercontent.com/13041399/229489757-f0f3d208-a26d-4fa2-8891-f4d1c7f3aa27.mp4




## Overview
 
Elements introduces for the first time the power of the Entity-Component-System (ECS) with the versatility of Scenegraphs, in the context of Computer Graphics (CG), Deep Learning (DL) for Scientific Visualization (SciViz). It also aims to provide the basic tools to anyone that wants to be involved with basic Computer Graphics as well as advanced topics such as Geometric Deep Learning, Geometric Algebra and many many more.

Following a modern educational approach, all related packages are in the Python programming language.

To dive in the details of the project check [its detailed developer documentation](https://elementsproject.readthedocs.io/en/latest/index.html) and the research paper behind this project: [arXiv LINK](https://arxiv.org/abs/2302.07691), [Eurographics LINK](https://diglib.eg.org/handle/10.2312/eged20231015).

## Packages Involved in Elements

* pyECSS: A package for applying ECS to any Scenegraph
* pyGLV : A package applying ECSS to CG, DL and SciViz problems
* pyEEL : A learning hub for various topics where ECSS can be applied



## Getting Started - Installation Instructions

Begin by following the installation instructions, found [HERE](https://elementsproject.readthedocs.io/en/latest/source/getting_started/installation.html). For **Computer Graphics Course students**, the instructions are [HERE](https://github.com/papagiannakis/Elements/wiki/Installation-Instructions-for-Computer-Graphics-Course-students).

> [!NOTE]
> We strongly recommend using:
> * [Anaconda](https://www.anaconda.com/products/individual) for your python environment, 
> * [Visual Studio Code](https://code.visualstudio.com) as your IDE, and
> * [Fork](https://git-fork.com)/[Sourcetree](https://www.sourcetreeapp.com) for version control.

The main steps summarize as follows:
* Install Anaconda, VSCode, Git and a optionally a version control app
* Clone (or download) this repo (or your forked repo)
* Create a python 3.9 (recommended) environment, by running 
  ```conda create -n elements python=3.9```,
  and activate it via
  ```conda activate elements```
* Install the Elements in editable mode by running
 ```pip install -e .```
  This is sufficient to run all examples in the repository.
* To install all optional extras as well, run
 ```pip install -e ."[all]"```
* Start exploring the examples in the ```Elements/examples``` folder.

## Known Issues

* **`imgui_bundle` (optional, `extras`/`all`) fails to build on macOS**: `pip install imgui_bundle`
  may try to build it from source and fail with a CMake error inside its vendored `freetype`
  dependency (`Compatibility with CMake < 3.5 has been removed from CMake`). This happens when pip
  can't find a prebuilt wheel matching your exact platform tag and falls back to a source build,
  which then hits a modern CMake (4.x) refusing to process `freetype`'s older
  `cmake_minimum_required()` version pin.

  * **Quickest fix** -- skip the source build entirely and force pip to use a prebuilt wheel,
    bypassing macOS's `SYSTEM_VERSION_COMPAT` compatibility shim (which can otherwise make Python
    misreport your OS version to pip and rule out a wheel that would actually match):

    ```bash
    SYSTEM_VERSION_COMPAT=0 pip install --only-binary=:all: imgui_bundle
    ```

    Note this may resolve to an older `imgui_bundle` release than the latest on GitHub/PyPI, if
    that's the newest version with a prebuilt wheel for your platform/Python combination.

  * **To get the latest version** (building from source): allow CMake to process the old version
    pin instead of erroring out on it, and skip pip's local cache so it re-resolves the latest
    release rather than reusing a previously-downloaded older sdist:

    ```bash
    CMAKE_POLICY_VERSION_MINIMUM=3.5 pip install --no-cache-dir --upgrade imgui_bundle
    ```

    This compiles Dear ImGui + hello_imgui + freetype + backends from C++ source, so expect it to
    take several minutes rather than seconds.

## Folder Structure

* [docs](./docs): Files used to generate the [documentation](https://elementsproject.readthedocs.io/en/latest/index.html)
The project follows a standard Python project layout with source code in `src/` and examples/tutorials at the top level.

```text
Elements/
├── src/
│   └── Elements/                  # Core package
│       ├── extensions/            # Modules extending basic functionality
│       │   ├── BasicShapes/       # Helper functions for basic 3D shapes
│       │   ├── GA/                # Geometric Algebra implementation
│       │   ├── Gizmos/            # Unity-like Gizmos for object manipulation
│       │   ├── SkinnedMesh/       # Skinned mesh visualization systems
│       │   ├── Slicing/           # Tools for slicing 3D objects
│       │   ├── Voronoi2D/         # Voronoi diagram visualization
│       │   ├── bezier/            # 3D Bezier curve visualization
│       │   ├── plane_fitting/     # Plane fitting visualization
│       │   ├── plotting/          # 2D/3D function plotting utilities
│       │   ├── rigid_body_animation/ # Skinned mesh animation (preliminary)
│       │   └── usd/               # USD format support (loading/saving)
│       ├── files/                 # Static assets and resources
│       │   ├── models/            # 3D models (static and rigged)
│       │   ├── scenes/            # Pre-built USD scenes
│       │   ├── scv/               # Scientific Visualization data
│       │   ├── shaders/           # GLSL shader programs
│       │   └── textures/          # Image textures
│       ├── pyECSS/                # Core Entity-Component-System-Scenegraph framework
│       │   └── tests/             # Unit tests for pyECSS
│       ├── pyGLV/                 # Graphics Library for Visualization (Rendering, GUI)
│       │   ├── GL/                # Low-level OpenGL wrappers
│       │   ├── GUI/               # Window management and GUI initialization
│       │   └── tests/             # Unit tests for pyGLV
│       └── utils/                 # General utility functions
├── examples/                      # Standalone example scripts
│   ├── A.Showcase/                # A single combined demo tying several techniques together
│   ├── B.Introductory/            # Basic examples for beginners
│   ├── C.Intermediate/            # Intermediate concepts (textures, cameras)
│   ├── D.Advanced/                # Advanced topics (USD, complex scenes)
│   └── E.Extended/                # Ungraded, self-contained demos and extension showcases
├── pyEEL/                         # Python Elements Educational Library (Learning Hub)
│   └── notebooks/                 # Jupyter notebooks
│       ├── CG/                    # Computer Graphics fundamentals
│       ├── DL/                    # Deep Learning fundamentals
│       ├── GATE/                  # Geometric Algebra Transformation Engine
│       ├── SciCom/                # Scientific Computation
│       └── neuralCG/              # Neural Networks in Computer Graphics
├── tests/                         # (Optional) Top-level tests
├── setup.py                       # Build and installation configuration
└── README.md                      # Project overview and instructions
```
  
## Testing in VS Code

For the current `src/` project layout, the most reliable way to configure test discovery in Visual Studio Code is:

1. Open `Python: Configure Tests`
2. Select `unittest`
3. Select the workspace folder `Elements`
4. Use the pattern `test*.py`

If you prefer storing the working configuration in [`.vscode/settings.json`](/Users/manos/github/Elements/.vscode/settings.json), the following setup matches the current repository layout:

```json
{
  "python.testing.pytestEnabled": false,
  "python.testing.unittestEnabled": true,
  "python.testing.cwd": "${workspaceFolder}/src",
  "python.testing.unittestArgs": [
    "-v",
    "-s",
    ".",
    "-p",
    "test*.py"
  ]
}
```

The equivalent command-line discovery command from the repository root is:

```bash
python -m unittest discover -s src -t src -p "test*.py"
```

This makes `unittest` discover tests from the `src/Elements/...` tree correctly. If tests are discovered in the terminal but not in the VS Code Testing tab, first confirm that VS Code is using the same Python interpreter/environment as your terminal.

## Contribute to Elements</h2>
If you want to contribute to Elements, kindly check its [WIKI](https://github.com/papagiannakis/Elements/wiki) 
for a list of potential projects and a contribution guide. A list of contributors can be found [here](https://github.com/papagiannakis/Elements/wiki/Contributors).

## Contact Us

If you have any questions or would like to learn more about our project, please don't hesitate to [contact us](mailto:papagian@ics.forth.gr).


## Citation

If you are using the Elements project, please cite:

```
@inproceedings {Elements2023,
booktitle = {Eurographics 2023 - Education Papers},
editor = {Magana, Alejandra and Zara, Jiri},
title = {{Project Elements: A Computational Entity-component-system in a Scene-graph Pythonic Framework, for a Neural, Geometric Computer Graphics Curriculum}},
author = {Papagiannakis, George and Kamarianakis, Manos and Protopsaltis, Antonis and Angelis, Dimitris and Zikas, Paul},
year = {2023},
publisher = {The Eurographics Association},
ISSN = {1017-4656},
ISBN = {978-3-03868-210-3},
DOI = {10.2312/eged.20231015}
}
```
