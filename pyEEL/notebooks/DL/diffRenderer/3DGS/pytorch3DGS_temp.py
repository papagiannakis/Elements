#!/usr/bin/env python
# coding: utf-8

# # 3D Gaussian Splatting: Differentiable Rendering with PyTorch
# 
# This notebook implements the **Reference Architecture** described in the breakthrough paper *["3D Gaussian Splatting for Real-Time Radiance Field Rendering"](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/)* (SIGGRAPH 2023).
# 
# ### Goal
# We aim to implement a **Differentiable Rasterizer** from scratch using pure PyTorch. This allows us to forward-render a scene of 3D Gaussians and, crucially, **optimize** their parameters (Position, Rotation, Scale, Color, Opacity) to match a target image.
# 
# ### The Pipeline
# 1.  **3D Gaussians**: Defined by Mean $\mu$ and Covariance $\Sigma$.
# 2.  **Projection**: Transforming 3D ellipsoids to 2D splats using the EWA (Elliptical Weighted Average) approximation.
# 3.  **Rasterization**: Sorting splats by depth and compositing them front-to-back.
# 4.  **Optimization**: Using Gradient Descent to learn the scene.
# 

# ## 1. The Mathematical Model
# 
# ### 1.1 The Anisotropic 3D Gaussian
# Instead of a hard point or significant mesh, we represent scene geometry as soft probabilistic blobs (Gaussians). A 3D Gaussian is defined by:
# $$ G(x) = e^{-\frac{1}{2} (x - \mu)^T \Sigma^{-1} (x - \mu)} $$
# where:
# *   $\mu$: The XYZ center of the Gaussian.
# *   $\Sigma$: The 3D Covariance Matrix controlling spread and orientation.
# 
# ### 1.2 Constructing Covariance ($\Sigma$)
# Directly optimizing $\Sigma$ is hard because it must remain positive semi-definite. Instead, we decompose it into **Scaling ($S$)** and **Rotation ($R$)**:
# $$ \Sigma = R S S^T R^T $$
# *   **$S$**: A diagonal scaling matrix (scaling factors for x, y, z axes).
# *   **$R$**: A rotation matrix derived from a Quaternion $q$.
# 
# ### 1.3 Projecting to 2D ($\Sigma'$)
# To render the Gaussian, we project it onto the 2D image plane. The local affine approximation of the perspective projection gives us the 2D covariance $\Sigma'$:
# $$ \Sigma' = J W \Sigma W^T J^T $$
# where:
# *   $W$: The **Viewing Transformation** matrix (World-to-Camera).
# *   $J$: The **Jacobian** of the affine approximation of the projective transformation.
# 
# ### 1.4 Alpha Blending (Splatting)
# The final color $C$ of a pixel is computed by blending $N$ ordered Gaussians overlapping that pixel:
# $$ C = \sum_{i \in N} c_i \alpha_i \prod_{j=1}^{i-1} (1 - \alpha_j) $$
# where $\alpha_i$ is the opacity of the $i$-th Gaussian at that pixel (product of learned opacity and Gaussian falloff).
# 

# In[ ]:


import torch
import torch.nn as nn
import math
import numpy as np
import matplotlib.pyplot as plt
import struct
import os

torch.manual_seed(42)
device = torch.device('cpu')
print(f"Using device: {device}")


# In[ ]:


def build_rotation(r):
    norm = torch.sqrt(r[:,0]*r[:,0] + r[:,1]*r[:,1] + r[:,2]*r[:,2] + r[:,3]*r[:,3])
    q = r / norm[:, None]
    R = torch.zeros((q.shape[0], 3, 3), device=device)
    r = q[:, 0]; x = q[:, 1]; y = q[:, 2]; z = q[:, 3]
    R[:, 0, 0] = 1 - 2 * (y*y + z*z)
    R[:, 0, 1] = 2 * (x*y - r*z)
    R[:, 0, 2] = 2 * (x*z + r*y)
    R[:, 1, 0] = 2 * (x*y + r*z)
    R[:, 1, 1] = 1 - 2 * (x*x + z*z)
    R[:, 1, 2] = 2 * (y*z - r*x)
    R[:, 2, 0] = 2 * (x*z - r*y)
    R[:, 2, 1] = 2 * (y*z + r*x)
    R[:, 2, 2] = 1 - 2 * (x*x + y*y)
    return R

