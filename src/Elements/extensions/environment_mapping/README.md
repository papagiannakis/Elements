
## Description

This extension implements environment mapping with reflection effects, allowing 3D objects to appear as reflective materials. The implementation uses cube maps to store the surrounding environment and calculates reflected view directions to create realistic mirror-like visual effects in real-time.
### Features

- **Reflection-based environment mapping**: Objects reflect the surrounding environment using standard reflection calculations
- **Optional colours**: color tints to simulate colored mirrors
- **Cube map support**: Works with custom cube maps loaded from image files
- **Skybox rendering**: Automatic skybox rendering that matches the environment map

- Paraskevi Mourelatou
- csd5149@csd.uoc.gr


### Running the Examples
The extension includes two example scripts one with the basics and one more advanced :

#### 1. Cow Model - Basic Example

python examples/4.Extended/example_environment_mapping_cow.py

This example demonstrates environment mapping on a cow model with:
- A skybox environment from the images directory
- A reflective cow model with slight blue tinting
- A ground plane showing the bottom face of the skybox


#### 2. Three Pigs Example

python examples/4.Extended/example_environment_mapping_pigs.py

This example demonstrates environment mapping on three pig models with different material properties:
- **Pig_Gold**: Gold-tinted reflective surface
- **Pig_Chrome**: Perfect mirror reflection
- **Pig_Blue**: Blue-tinted reflective surface

Note: The pigs example includes animated rotation and floating effects.

### Basic Usage

To apply environment mapping to your own entities:

# Load skybox images
skybox_images = {
    'front': 'path/to/front.png',
    'back': 'path/to/back.png',
    'top': 'path/to/top.png',
    'bottom': 'path/to/bottom.png',
    'left': 'path/to/left.png',
    'right': 'path/to/right.png',
}

# Create cubemap
face_data = get_texture_faces(**skybox_images)
cubemap = Texture3D(face_data)

# Apply environment mapping to an entity
shader = EnvironmentMapping.apply(entity, scene, cubemap=cubemap,  tint_color=(1.0, 1.0, 1.0),  # RGB tint color (white = no tint),tint_strength=0.0  # 0.0 = no tint, 1.0 = full tint)

# Update shader uniforms each frame

## Limitations
1. **Pigs Skybox Issue**: The skybox in example_environment_mapping_pigs.py does not work properly. The skybox may not render correctly.


## Optional Enhancements
### Future Improvements
- Fix the skybox rendering issue in the pigs example
- Support for varying reflectivity
- Roughness/glossiness parameters for non-perfect mirrors

