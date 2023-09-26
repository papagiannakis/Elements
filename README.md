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

Begin by following the installation instructions, found [HERE](https://elementsproject.readthedocs.io/en/latest/source/getting_started/installation.html). For **Computer Graphics Course students**, the instructions are [HERE](https://github.com/papagiannakis/Elements/wiki/Installation-Instructions-for-HY358-Students).

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
* [Elements](./Elements/): Contains all the source code of Elements
  * [examples](./Elements/examples): Example files related to pyECSS
  * [features](./Elements/features): Features extending basic functionality of Elements
    * [BasicShapes](./Elements/features/BasicShapes): Quickly add basic shapes (cubes, spheres, cones) to the scene with helper functions
    * [GA](./Elements/features/GA): Files related to Geometric Algebra(GA) and GA-based components-systems
    * [Gizmos](./Elements/features/Gizmos): Introducing Unity-like Gizmos to the Elements, for object manipulation
    * [SkinnedMesh](./Elements/features/SkinnedMesh): Visualize skinned meshes by applying the animation equation
    * [Slicing](./Elements/features/Slicing): Visualize sliced version of a 3D object
    * [Voronoi2D](./Elements/features/Voronoi2D): Visualize the Voronoi diagram of 2D points
    * [bezier](./Elements/features/bezier): Visualize a 3D bezier curve
    * [plane_fitting](./Elements/features/plane_fitting): Visualize the plane that best fits on a set of points
    * [plotting](./Elements/features/plotting): Plot a 2D or 3D function
    * [rigid_body_animation](./Elements/features/rigid_body_animation): Animate a skinned mesh (preliminary version)
    * [usd](./Elements/features/usd): Enable loading/saving using Pixar's Universal Scene Descriptor (USD) format
  * [files](./Elements/files): Static files required
    * [atlas_files](./Elements/files/atlas_files): Required for the Classification and Generative AI examples/notebooks
    * [models](./Elements/files/models): Various 3D models, static or rigged
    * [scenes](./Elements/files/scenes): Scenes in USD format
    * [scv](./Elements/files/scv): Various SCV files
    * [shaders](./Elements/files/shaders): Various shader files
    * [textures](./Elements/files/textures): Various texture files
  * [pyECSS](./Elements/pyECSS): Contains all the source code for pyECSS - Entity, Component, System, Scenegraph functionality
    * [tests](./Elements/pyECSS/tests): Test files for pyECSS
  * [pyGLV](./Elements/pyGLV): Contains all the source code for pyGLV - graphics, shading, imgui functionality
    * [tests](./Elements/pyGLV/tests): Test files for pyGLV
    * [GL](./Elements/pyGLV/GL): The basic Graphics Library files (Scene, Shader, Texture, VertexArray)
    * [GUI](./Elements/pyGLV/GUI): Files related to the window and GUI instantiation.
  * [pyEEL](./Elements/pyEEL): The pyEEL learning hub
    * [notebooks](./Elements/pyEEL/notebooks): Contains all the jupyter notebooks of pyEEL  
      * [SciCom](./Elements/pyEEL/notebooks/SciCom): Scientific Computation related notebooks
      * [neuralCG](./Elements/pyEEL/notebooks/neuralCG): Neural networks in CG related notebooks
      * [DL](./Elements/pyEEL/notebooks/DL): Deep Learning related notebooks
      * [CG](./Elements/pyEEL/notebooks/CG): Computer Graphics (CG) related notebooks
      * [GATE](./Elements/pyEEL/notebooks/GATE): Geometric Algebra Transformation Engine related notebooks
  * [utils](./Elements/utils): Utility files and functions for Elements
  
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