def build_scaling(s):
    S = torch.zeros((s.shape[0], 3, 3), device=device)
    S[:, 0, 0] = s[:, 0]
    S[:, 1, 1] = s[:, 1]
    S[:, 2, 2] = s[:, 2]
    return S

def compute_covariance_3d(scaling, quaternion):
    R = build_rotation(quaternion)
    S = build_scaling(scaling)
    M = torch.bmm(R, S)
    return torch.bmm(M, M.transpose(1, 2))

def compute_2d_covariance(covariance_3d, view_matrix, world_pos, width, height, tan_fovx, tan_fovy):
    R_view = view_matrix[:3, :3] 
    t_view = view_matrix[:3, 3]
    pos_view = torch.matmul(world_pos, R_view.T) + t_view
    x, y, z = pos_view[:, 0], pos_view[:, 1], pos_view[:, 2]
    focal_x = width / (2.0 * tan_fovx)
    focal_y = height / (2.0 * tan_fovy)
    z = torch.clamp(z, min=0.001)
    J = torch.zeros((world_pos.shape[0], 2, 3), device=device)
    J[:, 0, 0] = focal_x / z
    J[:, 0, 2] = -(focal_x * x) / (z * z)
    J[:, 1, 1] = focal_y / z
    J[:, 1, 2] = -(focal_y * y) / (z * z)
    W = R_view.unsqueeze(0).expand(world_pos.shape[0], 3, 3)
    T = torch.bmm(J, W)
    cov2d = torch.bmm(T, torch.bmm(covariance_3d, T.transpose(1, 2)))
    cov2d[:, 0, 0] += 0.3; cov2d[:, 1, 1] += 0.3
    return cov2d, pos_view

print("Math defined.")


# ## 2. Theory: How Differentiable Rasterization Works
# 
# This is the core innovation enabling the system to "learn".
# 
# ### 2.1 The Problem with Triangles
# In standard rendering, a pixel is either "inside" or "outside" a triangle. This is a binary step function.
# *   **Forward**: $Color = C_{tri}$ if inside else $C_{bg}$.
# *   **Gradient**: $\frac{\partial Color}{\partial Position}$ is **zero** almost everywhere (moving the triangle slightly doesn't change the pixel color) or **infinite** at the very edge (sudden jump).
# This makes Gradient Descent impossible.
# 
# ### 2.2 The Gaussian Solution
# A 2D Gaussian Splat decreases in opacity smoothly away from its center:
# $$ \alpha(x) = o \cdot e^{-\frac{1}{2} (x - \mu)^T \Sigma^{-1} (x - \mu)} $$
# If we shift the Gaussian center $\mu$ slightly by $\Delta \mu$, the opacity $\alpha(x)$ at a pixel changes smoothly by a small amount. This means the derivative $\frac{\partial \alpha}{\partial \mu}$ is well-defined and non-zero.
# 
# ### 2.3 The Chain Rule of Learning
# When we compute the Loss (Error) between the rendered image and the reference photo, the gradients flow backward through the entire pipeline:
# 
# 1.  **Pixel Loss** $\to$ **Blended Color**: The error tells us how the final pixel color needs to change.
#     $$ \frac{\partial Loss}{\partial C_{final}} $$
# 
# 2.  **Color** $\to$ **Opacity ($\alpha$)**: The blending formula $C = C_i \alpha_i + C_{bg} (1-\alpha_i)$ is differentiable. We learn how much more/less opacity we need.
#     $$ \frac{\partial C_{final}}{\partial \alpha_i} = C_i - C_{bg} $$
# 
# 3.  **Opacity** $\to$ **Position/Shape**: The opacity depends on the distance filter.
#     $$ \frac{\partial \alpha_i}{\partial \mu} \propto \alpha_i \cdot (x - \mu) $$
#     This tells the system: *"Move the Gaussian closer to this pixel to increase influence!"*
# 

# In[ ]:


