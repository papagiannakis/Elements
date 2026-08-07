import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent

MODEL_DIR = ROOT_DIR / "files" / "models"
TEXTURE_DIR = ROOT_DIR / "files" / "textures"
SCENES_DIR = ROOT_DIR / "files" / "scenes"
SCV_DIR = ROOT_DIR / "files" / "scv" 
PICKLES_DIR = ROOT_DIR / "files" / "pickles"
SHADER_DIR = ROOT_DIR / "files" / "shaders"
#: Cube-map skyboxes: one folder of six face images per set (Cloudy, Sea, Stars, ...).
SKYBOX_DIR = TEXTURE_DIR / "Skyboxes"