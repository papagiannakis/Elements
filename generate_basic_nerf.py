import nbformat as nbf
import os

nb = nbf.v4.new_notebook()

# Cell 1: Intro
intro_text = r"""# Basic Neural Radiance Fields (NeRF)

This notebook implements a basic **Neural Radiance Field** (NeRF) from scratch using PyTorch. 

## The Paper: "NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis"
*   **Original Paper**: [Mildenhall et al. ECCV 2020](https://arxiv.org/abs/2003.08934)
*   **Core Concept**: A scene is represented as a continuous 5D function $F(x, y, z, \theta, \phi) \to (r, g, b, \sigma)$, parameterized by a fully connected deep network (MLP).

### Main Innovations
1.  **Continuous Volumetric Representation**: Unlike meshes or voxel grids, NeRF represents geometry and appearance as a continuous field. This resolution-independent representation allows for high-quality close-ups.
2.  **Positional Encoding**: Neural networks favor low-frequency functions (spectral bias). NeRF maps input coordinates to a higher-dimensional space using high-frequency sinusoids: $\gamma(p) = (\sin(2^0\pi p), \cos(2^0\pi p), \dots)$, enabling the MLP to capture fine details like texture and sharp edges.
3.  **Differentiable Volumetric Rendering**: The rendering process is fully differentiable, allowing the 3D scene representation to be optimized directly from a set of 2D images using gradient descent.
4.  **Hierarchical Volume Sampling**: To render efficiently, NeRF uses a "coarse" network to find relevant scene areas and a "fine" network to sample densely there.

---

## Comparison with Other Techniques

### NeRF vs. 3D Gaussian Splatting (3DGS)
*   **Representation**: NeRF is **Implicit** (a neural network defines the scene). 3DGS is **Explicit** (millions of discrete Gaussian blobs).
*   **Rendering Speed**: NeRF requires querying a huge MLP hundreds of times *per pixel*, making it slow (seconds/minutes per frame). 3DGS projects Gaussians via rasterization, running in **real-time** (30-100+ FPS).
*   **Training Speed**: NeRF takes hours/days. 3DGS takes minutes/hours.
*   **Quality**: NeRF has less artifacts but can be blurry. 3DGS is sharper but can have "popping" artifacts.

### NeRF vs. Ray Tracing
*   **Paradigm**: Ray Tracing simulates the physical transport of light (bounces, refraction, reflection) to generate an image from geometry. NeRF approximates the *radiance* field directly.
*   **Usage**: Ray Tracing is "Forward Rendering" (Geometry $\to$ Image). NeRF is typically used for "Inverse Rendering" (Images $\to$ Geometry). Basic NeRF does not easily support relighting or moving objects, unlike Ray Tracing.

### NeRF vs. Rasterization (Standard 3D)
*   **Geometry**: Rasterization projects triangles (meshes) onto a 2D screen. NeRF integrates density along a ray.
*   **Differentiability**: Rasterization is hard to differentiate because occlusion (edges) is discontinuous. NeRF's volumetric rendering is smooth and fully differentiable, making it ideal for learning 3D structure from images.

### NeRF vs. Precomputed Radiance Transfer (PRT)
*   **Goal**: PRT solves the rendering equation for static scenes to enable fast real-time relighting with environment maps (using Spherical Harmonics).
*   **Relighting**: PRT separates lighting from transfer functions. Basic NeRF "bakes" the lighting into the radiance field. To achieve PRT-like results, extensions like NeRF-W or Relighting NeRFs disentangle material (BRDF) from illumination.
"""

# Cell 2: Imports
imports_code = """import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt

# Check for GPU
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Reproducibility
torch.manual_seed(42)
np.random.seed(42)
"""