def differentiable_rasterizer(world_pos, colors, opacities, scales, rots, width, height):
    fov_y = 60.0
    tan_fovy = math.tan(math.radians(fov_y) * 0.5)
    tan_fovx = tan_fovy * (width / height)
    view_mat = torch.eye(4, device=device)
    view_mat[2, 3] = 5.0 
    view_mat = torch.inverse(view_mat)
    
    cov3d = compute_covariance_3d(scales, rots)
    cov2d, pos_view = compute_2d_covariance(cov3d, view_mat, world_pos, width, height, tan_fovx, tan_fovy)
    
    focal_x = width / (2.0 * tan_fovx)
    focal_y = height / (2.0 * tan_fovy)
    screen_x = (pos_view[:, 0] / pos_view[:, 2]) * focal_x + width / 2.0
    screen_y = (pos_view[:, 1] / pos_view[:, 2]) * focal_y + height / 2.0
    
    depths = pos_view[:, 2]
    sorted_idx = torch.argsort(depths, descending=True)
    y_grid, x_grid = torch.meshgrid(torch.arange(height, device=device), torch.arange(width, device=device), indexing='ij')
    
    canvas = torch.zeros((height, width, 3), device=device)
    
    for idx in sorted_idx:
        canvas = canvas.clone()
        
        mu = torch.stack([screen_x[idx], screen_y[idx]])
        sigma = cov2d[idx]
        color = colors[idx]
        opacity = opacities[idx]
        
        try: inv_sigma = torch.inverse(sigma)
        except RuntimeError: continue
        
        det = torch.det(sigma)
        radius = 3.0 * torch.sqrt(torch.max(torch.abs(sigma)))
        radius = torch.clamp(radius, min=1.0, max=width)
        
        min_x = int(torch.clamp(mu[0] - radius, 0, width).item())
        max_x = int(torch.clamp(mu[0] + radius, 0, width).item())
        min_y = int(torch.clamp(mu[1] - radius, 0, height).item())
        max_y = int(torch.clamp(mu[1] + radius, 0, height).item())
        
        if max_x <= min_x or max_y <= min_y: continue
            
        grid_x_slice = x_grid[min_y:max_y, min_x:max_x].float()
        grid_y_slice = y_grid[min_y:max_y, min_x:max_x].float()
        dx = grid_x_slice - mu[0]
        dy = grid_y_slice - mu[1]
        power = -0.5 * (inv_sigma[0, 0] * dx * dx + 2 * inv_sigma[0, 1] * dx * dy + inv_sigma[1, 1] * dy * dy)
        alpha_splat = torch.exp(power) * opacity
        alpha_splat = alpha_splat.unsqueeze(-1)
        
        current_bg = canvas[min_y:max_y, min_x:max_x].clone()
        blended_slice = color * alpha_splat + current_bg * (1.0 - alpha_splat)
        canvas[min_y:max_y, min_x:max_x] = blended_slice
        
    return canvas

print("Rasterizer defined (Fix 2).")


# In[ ]:


def optimization_demo():
    print("Starting Optimization Demo...")
    W, H = 64, 64 
    target_canvas = torch.zeros((H, W, 3), device=device)
    xv, yv = torch.meshgrid(torch.arange(H), torch.arange(W), indexing='ij')
    dist = torch.sqrt((xv - W/2)**2 + (yv - H/2)**2)
    mask = dist < 15
    target_canvas[mask] = torch.tensor([0.0, 1.0, 0.0])
    
    xyz = nn.Parameter(torch.tensor([[2.0, 2.0, 0.0]], device=device))
    color = nn.Parameter(torch.tensor([[1.0, 0.0, 0.0]], device=device))
    scale = nn.Parameter(torch.tensor([[0.5, 0.5, 0.5]], device=device))
    rot = nn.Parameter(torch.tensor([[1.0, 0.0, 0.0, 0.0]], device=device)) 
    opacity = nn.Parameter(torch.tensor([0.8], device=device))
    
    optimizer = torch.optim.Adam([xyz, color, scale, opacity], lr=0.1)
    losses = []
    
    for i in range(101):
        optimizer.zero_grad()
        render = differentiable_rasterizer(xyz, color, opacity, scale, rot, W, H)
        loss = torch.mean(torch.abs(render - target_canvas))
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
        if i % 20 == 0: print(f"Iter {i}: Loss {loss.item():.4f}")
            
    plt.figure(figsize=(10,3))
    plt.subplot(1,3,1); plt.imshow(target_canvas.detach().cpu()); plt.title("Target Ground Truth")
    plt.subplot(1,3,2); plt.imshow(render.detach().cpu()); plt.title("Learned Gaussian")
    plt.subplot(1,3,3); plt.plot(losses); plt.title("Training Loss")
    plt.tight_layout()
    plt.show()

optimization_demo()


