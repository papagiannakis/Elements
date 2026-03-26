
from Elements.extensions.textToScene.src.text_parser import text_to_ir
from Elements.extensions.textToScene.src.code_generator import generate_scene
from Elements.extensions.textToScene.src.script_saver import save_script

text = input("Describe the scene: ")

ir = text_to_ir(text)

code = generate_scene(ir)

save_script(code)