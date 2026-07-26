# Object selection via second Frame Buffer
- Author: Boultadakis Themis - 4470

## 1. Implementation Description
__PickingSystem__ uses a secondary _Frame Buffer Object_ (fbo, PickingBuffer) that contains the ids of all objects converted to RGB values using bit shifting

### PickingSystem class:
---
1. __FUNCTIONS__: 
    - __init__ : 
        Initialize all fields (variables)
    - init : 
        Apply PickingShader (PICKING_VERT, PICKING_FRAG) to all entities in the scene and initialize FBO
    - _init_fbo:<a id="fbo_handling"></a> 
        Initialize FBO
    - resize : 
        Setter for (window) width and height that updates FBO textures
    - set_camera_matrices : 
        Setter for projMat and view
    - begin_picking_pass : 
        Reset PickingSystem fields and FBO parameters to prepare for next travesal
    - end_picking_pass :
        Rebind main FBO
    - apply2VertexArray :
        Applies PickingShader to all objects assigning them their respective color
    - pick :
        Gets Entity at clicked coordinates
    - check_for_click:
        Check for click and return coordinates or None
    - cleanup :
        Deletes PickingSystem fields (helper func for __del__)
    - __del__ :
        Deletes PickingSystem instance
        
2. __FIELDS__:
    - width : window width
    - height : window height
    - _shader : PickingShader instance
    - shader_dec : Actual Shader
    - fbo : Frame Buffer Object instance (PickingBuffer)
    - tex_color : Texture attachment to FBO that keeps color to id relations
    - rbo_depth :  z-buffer for PickingSystem
    - _next_id : iterator value
    - id_to_entity : Dictionary to match ids to entities
    - entity_to_id : Dictionary for the other way around
    - projMat : Projection matrix 
    - view : View matrix
    - _mouse_state : buffer for last mouse state
---

### Some design choices
---
1. Implemented as a System: Applicable to any program with a scene
2. PickingShader:
    - PICKING_VERT : Only transforms vertices from object space to clip space 
    - PICKING_FRAG : Fragment shader that applies the id to rgb logic:

    ```python
        # Encode ID to normalized RGB
        r = ((obj_id) & 0xFF) / 255.0
        g = ((obj_id >> 8) & 0xFF) / 255.0
        b = ((obj_id >> 16) & 0xFF) / 255.0
    ```  
3. The PickingSystem handles its own FBO at all times, it only expects signals from the main program at the appropriate times
4. Monitors SDL_MouseState to get clicks when changes take place (holds history in _mouse_state field of PickingSystem class)
---

## 2. Basic use outline:

```python

# Create and add to world
pickingSystem = pb.PickingSystem(1024, 720)
scene.world.createSystem(pickingSystem)

# After scene.init()! (window must exist for _init_fbo!)
pickingSystem.set_camera_matrices(projMat, view)
picking.init()

# Inside Main Loop:
click_coords = pickingSystem.check_for_click()
if click_coords:
    mouse_x = click_coords[0]
    mouse_y = click_coords[1]

    pickingSystem.set_camera_matrices(projMat, view) # Update camera matrices !
    
    pickingSystem.begin_picking_pass()   
    scene.world.traverse_visit(pickingSystem, scene.world.root)  
    pickingSystem.end_picking_pass()

    entity, picked_id = pickingSystem.pick(mouse_x, mouse_y, height) # Picking

    print("\nPicked id: ", picked_id, entity,"\n")

```
---

## 3. Included files
1. __init__.py (dont know, saw it in other extension folders and added it)
2. Example_PickingBuffer.py : Sample scene with a cude and a floor(terrain) with the PickingSystem applied
3. PickingBuffer.py : Includes the PickingSystem(System) class (__source code__)
4. test_PickingBuffer.py : AI generated unit tests for each function of the implementation

> ___PS___: AI use made for [FBO handling](#fbo_handling), corner cases and unit test generation!