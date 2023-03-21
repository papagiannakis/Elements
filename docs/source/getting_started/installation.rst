Installation
============

The pyECSS can be installed via the standard mechanisms for Python packages, and is available through PyPI for standalone use, 
or Github, for development. We strongly propose to **install and use** pyECSS within a new environment created via ``conda``.


Creating a Conda Environment
------------------------------
After downloading the proper 
`Anaconda python distribution <https://www.anaconda.com/distribution/#download-section>`_, 
based on your system, you may create a virtual environment via the ``conda`` command.

Typically, you may create a new envirnment via the command::

    conda create -n myenv python==3.8

This creates a new environment, named myenv, with a python version 3.8, which is the proper version to run pyECSS.

You may now activate the environment by running::

    conda activate myenv

When finished, you may deactivate it by running::

    conda deactivate



Stable Version - Standalone Use
--------------------------------
For standalone use, you may install pyECSS, via ``pip3`` ::

    pip3 install pyECSS

.. note ::

    The version installed via pip3 may be a few versions behind the current version in development. 
    If you need to test the latest version, you should install it via ``git`` and local install.

Latest Version - Standalone Use
----------------------------------

If you want the latest (development) version of ``pyECSS`` you can locally pip install it from the latest develop branch with::

    pip3 install git+https://github.com/papagiannakis/pyECSS.git

Latest Version - For development
-----------------------------------

If you want to run and modify ``pyECSS``, you should use an editable (``-e``) installation::

    git clone https://github.com/papagiannakis/pyECSS.git
    pip3 install -e ./pyECSS


Contributing to ``pyECSS``
-----------------------------------

In order to contribute to contribute to the ``pyECSS`` package: 

1. Fork the `develop branch <https://github.com/papagiannakis/pyECSS.git>`_.
2. Clone your forked repo to your computer.
3. Install it in editable mode by running::

    pip3 install -e .

  at the directory where the `setup.py` file is located. 
4. Create a feature branch from the develop branch, and work on it. 
5. Push your feature branch to your github repo. 
6. Open a Pull Request to the `original develop branch <https://github.com/papagiannakis/pyECSS.git>`_.