# Cell 3: Data Generation (Tiny Synthetic Scene)
data_text = """## 1. Scene & Data Generation
We create a synthetic synthetic scene composed of simple geometric objects (Spheres) to train our NeRF on.
Since we don't have an external dataset, we generate "Ground Truth" images by ray-tracing these spheres analytically.
"""
data_code = """def get_rays(H, W, focal, c2w):
    # Create meshgrid of pixels
    i, j = torch.meshgrid(torch.linspace(0, W-1, W), torch.linspace(0, H-1, H), indexing='ij')
    i = i.t(); j = j.t()
    
    # Pixel -> Camera Coordinates
    dirs = torch.stack([(i-W*.5)/focal, -(j-H*.5)/focal, -torch.ones_like(i)], -1)
    
    # Camera -> World Coordinates (Rotate ray directions)
    rays_d = torch.sum(dirs[..., np.newaxis, :] * c2w[:3,:3], -1) 
    
    # Ray origins are just the camera position
    rays_o = c2w[:3, -1].expand(rays_d.shape)
    
    return rays_o, rays_d

def render_sphere_gt(H, W, focal, c2w, radius=0.5, center=torch.tensor([0,0,-1.0])):
    # Analytical sphere rendering for Ground Truth
    rays_o, rays_d = get_rays(H, W, focal, c2w)
    
    # Ray-Sphere Intersection
    # Sphere: ||x - c||^2 = r^2
    # Ray: x = o + t*d
    # Quadratic equation for t
    
    oc = rays_o - center
    a = torch.sum(rays_d**2, dim=-1)
    b = 2.0 * torch.sum(oc * rays_d, dim=-1)
    c = torch.sum(oc**2, dim=-1) - radius**2
    
    discriminant = b**2 - 4*a*c
    mask = discriminant > 0
    
    img = torch.zeros((H, W, 3))
    
    # Simple shading based on normal
    if mask.any():
        t = (-b[mask] - torch.sqrt(discriminant[mask])) / (2*a[mask])
        hit_points = rays_o[mask] + t.unsqueeze(-1) * rays_d[mask]
        
        normals = (hit_points - center) / radius
        light_dir = torch.tensor([0.577, 0.577, 0.577]) # Directional light
        
        diffuse = torch.clamp(torch.sum(normals * light_dir, dim=-1), 0.0, 1.0)
        col = torch.tensor([1.0, 0.0, 0.0]) # Red sphere
        
        img[mask] = col * diffuse.unsqueeze(-1) + 0.1 # Ambient
        
    return img

test_H, test_W = 100, 100
test_focal = 100
test_c2w = torch.eye(4)
test_gt = render_sphere_gt(test_H, test_W, test_focal, test_c2w)

plt.imshow(test_gt)
plt.title("Synthetic Ground Truth (Sphere)")
plt.show()
"""

# Cell 4: NeRF Model
model_text = r"""## 2. NeRF Architecture
The model consists of:
1.  **Positional Encoding**: $\gamma(p) = (\sin(2^0 \pi p), \cos(2^0 \pi p), ..., \sin(2^{L-1} \pi p), \cos(2^{L-1} \pi p))$. This maps low-freq positions to high-freq features, enabling the network to learn fine details (spectral bias).
2.  **MLP**: A simple fully connected network.
"""
model_code = """class PositionalEncoding(nn.Module):
    def __init__(self, L_embed=6):
        super().__init__()
        self.L_embed = L_embed
        
    def forward(self, x):
        emb = [x]
        for i in range(self.L_embed):
            emb.append(torch.sin(2.0**i * x))
            emb.append(torch.cos(2.0**i * x))
        return torch.cat(emb, dim=-1)

class NeRF(nn.Module):
    def __init__(self, D=8, W=256, output_ch=4, skips=[4], L_embed=6):
        super().__init__()
        self.skips = skips
        input_ch = 3 + 3 * 2 * L_embed 
        
        self.pts_linears = nn.ModuleList(
            [nn.Linear(input_ch, W)] + 
            [nn.Linear(W, W) if i not in skips else nn.Linear(W + input_ch, W) for i in range(D-1)]
        )
        
        self.output_linear = nn.Linear(W, output_ch) # RGB + Sigma
        
    def forward(self, x):
        h = x
        for i, l in enumerate(self.pts_linears):
            h = self.pts_linears[i](h)
            h = F.relu(h)
            if i in self.skips:
                h = torch.cat([x, h], -1)
        
        outputs = self.output_linear(h)
        return outputs
"""

# Cell 5: Volumetric Rendering
renderer_text = r"""## 3. Differentiable Volumetric Rendering
This is the core physics simulation.
We sample points along the ray, query the model, and integrate.
$$ C = \sum T_i \alpha_i c_i $$
where $\alpha_i = 1 - \exp(-\sigma_i \delta_i)$.
"""
renderer_code = """def raw2outputs(raw, z_vals, rays_d):
    # raw: [N_rays, N_samples, 4] -> (rgb, density)
    # z_vals: [N_rays, N_samples] -> integration time
    # rays_d: [N_rays, 3] -> ray direction
    
    # 1. Distances between adjacent samples
    dists = z_vals[..., 1:] - z_vals[..., :-1]
    # Add infinite distance for implementation convenience at the end
    last_dist = torch.tensor([1e10], device=raw.device).expand(dists[...,:1].shape)
    dists = torch.cat([dists, last_dist], -1)
    
    # Scale density by ray direction magnitude (optional, usually normalized d)
    dists = dists * torch.norm(rays_d[...,None,:], dim=-1)
    
    # 2. Extract Data
    rgb = torch.sigmoid(raw[..., :3]) # [N_rays, N_samples, 3]
    noise = 0.0
    # Use Softplus to avoid "dead neurons" (zero gradient) when density is initially low
    sigma_a = F.softplus(raw[..., 3] + noise)
    
    # 3. Alpha Composition
    # alpha = 1 - exp(-sigma * delta)
    alpha = 1.0 - torch.exp(-sigma_a * dists)
    
    # 4. Transmittance
    # T_i = exp(-sum(sigma_j * delta_j))
    # We use cumprod of (1-alpha) which is equivalent to exp(-sum...)
    # T_i is prob of NOT hitting anything up to i
    
    weights = alpha * torch.cumprod(torch.cat([torch.ones((alpha.shape[0], 1), device=alpha.device), 1.-alpha + 1e-10], -1), -1)[:, :-1]
    
    rgb_map = torch.sum(weights[...,None] * rgb, -2)
    depth_map = torch.sum(weights * z_vals, -1)
    
    return rgb_map, depth_map, weights

def render_rays(rays_o, rays_d, model, embedder, near=2.0, far=6.0, N_samples=64):
    device = rays_o.device
    
    # Stratified Sampling (Stochastic)
    z_vals = torch.linspace(near, far, N_samples, device=device).expand(rays_o.shape[0], N_samples)
    
    # Perturb during training
    mids = .5 * (z_vals[...,1:] + z_vals[...,:-1])
    upper = torch.cat([mids, z_vals[...,-1:]], -1)
    lower = torch.cat([z_vals[...,:1], mids], -1)
    t_rand = torch.rand(z_vals.shape, device=device)
    z_vals = lower + (upper - lower) * t_rand
    
    # Evaluate Points
    # pts = o + t * d
    pts = rays_o[...,None,:] + rays_d[...,None,:] * z_vals[...,:,None]
    
    # Flatten for network
    flat_pts = pts.reshape(-1, 3)
    embedded_pts = embedder(flat_pts)
    
    # Network pass (Chunkify if needed for memory, here simplified)
    raw = model(embedded_pts)
    raw = raw.reshape(rays_o.shape[0], N_samples, 4)
    
    # Volume Rendering
    rgb_map, depth_map, weights = raw2outputs(raw, z_vals, rays_d)
    
    return rgb_map, depth_map
"""

