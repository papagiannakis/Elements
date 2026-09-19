import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent

MODEL_DIR = ROOT_DIR / "assets" / "models"
TEXTURE_DIR = ROOT_DIR / "assets" / "textures"
SCENES_DIR = ROOT_DIR / "assets" / "scenes"
SCV_DIR = ROOT_DIR / "assets" / "scv" 
PICKLES_DIR = ROOT_DIR / "assets" / "pickles"
SHADER_DIR = ROOT_DIR / "assets" / "shaders"
#: Cube-map skyboxes: one folder of six face images per set (Cloudy, Sea, Stars, ...).
SKYBOX_DIR = ROOT_DIR / "assets" / "skyboxes"