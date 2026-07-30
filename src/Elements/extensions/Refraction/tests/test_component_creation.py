"""
Test for entity creation and shader loading
"""
import numpy as np
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Elements.extensions.Refraction.refraction_component import create_refractive_entity, STANDARD_VERT_PATH, REFRACTION_FRAG
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import RenderMesh


def test_shader_files():

    """Check that shader files exist and have required content"""
    
    print("Checking shader files:\n")
    
    # Check vertex shader file
    if not STANDARD_VERT_PATH.exists():
        print(f" - ERROR: Standard.vert not found at {STANDARD_VERT_PATH}")
        return False
    
    with open(STANDARD_VERT_PATH, 'r') as f:
        vert_shader = f.read()
    
    if len(vert_shader) == 0:
        print("- ERROR: Standard.vert is empty")
        return False
    
    # Check for basic GLSL stuff
    if 'gl_Position' not in vert_shader:
        print("- ERROR: Standard.vert missing gl_Position")
        return False
    
    print("- Vertex shader status: OK")
    
    # Check fragment shader
    if len(REFRACTION_FRAG) == 0:
        print("- ERROR: REFRACTION_FRAG is empty")
        return False
    
    # Check for refraction stuff
    required = ['refract', 'cubemap', 'u_Ratio', 'camPos']
    for req in required:
        if req not in REFRACTION_FRAG:
            print(f"- ERROR: Fragment shader missing '{req}'")
            return False
    
    print("- Fragment shader status: OK")
    print("="*50)
    return True


def test_entity_creation():

    """Test whether entity and components are properley created or not"""
    
    print("\nTesting entity creation:\n")
    
    # Make a simple cube
    verts = np.array([
        [-0.5, -0.5,  0.5, 1.0], [-0.5,  0.5,  0.5, 1.0],
        [ 0.5,  0.5,  0.5, 1.0], [ 0.5, -0.5,  0.5, 1.0],
        [-0.5, -0.5, -0.5, 1.0], [-0.5,  0.5, -0.5, 1.0],
        [ 0.5,  0.5, -0.5, 1.0], [ 0.5, -0.5, -0.5, 1.0]
    ], dtype=np.float32)
    
    inds = np.array([
        0,1,2, 0,2,3, 4,5,6, 4,6,7,
        0,4,7, 0,7,3, 1,5,6, 1,6,2,
        0,1,5, 0,5,4, 3,2,6, 3,6,7
    ], dtype=np.uint32)
    
    scene = Scene()
    root = scene.world.createEntity(Entity(name="Root"))
    
    # Create entity
    ent, trans, shader = create_refractive_entity(scene, root, "Cube", verts, inds)
    
    if not ent:
        print("- ERROR: Entity is None")
        return False
    print("- Entity created")
    
    if not trans:
        print("- ERROR: Transform is None")
        return False
    print("- Transform component status: OK")
    
    if not shader:
        print("- ERROR: Shader is None")
        return False
    print("- Shader component status: OK")
    
    # Check that transform has the right matrix (should be identity)
    if not hasattr(trans, 'l2world'):
        print("- ERROR: Transform missing l2world matrix")
        return False
    print("- Transform has l2world matrix")
    
    # Verify entity is in scene
    if ent not in scene.world._entities:
        print("- ERROR: Entity not in scene world")
        return False
    print("- Entity registered in scene")
    
    print("- All components created successfully")
    return True


if __name__ == "__main__":
    print("="*50)
    print("- Component Creation and Shader Test")
    print("="*50)
    
    try:
        test1 = test_shader_files()
        test2 = test_entity_creation()
        
        if test1 and test2:
            print("\n" + "="*50)
            print("All tests PASSED!")
            print("="*50)
            sys.exit(0)
        else:
            print("\n" + "="*50)
            print("Some tests FAILED!")
            print("="*50)
            sys.exit(1)
            
    except Exception as e:
        print(f"\nTests FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)