# Cell 6: Training Loop
train_text = r"""## 4. Training Loop
1.  **Data**: Generate random rays from our view.
2.  **Forward**: Render rays using NeRF.
3.  **Loss**: MSE between Render and Ground Truth ($L = ||C - C_{gt}||^2$).
4.  **Backend**: Adam Optimizer.
"""
train_code = """# Setup
L_embed = 6
embedder = PositionalEncoding(L_embed=L_embed).to(device)
model = NeRF(L_embed=L_embed).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=5e-4)

# Training Configuration
N_iters = 1001
batch_size = 1024 # Rays per step
print_every = 100

history_loss = []

# Create a full image of rays for testing
test_rays_o, test_rays_d = get_rays(test_H, test_W, test_focal, test_c2w)
test_rays_o = test_rays_o.reshape(-1, 3).to(device)
test_rays_d = test_rays_d.reshape(-1, 3).to(device)
test_target = test_gt.reshape(-1, 3).to(device)

print("Starting Training...")

for i in range(N_iters):
    model.train()
    
    # Randomly sample rays from the image (Just 1 view for overfitting demo)
    # Ideally we use multiple views!
    idxs = np.random.choice(test_rays_o.shape[0], batch_size, replace=False)
    batch_rays_o = test_rays_o[idxs]
    batch_rays_d = test_rays_d[idxs]
    batch_target = test_target[idxs]
    
    # Render
    rgb, depth = render_rays(batch_rays_o, batch_rays_d, model, embedder, near=0.5, far=1.5)
    
    # Loss
    loss = torch.mean((rgb - batch_target)**2)
    
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    history_loss.append(loss.item())
    
    if i % print_every == 0:
        print(f"Iter {i}: Loss {loss.item():.4f}")
        
        # Validation Rendering (Low Res to be fast)
        # We just render the center line
        with torch.no_grad():
            row_idx = test_H // 2
            # Render one full image every so often if needed, but slow on CPU
            
# Final Render
print("Rendering Final Result...")
model.eval()
all_rgb = []
chunk = 1024
with torch.no_grad():
    for j in range(0, test_rays_o.shape[0], chunk):
        batch_rays_o = test_rays_o[j:j+chunk]
        batch_rays_d = test_rays_d[j:j+chunk]
        rgb, _ = render_rays(batch_rays_o, batch_rays_d, model, embedder, near=0.5, far=1.5)
        all_rgb.append(rgb.cpu())

final_img = torch.cat(all_rgb, 0).reshape(test_H, test_W, 3)

plt.figure(figsize=(10,4))
plt.subplot(1,3,1); plt.imshow(test_gt.cpu()); plt.title("Target")
plt.subplot(1,3,2); plt.imshow(final_img); plt.title("Learned NeRF")
plt.subplot(1,3,3); plt.plot(history_loss); plt.title("Loss")
plt.show()
"""

nb['cells'] = [
    nbf.v4.new_markdown_cell(intro_text),
    nbf.v4.new_code_cell(imports_code),
    nbf.v4.new_markdown_cell(data_text),
    nbf.v4.new_code_cell(data_code),
    nbf.v4.new_markdown_cell(model_text),
    nbf.v4.new_code_cell(model_code),
    nbf.v4.new_markdown_cell(renderer_text),
    nbf.v4.new_code_cell(renderer_code),
    nbf.v4.new_markdown_cell(train_text),
    nbf.v4.new_code_cell(train_code)
]

output_path = 'pyEEL/notebooks/DL/diffRenderer/NERF/basicNERF.ipynb'
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, 'w') as f:
    nbf.write(nb, f)
    
print(f"Generated {output_path}")
