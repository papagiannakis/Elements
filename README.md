# Welcome to project Elements!

[![Documentation](https://readthedocs.org/projects/elementsproject/badge/)](http://ElementsProject.readthedocs.io/en/latest/)
[![Project's GitHub Page](https://github.com/papagiannakis/Elements/actions/workflows/pages/pages-build-deployment/badge.svg?branch=github_page)](https://papagiannakis.github.io/Elements)
[![arXiv](https://img.shields.io/badge/arXiv-2302.07691-b31b1b.svg)](https://arxiv.org/abs/2302.07691)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

<iframe width="560" height="315" src="https://www.youtube.com/embed/XZ7sW3hxzRA" title="The Elements Project" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

For a more detailed developer documentation please refer [here](https://elementsproject.readthedocs.io/en/latest/index.html). The research paper behind this project can be found [here](https://arxiv.org/abs/2302.07691)

## Overview
 
Elements introduces for the first time the power of the Entity-Component-System (ECS) with the versatility of Scenegraphs, in the context of Computer Graphics (CG), Deep Learning (DL) for Scientific Visualization (SciViz). It also aims to provide the basic tools to anyone that wants to be involved with basic Computer Graphics as well as advanced topics such as Geometric Deep Learning, Geometric Algebra and many many more.

Following a modern educational approach, all related packages are in the Python programming language.

## Packages Involved in Elements

* pyECSS: A package for applying ECS to any Scenegraph
* pyGLV : A package applying ECSS to CG, DL and SciViz problems
* pyEEL : A learning hub for various topics where ECSS can be applied



## Quick Start

Download (or clone) this repo (or your fork) and, in a python 3.8 environment, run ```pip install -e .```

Go to the ```Elements/pyGLV/examples``` folder and quickstart by using/modifying one of the existing examples.

## Folder Structure

* [docs](./docs): Files used to generate the [documentation](https://elementsproject.readthedocs.io/en/latest/index.html)
* [Elements](./Elements/): Contains all the source code of Elements
  * [pyECSS](./Elements/pyECSS): Contains all the source code for pyECSS - Entity, Component, System, Scenegraph functionality
    * [examples](./Elements/pyECSS): Example files related to pyECSS
    * [GA](./Elements/pyECSS/GA): Files related to Geometric Algebra(GA) and GA-based components-systems
    * [tests](./Elements/pyECSS/tests): Test files for pyECSS
  * [pyGLV](./Elements/pyGLV): Contains all the source code for pyGLV - graphics, shading, imgui functionality
    * [examples](./Elements/pyGLV): Example files related to pyGLV
    * [tests](./Elements/pyGLV/tests): Test files for pyGLV
    * [GL](./Elements/pyGLV/GL): The basic Graphics Library files (Scene, Shader, Texture, VertexArray)
    * [GUI](./Elements/pyGLV/GUI): Files related to the window and GUI instantiation.
    * [utils](./Elements/pyGLV/utils): Utility files and functions for pyGLV.
  * [pyEEL](./Elements/pyEEL): The pyEEL learning hub
    * [examples](./Elements/pyEEL/examples): Contains all the jupyter notebooks of pyEEL  
      * [SciCom](./Elements/pyEEL/examples/SciCom): Scientific Computation related notebooks
      * [neuralCG](./Elements/pyEEL/examples/neuralCG): Neural networks in CG related notebooks
      * [DL](./Elements/pyEEL/examples/DL): Deep Learning related notebooks
      * [CG](./Elements/pyEEL/examples/CG): Computer Graphics (CG) related notebooks
      * [GATE](./Elements/pyEEL/examples/GATE): Geometric Algebra Transformation Engine related notebooks

## Contribute to Elements</h2>
If you want to contribute to Elements, kindly check its [WIKI](https://github.com/papagiannakis/Elements/wiki) 
for a list of potential projects and a contribution guide.

## Contact Us

If you have any questions or would like to learn more about our project, please don't hesitate to [contact us](mailto:papagian@ics.forth.gr).


## Citation

If you are using the Elements project, please cite:

```
@misc{projectElements,
  title = {Project Elements: A computational entity-component-system in a scene-graph pythonic framework, for a neural, geometric computer graphics curriculum},
  author = {Papagiannakis, George and Kamarianakis, Manos and Protopsaltis, Antonis and Angelis, Dimitris and Zikas, Paul},
  doi = {10.48550/ARXIV.2302.07691},
  url = {https://arxiv.org/abs/2302.07691},
  publisher = {arXiv},
  year = {2023}
}
```
