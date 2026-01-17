# test_geometry.py - Simple tests for geometry functions
import numpy as np

# Copy the functions here for testing
def generateElegantFloor(size=4, center_color=[0.8, 0.8, 0.8, 1.0], edge_color=[0.2, 0.2, 0.2, 1.0]):
    points = [
        [-size, 0.0, -size], 
        [size,  0.0, -size],
        [size,  0.0, size],  
        [-size, 0.0, size]  
    ]
    indices = [0, 1, 2, 0, 2, 3]
    colorT = [edge_color, edge_color, center_color, center_color]
    return np.array(points, dtype=np.float32), np.array(indices, dtype=np.uint32), np.array(colorT, dtype=np.float32)


def generateSkybox(size=50.0):
    points = [
        [-size, size, -size], [size, size, -size], [size, size, size], [-size, size, size],   
        [-size, -size, -size], [size, -size, -size], [size, -size, size], [-size, -size, size]  
    ]
    sky_color = [0.0, 0.5, 1.0, 1.0]   
    horizon_color = [0.8, 0.8, 0.9, 1.0] 
    colors = [sky_color, sky_color, sky_color, sky_color, horizon_color, horizon_color, horizon_color, horizon_color]
    indices = [0, 1, 2, 0, 2, 3, 4, 6, 5, 4, 7, 6, 0, 3, 7, 0, 7, 4, 1, 5, 6, 1, 6, 2, 3, 2, 6, 3, 6, 7, 0, 4, 5, 0, 5, 1]
    return np.array(points, dtype=np.float32), np.array(indices, dtype=np.uint32), np.array(colors, dtype=np.float32)


def generateGrid(size=4, N=20, color=[0.2, 0.2, 0.2, 1.0]):
    points = []
    indices = []
    colors = []
    step = (2.0 * size) / N
    current_pos = -size
    idx = 0
    
    for i in range(N + 1):
        points.append([current_pos, 0.0, -size]) 
        points.append([current_pos, 0.0, size])  
        points.append([-size, 0.0, current_pos]) 
        points.append([size, 0.0, current_pos])  
        indices.append(idx)
        indices.append(idx + 1)
        indices.append(idx + 2)
        indices.append(idx + 3)
        colors.extend([color, color, color, color])
        idx += 4
        current_pos += step
        
    return np.array(points, dtype=np.float32), np.array(indices, dtype=np.uint32), np.array(colors, dtype=np.float32)


print("=" * 60)
print("Test gia ta geometry functions")
print("=" * 60)


# =====================================================================
# TEST 1: generateElegantFloor
# =====================================================================

print("\nTEST 1: Elegant Floor")
print("-" * 60)

# Kalo tin function
vertices, indices, colors = generateElegantFloor(size=5.0)

print("Ftiaxno ena floor me megethos 5.0")

# Tsekaro ta shapes
print(f"Vertices: {vertices.shape} - prepei na einai (4, 3)")
print(f"Indices: {indices.shape} - prepei na einai (6,)")
print(f"Colors: {colors.shape} - prepei na einai (4, 4)")

# Tsekaro an ola einai sto y=0
all_on_ground = np.allclose(vertices[:, 1], 0.0)

# Tsekaro an ta vertices einai sta swsta shmeia
correct_positions = (
    np.allclose(vertices[0], [-5.0, 0.0, -5.0]) and
    np.allclose(vertices[1], [5.0, 0.0, -5.0]) and
    np.allclose(vertices[2], [5.0, 0.0, 5.0]) and
    np.allclose(vertices[3], [-5.0, 0.0, 5.0])
)

# Apotelesma
test1_pass = (vertices.shape == (4, 3) and 
              indices.shape == (6,) and 
              colors.shape == (4, 4) and
              all_on_ground and
              correct_positions)

if test1_pass:
    print("\nPASS - To floor ftiachtike swsta")
    print("  - 4 vertices sta swsta shmeia")
    print("  - 6 indices gia 2 trigwna")
    print("  - Ola ta vertices sto y=0")
else:
    print("\nFAIL - Kati pige lathos")
    if not all_on_ground:
        print("  - Ta vertices den einai ola sto y=0")
    if not correct_positions:
        print("  - Ta vertices den einai sta swsta shmeia")


# =====================================================================
# TEST 2: generateSkybox
# =====================================================================

print("\n\nTEST 2: Skybox")
print("-" * 60)

# Kalo tin function me default size
sky_v, sky_i, sky_c = generateSkybox()

print("Ftiaxno skybox me default megethos (50.0)")

# Tsekaro ta shapes
print(f"Vertices: {sky_v.shape} - prepei na einai (8, 3)")
print(f"Indices: {sky_i.shape} - prepei na einai (36,)")
print(f"Colors: {sky_c.shape} - prepei na einai (8, 4)")

