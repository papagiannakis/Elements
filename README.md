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
* Create a python 3.8 environment, by running 
  ```conda create -n elements python=3.8```,
  and activate it via
  ```conda activate elements```
* Install the Elements in editable mode by running
 ```pip install -e .```
* Start exploring the examples in the ```Elements/examples``` folder.





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
│       │   ├── atlas_files/       # Resources for AI examples
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
│   ├── 1.Introductory/            # Basic examples for beginners
│   ├── 2.Intermediate/            # Intermediate concepts (textures, cameras)
│   ├── 3.Advanced/                # Advanced topics (USD, complex scenes)
│   └── 4.Experimental/            # Experimental features (AI, Generative)
├── pyEEL/                         # Python Elements Educational Library (Learning Hub)
│   └── notebooks/                 # Jupyter notebooks
│       ├── CG/                    # Computer Graphics fundamentals
│       ├── DL/                    # Deep Learning fundamentals
│       ├── GATE/                  # Geometric Algebra Transformation Engine
│       ├── SciCom/                # Scientific Computation
│       └── neuralCG/              # Neural Networks in Computer Graphics
├── docs/                          # Documentation source files
├── tests/                         # (Optional) Top-level tests
├── setup.py                       # Build and installation configuration
└── README.md                      # Project overview and instructions
```
  
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
