def text_to_ir(text):
    lines = text.strip().splitlines()
    ir = {"window": {}, "objects": []}
    for line in lines:
        line = line.strip()
        if line.startswith("window"):
            parts = line.split()
            if len(parts) != 3:
                raise ValueError("Window definition must be in the format: 'window width height'")
            ir["window"]["width"] = int(parts[1])
            ir["window"]["height"] = int(parts[2])
        elif line.startswith("object"):
            parts = line.split()
            if len(parts) < 3:
                raise ValueError("Object definition must be in the format: 'object type name [position] [scale] [color]'")
            obj_type = parts[1]
            name = parts[2]
            position = [0, 0, 0]
            scale = [1, 1, 1]
            color = [1, 1, 1]
            for part in parts[3:]:
                if part.startswith("position="):
                    position = list(map(float, part[len("position="):].split(",")))
                elif part.startswith("scale="):
                    scale = list(map(float, part[len("scale="):].split(",")))
                elif part.startswith("color="):
                    color = list(map(float, part[len("color="):].split(",")))
                else:
                    raise ValueError(f"Unknown object property: {part}")
            ir["objects"].append({
                "type": obj_type,
                "name": name,
                "position": position,
                "scale": scale,
                "color": color
            })
        else:
            raise ValueError(f"Unknown line type: {line}")
    return ir
