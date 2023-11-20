from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))

# imports from __version__
with open(path.join(this_directory, 'Elements', '_version.py'), encoding='utf-8') as f:
    exec(f.read())

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Elements',
    version=__version__, 
    license='Apache 2', 
    description = "The Elements project",
    long_description=long_description,
    # long_description= file: README.md, LICENSE.txt
    long_description_content_type='text/markdown',
    author = "George Papagiannakis", 
    author_email = "papagian@csd.uoc.gr",
    maintainer='Manos Kamarianakis',
    maintainer_email='m.kamarianakis@gmail.com',
    url='https://github.com/papagiannakis/Elements',
    keywords = ['ECS','Scenegraph','Python design patterns','Computer Graphics'],
    package_dir={'Elements':'Elements'},
    packages=find_packages(exclude=["tests","tests.*", "tests/*", "pyEEL/*" ]),
    install_requires=[
        'pip',
        'setuptools>=61',
        'wheel',
        'numpy',
        'scipy',
        'imgui',
        'PyOpenGL',
        'pillow',
        'PyOpenGL_accelerate',
        'pysdl2',
        'pysdl2-dll',
        'ipykernel',
        'usd-core',
        'jupyter',
        'scikit-spatial',
        'bezier',
        'clifford',
        'trimesh',
        'pyganja',
        'open3d',
        'pyassimp==4.1.3',
        'meshplot'
    ],
    

    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Environment :: MacOS X",
        "Environment :: Win32 (MS Windows)",
        "Environment :: X11 Applications",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    project_urls={
        "Homepage" : "https://papagiannakis.github.io/Elements",
        "Source" : "https://github.com/papagiannakis/Elements",
        "Documentation" : "https://ElementsProject.readthedocs.io",
    },

    python_requires=">=3.8,<3.10",

)