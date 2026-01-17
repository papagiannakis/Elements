import os
import sys
import math
import numpy as np
import glfw
import importlib.util
from OpenGL.GL import *

# Load the algorithm module from Elements/extensions/Elements/extensions/example.py
current_dir = os.path.dirname(os.path.abspath(__file__))
algorithm_path = os.path.join(current_dir, "algorithm.py")

#Manual module loading
spec = importlib.util.spec_from_file_location("algorithm", algorithm_path)
algorithm = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(algorithm)
    create_raytracing_program = algorithm.create_raytracing_program
except Exception as e:
    print(f"Σφάλμα κατά τη φόρτωση του algorithm.py: {e}")
    sys.exit(1)


def generate_pyramid_data():
    """Δημιουργεί τα δεδομένα για τις σφαίρες της πυραμίδας και το έδαφος."""
    sphere_data = []
    colors = []
    layers, radius = 5, 1.0
    spacing = radius * 2.0
    height_step = spacing * 0.816
    base_y_center = -3.0

    for layer in range(layers):
        layer_size = layers - layer 
        y = layer * height_step + base_y_center
        for row in range(layer_size):
            for col in range(layer_size):
                x = (row * spacing) - (layer_size * spacing / 2) + (spacing / 2)
                z = (col * spacing) - (layer_size * spacing / 2) + (spacing / 2)
                sphere_data.extend([x, y, z, radius])
                colors.extend([0.8, 0.1, 0.1])  # Κόκκινο χρώμα
    
    # Προσθήκη εδάφους (μια τεράστια σφαίρα πολύ μακριά)
    sphere_data.extend([0.0, base_y_center - radius - 5000.0, 0.0, 5000.0])
    colors.extend([0.4, 0.4, 0.4])  # Γκρι χρώμα εδάφους
    
    return np.array(sphere_data, dtype=np.float32), np.array(colors, dtype=np.float32), (len(colors)//3)

def main():
    # Αρχικοποίηση GLFW
    if not glfw.init():
        return

    # Ρυθμίσεις για Linux/Wayland compatibility
    os.environ["WAYLAND_DISPLAY"] = "" 
    os.environ["XDG_SESSION_TYPE"] = "x11"

    width, height = 1280, 720
    window = glfw.create_window(width, height, "Ray Tracing Extension - Ambient Occlusion", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)
    glfw.swap_interval(1)

    # Δημιουργία του Shader Program από το algorithm.py
    try:
        shader = create_raytracing_program()
        glUseProgram(shader)
    except Exception as e:
        print(f"Shader Error: {e}")
        glfw.terminate()
        return

    # Προετοιμασία δεδομένων
    s_data, c_data, count = generate_pyramid_data()
    
    # Full-screen quad (ορθογώνιο που καλύπτει όλη την οθόνη)
    vertices = np.array([
        -1.0, -1.0, 
         1.0, -1.0, 
        -1.0,  1.0, 
        -1.0,  1.0, 
         1.0, -1.0, 
         1.0,  1.0
    ], dtype=np.float32)
    
    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

    # Uniform Locations
    loc_res = glGetUniformLocation(shader, "resolution")
    loc_cam = glGetUniformLocation(shader, "camPos")
    loc_dir = glGetUniformLocation(shader, "camDir")
    loc_spheres = glGetUniformLocation(shader, "spheres")
    loc_colors = glGetUniformLocation(shader, "sphereColors")
    loc_count = glGetUniformLocation(shader, "sphereCount")

    # Ανέβασμα στατικών δεδομένων στην GPU
    glUniform4fv(loc_spheres, count, s_data)
    glUniform3fv(loc_colors, count, c_data)
    glUniform1i(loc_count, count)

    cam_target = np.array([0.0, -3.0, 0.0], dtype=np.float32)

    print("Rendering started. Close the window to exit.")

    while not glfw.window_should_close(window):
        t = glfw.get_time()
        
        # Ενημέρωση διαστάσεων παραθύρου
        w, h = glfw.get_framebuffer_size(window)
        glViewport(0, 0, w, h)
        glUniform2f(loc_res, float(w), float(h))

        # Animation Κάμερας
        cp = [math.sin(t * 0.3) * 15.0, 5.0, math.cos(t * 0.3) * 15.0]
        direction = cam_target - np.array(cp)
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction /= norm
        
        glUniform3f(loc_cam, cp[0], cp[1], cp[2])
        glUniform3f(loc_dir, direction[0], direction[1], direction[2])

        # Σχεδίαση
        glClear(GL_COLOR_BUFFER_BIT)
        glBindVertexArray(vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()
