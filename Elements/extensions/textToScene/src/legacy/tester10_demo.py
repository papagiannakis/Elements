import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from code_generator import generate_scene_script, save_script


def material(color):
    return {
        "color": color,
        "texture": {
            "enabled": False,
            "path": None
        }
    }


def mesh(name, shape, position, scale, color):
    return {
        "node_type": "mesh_object",
        "name": name,
        "shape": shape,
        "transform": {
            "position": position,
            "scale": scale
        },
        "material": material(color)
    }


scene_ir = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1200,
        "height": 800,
        "title": "Sunny Grass Scene Demo"
    },
    "children": [
        {
            "node_type": "light",
            "name": "sun_light",
            "light_type": "point",
            "properties": {
                "position": [2.8, 4.2, 1.5],
                "color": [1.0, 0.95, 0.75],
                "intensity": 2.2
            }
        },

        mesh(
            "grass_ground",
            "plane",
            [0.0, 0.0, 0.0],
            [10.0, 1.0, 10.0],
            [0.18, 0.85, 0.22]
        ),

        mesh(
            "sun_visible_sphere",
            "sphere",
            [2.8, 4.2, 1.5],
            [0.8, 0.8, 0.8],
            [1.0, 0.9, 0.05]
        ),

        {
            "node_type": "group",
            "name": "cherry_tree",
            "transform": {
                "position": [-1.7, 0.0, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            "children": [
                mesh(
                    "tree_trunk",
                    "cylinder",
                    [0.0, 0.75, 0.0],
                    [0.35, 1.5, 0.35],
                    [0.55, 0.28, 0.08]
                ),

                mesh(
                    "tree_leaves",
                    "sphere",
                    [0.0, 1.9, 0.0],
                    [1.65, 1.45, 1.65],
                    [0.05, 0.62, 0.12]
                ),

                # Bigger cherries, moved toward the front/right so the camera can see them.
                mesh(
                    "cherry_1",
                    "sphere",
                    [-0.5, 2.05, 0.8],
                    [0.28, 0.28, 0.28],
                    [1.0, 0.02, 0.02]
                ),
                mesh(
                    "cherry_2",
                    "sphere",
                    [0.35, 2.2, 0.75],
                    [0.28, 0.28, 0.28],
                    [1.0, 0.02, 0.02]
                ),
                mesh(
                    "cherry_3",
                    "sphere",
                    [0.05, 1.72, 0.95],
                    [0.26, 0.26, 0.26],
                    [1.0, 0.02, 0.02]
                ),
                mesh(
                    "cherry_4",
                    "sphere",
                    [-0.15, 2.35, 0.45],
                    [0.26, 0.26, 0.26],
                    [1.0, 0.02, 0.02]
                ),
                mesh(
                    "cherry_5",
                    "sphere",
                    [0.65, 1.9, 0.25],
                    [0.25, 0.25, 0.25],
                    [1.0, 0.02, 0.02]
                )
            ]
        },

        mesh(
            "ball_on_ground",
            "sphere",
            [1.6, 0.35, 0.9],
            [0.7, 0.7, 0.7],
            [0.08, 0.25, 1.0]
        )
    ]
}


script = generate_scene_script(scene_ir)
compile(script, "scene_out.py", "exec")
print("Syntax OK")
save_script(script, scene_ir=scene_ir)
print("Saved sunny scene demo successfully")