# Tsekaro an oi panw korifes exoun sky color
sky_color_correct = (
    np.allclose(sky_c[0], [0.0, 0.5, 1.0, 1.0]) and
    np.allclose(sky_c[1], [0.0, 0.5, 1.0, 1.0]) and
    np.allclose(sky_c[2], [0.0, 0.5, 1.0, 1.0]) and
    np.allclose(sky_c[3], [0.0, 0.5, 1.0, 1.0])
)

# Tsekaro an oi katw korifes exoun horizon color
horizon_color_correct = (
    np.allclose(sky_c[4], [0.8, 0.8, 0.9, 1.0]) and
    np.allclose(sky_c[5], [0.8, 0.8, 0.9, 1.0]) and
    np.allclose(sky_c[6], [0.8, 0.8, 0.9, 1.0]) and
    np.allclose(sky_c[7], [0.8, 0.8, 0.9, 1.0])
)

# Apotelesma
test2_pass = (sky_v.shape == (8, 3) and 
              sky_i.shape == (36,) and 
              sky_c.shape == (8, 4) and
              sky_color_correct and
              horizon_color_correct)

if test2_pass:
    print("\nPASS - To skybox ftiachtike swsta")
    print("  - 8 vertices gia ton kuvo")
    print("  - 36 indices gia 12 trigwna (6 faces * 2)")
    print("  - Swsta xrwmata: ble panw, gkri katw")
else:
    print("\nFAIL - Kati pige lathos")
    if not sky_color_correct:
        print("  - Ta panw xrwmata den einai swsta")
    if not horizon_color_correct:
        print("  - Ta katw xrwmata den einai swsta")


# =====================================================================
# TEST 3: generateGrid
# =====================================================================

print("\n\nTEST 3: Grid")
print("-" * 60)

# Kalo tin function me N=10 gia na einai pio aplo
grid_v, grid_i, grid_c = generateGrid(size=4, N=10)

print("Ftiaxno grid me size=4 kai N=10 grammes")

# Ypologizw posa vertices prepei na exw
# Gia N=10, exw 11 grammes (0 ews 10)
# Kathe grammi exei 2 vertices kai ftiaxnw kai orizontia kai katheti
# Ara: (N+1) * 4 vertices = 11 * 4 = 44
expected_vertices = (10 + 1) * 4

print(f"Vertices: {grid_v.shape[0]} - prepei na einai {expected_vertices}")
print(f"Indices: {grid_i.shape[0]} - prepei na einai {expected_vertices}")

# Tsekaro an ola einai sto y=0
all_on_ground = np.allclose(grid_v[:, 1], 0.0)

# Tsekaro an ola ta vertices einai mesa sta oria
within_bounds = (
    np.all(grid_v[:, 0] >= -4.0) and np.all(grid_v[:, 0] <= 4.0) and
    np.all(grid_v[:, 2] >= -4.0) and np.all(grid_v[:, 2] <= 4.0)
)

# Apotelesma
test3_pass = (grid_v.shape[0] == expected_vertices and 
              grid_i.shape[0] == expected_vertices and
              all_on_ground and
              within_bounds)

if test3_pass:
    print("\nPASS - To grid ftiachtike swsta")
    print(f"  - {expected_vertices} vertices gia 11 grammes")
    print("  - Ola ta vertices sto y=0")
    print("  - Ola ta vertices mesa sta oria -4 ews +4")
else:
    print("\nFAIL - Kati pige lathos")
    if grid_v.shape[0] != expected_vertices:
        print(f"  - Lathos arithmos vertices: {grid_v.shape[0]} anti gia {expected_vertices}")
    if not all_on_ground:
        print("  - Ta vertices den einai ola sto y=0")
    if not within_bounds:
        print("  - Kapoio vertex einai ektos oriwn")


# =====================================================================
# TELIKA APOTELESMATA
# =====================================================================

print("\n" + "=" * 60)
print("APOTELESMATA")
print("=" * 60)

# Metrima posa tests perase
tests = [
    ("Elegant Floor", test1_pass),
    ("Skybox", test2_pass),
    ("Grid", test3_pass)
]

passed = sum(1 for _, p in tests if p)

print(f"\n{passed}/3 tests perase\n")

for name, result in tests:
    status = "PASS" if result else "FAIL"
    print(f"  {status} - {name}")

print("\n" + "=" * 60)

if passed == 3:
    print("OLA SWSTA - Ta geometry functions douleuoun kala")
else:
    print(f"PROSOXH - {3-passed} test(s) apetuxe")

print("=" * 60)