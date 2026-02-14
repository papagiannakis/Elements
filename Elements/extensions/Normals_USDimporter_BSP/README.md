Authors:
    Almani Iosif - csd4824
    Kapetanakis Ioannis - csd4641

Tests are written for pytest
    -> To run all the tests, type: pytest Tests


<Proper Normals Task:>
Implemented correct flat/smooth normal handling by detecting shared vs unique vertex indexing and converting the vertex/index buffers accordingly. Helper utilities determine whether vertices are shared or unique by analyzing index usage. This fixes smooth-shading artifacts caused by incorrect vertex-sharing assumptions and ensures the appropriate flat or smooth shading path is selected.

Usage:
    python cow_example.py
    python sphere_example.py

Runtime options (ImGui):
    - Shading: Smooth / Flat
    - Normals as color: toggles normal-visualization by mapping normals to RGB

<USD Importer Task:>
The LoadScene_Blender method imports a USD scene exported from Blender and converts it into an Elements scene representation. It traverses the USD stage hierarchy, creates corresponding entities for each UsdGeom.Xform, and reconstructs parent–child relationships based on USD paths.

For each UsdGeom.Mesh, the method extracts geometry data including vertex positions, face topology, normals, and material color information. It supports both smooth and flat shading by handling different normal interpolation modes (vertex and faceVarying). Polygonal faces are triangulated appropriately, with corner-space triangulation used for flat shading.

The method uploads vertex attributes and indices to the GPU and performs coordinate system conversion from Blender’s Z-up convention to the engine’s Y-up convention.

Usage:
    python usd_import_example.py

Runtime options (ImGui):
    - Load USD (colors)
    - Load USD (normals as color)

<BSP Task:>
The implemented method builds an axis-aligned Binary Space Partitioning (BSP) tree for triangle meshes.

Each triangle is implicitly assigned an ID based on its position in the index buffer (every 3 consecutive indices correspond to one triangle). The search(id) function references triangles using this index-based ID.

At each node, the splitting axis is selected based on the largest spatial extent of the triangles, while the split position is chosen as the median of triangle centroids along that axis to avoid unbalanced partitions.

Triangles are classified as fully on one side of the split plane or intersecting it; intersecting triangles are propagated to all child leaf nodes to preserve spatial correctness.

During search, the BSP tree is traversed by testing each triangle against the split planes. The traversal path and tree structure are printed to the terminal.

Usage:
    python bsp_example.py

    What to try:
    - Move the camera to view triangle placement.
    - Use Triangle id = 0..4 and press Search to observe different traversal paths.
    - Press Print tree to inspect the BSP structure by depth.

    In each case, the result is printed to the terminal.


Runtime options (ImGui):
    - Triangle id (input)
    - Search (prints traversal path to the terminal)
    - Print tree (prints the BSP structure by depth to the terminal)