# ## 6. Visualizing a Real 3DGS Scene
# 
# This section allows you to load a standard `point_cloud.ply` file from a trained model (e.g., from the official Inria repository or a huggingface dataset) and visualize it using our differentiable rasterizer.
# 
# **Note on Performance**: 
# Because our pure Python rasterizer iterates over Gaussians one-by-one, rendering millions of points would take hours. 
# We strictly **subsample** the scene to a small number of points (e.g., 2000) for this visualization.
# 

# In[ ]:


def load_ply_tensor(path, max_gaussians=5000):
    """
    Loads a PLY file directly into PyTorch tensors.
    Subsamples randomly if the file is too large.
    """
    print(f"Loading {path}...")
    with open(path, "rb") as f:
        properties = []
        num_verts = 0
        while True:
            line = f.readline().decode("utf-8", errors='ignore').strip()
            if line == "end_header": break
            if line.startswith("element vertex"): num_verts = int(line.split()[-1])
            if line.startswith("property"): properties.append(line.split()[-1])
        
        # Limit reading for speed
        print(f"Total points: {num_verts} (Loading up to {max_gaussians} for demo)")
        
        # Read full header stride
        dtype = np.dtype([(p, np.float32) for p in properties])
        stride = 4 * len(properties)
        
        # We read ALL and then subsample (if possible/memory allows) or just read first N
        # Better: Read first N for speed.
        read_limit = min(num_verts, max_gaussians * 10) # Read a bit more to sample better?
        # Actually just read first max_gaussians for simplicity in pure python demo
        read_count = min(num_verts, max_gaussians)
        
        data = f.read(stride * read_count)
        vertices = np.frombuffer(data, dtype=dtype, count=read_count)

    # Extract to Tensors
    def get_attr(names, default_val=0.0):
        for name in names:
            if name in vertices.dtype.names: return torch.from_numpy(vertices[name].copy())
        return torch.full((read_count,), default_val)
        
    x = get_attr(['x'])
    y = get_attr(['y'])
    z = get_attr(['z'])
    xyz = torch.stack([x, y, z], dim=1).to(device)
    
    sx = torch.exp(get_attr(['scale_0'], -3.0))
    sy = torch.exp(get_attr(['scale_1'], -3.0))
    sz = torch.exp(get_attr(['scale_2'], -3.0))
    scale = torch.stack([sx, sy, sz], dim=1).to(device)
    
    rw = get_attr(['rot_0'], 1.0)
    rx = get_attr(['rot_1'], 0.0)
    ry = get_attr(['rot_2'], 0.0)
    rz = get_attr(['rot_3'], 0.0)
    rot = torch.stack([rx, ry, rz, rw], dim=1).to(device)
    
    op_raw = get_attr(['opacity'], 0.0)
    opacity = torch.sigmoid(op_raw).to(device)
    
    # Standard SH DC terms => RGB
    SH_C0 = 0.28209479177387814
    dc0 = get_attr(['f_dc_0', 'red'])
    dc1 = get_attr(['f_dc_1', 'green'])
    dc2 = get_attr(['f_dc_2', 'blue'])
    
    # If standard 3DGS, convert SH to RGB
    if 'f_dc_0' in vertices.dtype.names:
        r = 0.5 + SH_C0 * dc0
        g = 0.5 + SH_C0 * dc1
        b = 0.5 + SH_C0 * dc2
    else:
        r = dc0 / 255.0
        g = dc1 / 255.0
        b = dc2 / 255.0
        
    rgb = torch.stack([r, g, b], dim=1).clamp(0.0, 1.0).to(device)
    
    return xyz, rgb, opacity, scale, rot

ply_path = "point_cloud.ply"
if os.path.exists(ply_path):
    try:
        print("Visualizing Real Scene (Subsampled)...")
        xyz, rgb, op, sc, rot = load_ply_tensor(ply_path, max_gaussians=3000)
        
        # Center the object roughly
        center = torch.mean(xyz, dim=0)
        xyz = xyz - center
        
        # Render
        with torch.no_grad():
            img = differentiable_rasterizer(xyz, rgb, op, sc, rot, 256, 256)
        
        plt.figure(figsize=(5,5))
        plt.imshow(img.cpu().numpy())
        plt.title(f"Real Scene (3000 points)")
        plt.axis('off'); plt.show()
    except Exception as e:
        print(f"Failed to render real scene: {e}")
else:
    print("No 'point_cloud.ply' found. Add one to visualize a real scene!")

