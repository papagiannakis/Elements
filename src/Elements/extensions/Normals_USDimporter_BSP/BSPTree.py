import numpy as np

class BSPNode:
    """
    Node of a Binary Space Partitioning (BSP) tree.
    """

    def __init__(self, axis=None, value=None):
        self.left = None
        self.right = None
        self.axis = axis
        self.value = value
        self.triangles = None  # np.ndarray of triangle ids stored in leaves

    def isLeaf(self):
        """
        Check whether this node is a leaf.
        """
        return self.left is None and self.right is None


class BSPTree:
    """
    Binary Space Partitioning (BSP) tree for triangle meshes.
    """

    def __init__(self, vertices: np.ndarray, indices: np.ndarray, max_depth: int = 18):
        self.vertices = vertices.astype(np.float32)
        self.indices = indices
        self.max_depth = max_depth
        self.root = None
        self.triangle_ids = None

    def build(self):
        """
        Build the BSP tree from the provided vertices and indices.
        """
        # Reshape indices to (T, 3)
        self.indices = self.indices.reshape(-1, 3).astype(np.int32)
        T = self.indices.shape[0]
        self.triangle_ids = np.arange(T, dtype=np.int32)

        # Create root node and start recursive splitting
        self.root = BSPNode()
        empty = np.array([], dtype=np.int32)
        self.split(self.root, self.triangle_ids, 0, empty)

    def tri_axis_minmax(self, tri_ids: np.ndarray, axis: int):
        """
        Compute per-triangle min and max coordinates along a given axis.
        """
        tris = self.indices[tri_ids]
        v = self.vertices[tris]
        a = v[:, :, axis]           
        return a.min(axis=1), a.max(axis=1)

    def choose_axis_value(self, tri_ids: np.ndarray):
        """
        Choose the splitting axis and split value for a set of triangles.
        """
        tris = self.indices[tri_ids]
        v = self.vertices[tris]
        tri_min = v.min(axis=1)
        tri_max = v.max(axis=1)

        overall_min = tri_min.min(axis=0)
        overall_max = tri_max.max(axis=0)
        spreads = overall_max - overall_min

        # Try axes in descending spread order
        for axis in np.argsort(spreads)[::-1]:
            axis = int(axis)
            if spreads[axis] < 1e-9:
                continue

            centroids = v.mean(axis=1)
            value = float(np.median(centroids[:, axis]))

            minA = tri_min[:, axis]
            maxA = tri_max[:, axis]

            left_possible = np.any(maxA < value)
            right_possible = np.any(minA > value)

            if left_possible and right_possible:
                return axis, value

        return None, None

    def split(self, node: BSPNode, tri_ids: np.ndarray, depth: int, carry_ids: np.ndarray):
        """
        Recursively split triangles into a BSP tree.

        Triangles that intersect the split plane are not passed to children;
        instead, they are inherited by all descendant leaves via the carry_ids
        mechanism.
        """
        n = int(tri_ids.size)

        # Stop criteria: create a leaf storing inherited and remaining triangles
        if depth >= self.max_depth or n == 0:
            if carry_ids.size == 0:
                node.triangles = tri_ids.astype(np.int32)
            elif n == 0:
                node.triangles = carry_ids.astype(np.int32)
            else:
                node.triangles = np.unique(
                    np.concatenate([carry_ids.astype(np.int32), tri_ids.astype(np.int32)])).astype(np.int32)
            return

        axis, value = self.choose_axis_value(tri_ids)
        if axis is None:
            if carry_ids.size == 0:
                node.triangles = tri_ids.astype(np.int32)
            else:
                node.triangles = np.unique(np.concatenate([carry_ids.astype(np.int32), tri_ids.astype(np.int32)])).astype(np.int32)
            return

        minA, maxA = self.tri_axis_minmax(tri_ids, axis)

        left_only = []
        right_only = []
        intersected = [] # both left and right

        for i, tid in enumerate(tri_ids):
            if maxA[i] < value:
                left_only.append(int(tid))
            elif minA[i] > value:
                right_only.append(int(tid))
            else:
                intersected.append(int(tid))

        left_ids = np.array(left_only, dtype=np.int32)
        right_ids = np.array(right_only, dtype=np.int32)
        stay_ids = np.array(intersected, dtype=np.int32)

        # If the split is not meaningful, create a leaf
        if left_ids.size == 0 or right_ids.size == 0:
            if carry_ids.size == 0:
                node.triangles = tri_ids.astype(np.int32)
            else:
                node.triangles = np.unique(
                    np.concatenate([carry_ids.astype(np.int32), tri_ids.astype(np.int32)])).astype(np.int32)
            return

        # Compute new inherited triangles for children
        if carry_ids.size == 0:
            new_carry = stay_ids
        elif stay_ids.size == 0:
            new_carry = carry_ids.astype(np.int32)
        else:
            new_carry = np.unique(np.concatenate([carry_ids.astype(np.int32), stay_ids])).astype(np.int32)

        # Commit internal node
        node.axis = axis
        node.value = float(value)
        node.triangles = None

        node.left = BSPNode()
        node.right = BSPNode()

        self.split(node.left, left_ids, depth + 1, new_carry)
        self.split(node.right, right_ids, depth + 1, new_carry)

    def trianglesCentroids(self):
        # self.indices: (T,3)
        i0 = self.indices[:, 0]
        i1 = self.indices[:, 1]
        i2 = self.indices[:, 2]

        v0 = self.vertices[i0]
        v1 = self.vertices[i1]
        v2 = self.vertices[i2]

        centroids = (v0 + v1 + v2) / 3.0
        return centroids.astype(np.float32)
    
    def print_by_depth(self):
        if self.root is None:
            print("Empty tree")
            return

        q = [(self.root, 0)]
        idx = 0
        cur_depth = 0
        print("Depth 0:")

        while idx < len(q):
            node, d = q[idx]
            idx += 1

            if d != cur_depth:
                cur_depth = d
                print(f"\nDepth {cur_depth}:")

            if node.isLeaf():
                print(f"  Leaf(tris={len(node.triangles)})", end="  ")
            else:
                print(f"  (a={node.axis}, v={node.value:.2f})", end="  ")
                if node.left is not None:
                    q.append((node.left, d + 1))
                if node.right is not None:
                    q.append((node.right, d + 1))

        print()

    def search(self, tri_id: int):
        """
        Directed BSP traversal.
        Returns a list of (leaf_node, path) where path contains
        (axis, value, decision) entries.
        """
        tri_id = int(tri_id)
        if self.root is None:
            return []

        # Compute triangle bounds once
        tri = self.indices[tri_id]
        v = self.vertices[tri]
        tri_min = v.min(axis=0)
        tri_max = v.max(axis=0)

        results = []
        stack = [(self.root, [])]  # (node, path)

        while stack:
            node, path = stack.pop()
            if node is None:
                continue

            if node.isLeaf():
                if node.triangles is not None and tri_id in node.triangles:
                    results.append((node, path))
                continue

            a = node.axis
            s = node.value

            if tri_max[a] < s:
                # LEFT only
                new_path = path + [(a, s, "LEFT")]
                stack.append((node.left, new_path))

            elif tri_min[a] > s:
                # RIGHT only
                new_path = path + [(a, s, "RIGHT")]
                stack.append((node.right, new_path))

            else:
                # BOTH sides
                new_path_left  = path + [(a, s, "BOTH")]
                new_path_right = path + [(a, s, "BOTH")]
                stack.append((node.left, new_path_left))
                stack.append((node.right, new_path_right))

        for i, (_, path) in enumerate(results):
            print(f"Path {i}:")
            for depth, (axis, value, decision) in enumerate(path):
                axis_name = ['x', 'y', 'z'][axis]
                print(f"  Depth {depth}: split {axis_name} = {value:.2f} -> {decision}")
            print()

        return results