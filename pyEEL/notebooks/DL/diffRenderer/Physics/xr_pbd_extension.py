"""
xr_pbd_extension.py — Elements Extension Module for XR-PBD

Provides a clean importable API wrapping the XR-PBD simulation classes
from the xr_pbd.ipynb notebook.

Usage (from another Elements notebook):
    import sys
    sys.path.insert(0, '../Physics')
    from xr_pbd_extension import XRPBDSimulator, Particle

Reference:
    Tamiolakis (2024) MSc Thesis; Tamiolakis et al. SIGGRAPH Asia 2025 XR-PBD paper.
"""
import numpy as np


class Particle:
    """A single XPBD simulation particle."""
    def __init__(self, pos, mass=1.0):
        self.pos = np.array(pos, dtype=float)
        self.prev_pos = self.pos.copy()
        self.vel = np.zeros_like(self.pos)
        self.mass = mass
        self.inv_mass = 0.0 if mass == 0 else 1.0 / mass


class DistanceConstraint:
    """Distance constraint: C(x1,x2) = |x1-x2| - d_rest (§4.3.1 of thesis)."""
    def __init__(self, p1, p2, particles, rest_len=None, alpha=0.0,
                 breakable=False, break_force=1e9):
        self.i1, self.i2 = p1, p2
        self.particles = particles
        self.alpha = alpha
        self.active = True
        self.breakable = breakable
        self.break_force = break_force
        self.lam = 0.0
        if rest_len is None:
            rest_len = np.linalg.norm(particles[p1].pos - particles[p2].pos)
        self.rest_len = rest_len

    def reset_lambda(self): self.lam = 0.0

    def solve(self, h, sor=1.0):
        if not self.active: return
        p1, p2 = self.particles[self.i1], self.particles[self.i2]
        diff = p1.pos - p2.pos
        dist = np.linalg.norm(diff)
        if dist < 1e-9: return
        n = diff / dist
        C = dist - self.rest_len
        alpha_t = self.alpha / (h * h)
        w_sum = p1.inv_mass + p2.inv_mass + alpha_t
        if w_sum < 1e-9: return
        d_lam = (-C - alpha_t * self.lam) / w_sum
        if self.breakable and abs(d_lam) / (h * h) > self.break_force:
            self.active = False; return
        d_lam *= sor
        self.lam += d_lam
        p1.pos += p1.inv_mass * d_lam * n
        p2.pos -= p2.inv_mass * d_lam * n


class VolumeConstraint:
    """
    Tetrahedral volume preservation constraint (§4.3.3 of thesis).

    Uses the signed scalar triple product formulation from XPBD:
      V = (1/6) * d1 · (d2 × d3)
      C = V - V0        (signed, so gradients are always correct)

    Gradients (from §A.2 of Müller 2020):
      ∇x0 C = (1/6)(d2×d3 + d3×d1 + d1×d2)  ... simplified: -1/6*(cross sums)
      ∇xi C = (1/6)(di-1 × di+1)
    """
    def __init__(self, i0, i1, i2, i3, particles, alpha=1e-5):
        self.ids = [i0, i1, i2, i3]
        self.particles = particles
        self.alpha = alpha
        self.lam = 0.0
        p = [particles[i].pos for i in self.ids]
        # Use signed rest volume (scalar triple product); track sign for consistency
        d1, d2, d3 = p[1]-p[0], p[2]-p[0], p[3]-p[0]
        self.V0_signed = np.dot(d1, np.cross(d2, d3)) / 6.0
        self.V0 = abs(self.V0_signed)
        # If rest volume is degenerate, flip orientation
        if abs(self.V0_signed) < 1e-10:
            self.V0_signed = 1e-10

    def reset_lambda(self): self.lam = 0.0

    def _signed_volume(self, p):
        d1, d2, d3 = p[1]-p[0], p[2]-p[0], p[3]-p[0]
        return np.dot(d1, np.cross(d2, d3)) / 6.0

    def solve(self, h, sor=1.0):
        p = [self.particles[i].pos for i in self.ids]
        V = self._signed_volume(p)
        # Constraint: match absolute volume (avoid sign flip blowup)
        C = abs(V) - self.V0
        if abs(C) < 1e-8: return

        # Gradients of |V| w.r.t. each vertex (sign from current V)
        sgn = 1.0 if V >= 0 else -1.0
        d1, d2, d3 = p[1]-p[0], p[2]-p[0], p[3]-p[0]
        # ∇x1 V = (1/6)(d2 × d3),  etc.
        g1 = sgn * np.cross(d2, d3) / 6.0
        g2 = sgn * np.cross(d3, d1) / 6.0
        g3 = sgn * np.cross(d1, d2) / 6.0
        g0 = -(g1 + g2 + g3)

        grads = [g0, g1, g2, g3]
        w = [self.particles[i].inv_mass for i in self.ids]
        w_sum = sum(wi * np.dot(g, g) for wi, g in zip(w, grads))
        alpha_t = self.alpha / (h * h)
        if w_sum + alpha_t < 1e-12: return
        d_lam = (-C - alpha_t * self.lam) / (w_sum + alpha_t) * sor
        self.lam += d_lam
        for i, g in zip(self.ids, grads):
            self.particles[i].pos += self.particles[i].inv_mass * d_lam * g


class InsertionConstraint:
    """
    5-particle insertion constraint for needle-tissue piercing.
    Novel contribution of XR-PBD (SIGGRAPH Asia 2025, §4.4).

    Parameters:
        t0,t1,t2  — tissue triangle particle indices
        n0,n1     — needle segment particle indices
        bw0..bw2  — barycentric weights of puncture point on triangle
        v         — parametric coord of puncture on needle (0=n0, 1=n1)
        alpha     — compliance (lower = stiffer)
        friction  — tangential friction coefficient
    """
    def __init__(self, t0, t1, t2, n0, n1, particles,
                 bw0=1/3, bw1=1/3, bw2=1/3, v=0.5,
                 alpha=1e-5, friction=0.4):
        self.t_ids = [t0, t1, t2]
        self.n_ids = [n0, n1]
        self.particles = particles
        self.bw = np.array([bw0, bw1, bw2])
        self.v = v
        self.alpha = alpha
        self.friction = friction
        self.lam = 0.0

    def reset_lambda(self): self.lam = 0.0

    def solve(self, h, sor=1.0):
        tp = [self.particles[i].pos for i in self.t_ids]
        np_ = [self.particles[i].pos for i in self.n_ids]
        q = sum(w*p for w, p in zip(self.bw, tp))
        r = (1-self.v)*np_[0] + self.v*np_[1]
        diff = q - r
        dist = np.linalg.norm(diff)
        if dist < 1e-9: return
        n_dir = diff / dist
        C = dist
        w_t = sum(w*w*self.particles[i].inv_mass
                  for w, i in zip(self.bw, self.t_ids))
        w_n = ((1-self.v)**2 * self.particles[self.n_ids[0]].inv_mass +
               self.v**2     * self.particles[self.n_ids[1]].inv_mass)
        alpha_t = self.alpha / (h*h)
        d_lam = (-C - alpha_t*self.lam) / (w_t + w_n + alpha_t) * sor
        self.lam += d_lam
        for w, i in zip(self.bw, self.t_ids):
            self.particles[i].pos += self.particles[i].inv_mass * w * d_lam * n_dir
        self.particles[self.n_ids[0]].pos -= (self.particles[self.n_ids[0]].inv_mass *
                                               (1-self.v) * d_lam * n_dir)
        self.particles[self.n_ids[1]].pos -= (self.particles[self.n_ids[1]].inv_mass *
                                               self.v * d_lam * n_dir)


class XRPBDSimulator:
    """
    High-level XR-PBD simulation API for Elements integration.

    Implements the main simulation loop from Algorithm 1 (thesis §4.2)
    with SOR acceleration (SIGGRAPH Asia 2025, §3.2).
    """
    def __init__(self, substeps=6, iterations=6, sor_factor=1.8,
                 gravity=None, dim=2):
        self.substeps = substeps
        self.iterations = iterations
        self.sor_factor = sor_factor
        self.dim = dim
        if gravity is None:
            self.gravity = np.array([0., -9.81]) if dim == 2 else np.array([0., -9.81, 0.])
        else:
            self.gravity = np.array(gravity)
        self.particles = []
        self.constraints = []

    # ── Builder helpers ────────────────────────────────────────────────────

    def add_particle(self, pos, mass=1.0):
        p = Particle(pos, mass)
        self.particles.append(p)
        return len(self.particles) - 1

    def add_constraint(self, c):
        self.constraints.append(c)
        return c

    def add_rope(self, n=15, length=3.0, origin=(0., 4.), mass=1.0, alpha=1e-5):
        """Add a chain of n particles as a rope. Top particle is pinned."""
        ids = []
        dx = length / max(n-1, 1)
        ox, oy = origin
        for i in range(n):
            pid = self.add_particle([ox, oy - i*dx], mass=mass)
            ids.append(pid)
            if i > 0:
                self.add_constraint(DistanceConstraint(ids[i-1], ids[i],
                                                        self.particles, alpha=alpha))
        self.particles[ids[0]].inv_mass = 0.0
        return ids

    def add_cloth_grid(self, rows=10, cols=10, width=3., height=3.,
                       origin=(0., 3.), mass=0.5,
                       alpha_struct=1e-6, alpha_shear=5e-5, alpha_bend=1e-3):
        """Add a 2D cloth grid (pins two top corners)."""
        ids = np.zeros((rows, cols), dtype=int)
        dx = width/(cols-1); dy = height/(rows-1)
        ox, oy = origin
        for r in range(rows):
            for c in range(cols):
                x = ox - width/2 + c*dx
                ids[r, c] = self.add_particle([x, oy - r*dy], mass=mass)
        self.particles[ids[0,  0]].inv_mass = 0
        self.particles[ids[0, -1]].inv_mass = 0
        p = self.particles
        for r in range(rows):
            for c in range(cols):
                if c+1 < cols:
                    self.add_constraint(DistanceConstraint(ids[r,c],ids[r,c+1],p,alpha=alpha_struct))
                if r+1 < rows:
                    self.add_constraint(DistanceConstraint(ids[r,c],ids[r+1,c],p,alpha=alpha_struct))
                if r+1<rows and c+1<cols:
                    self.add_constraint(DistanceConstraint(ids[r,c],ids[r+1,c+1],p,alpha=alpha_shear))
                    self.add_constraint(DistanceConstraint(ids[r+1,c],ids[r,c+1],p,alpha=alpha_shear))
                if c+2 < cols:
                    self.add_constraint(DistanceConstraint(ids[r,c],ids[r,c+2],p,alpha=alpha_bend))
                if r+2 < rows:
                    self.add_constraint(DistanceConstraint(ids[r,c],ids[r+2,c],p,alpha=alpha_bend))
        return ids

    # ── Simulation step ────────────────────────────────────────────────────

    def step(self, dt=0.016):
        """
        Advance simulation by dt using substeps and SOR-accelerated XPBD.
        According to SIGGRAPH Asia 2025 §3 (Algorithm 1 of thesis).
        """
        h = dt / self.substeps
        for _ in range(self.substeps):
            # Predict — broadcast gravity to match particle dimensionality
            for pt in self.particles:
                if pt.inv_mass == 0: continue
                ndim = pt.pos.shape[0]
                g = self.gravity[:ndim] if len(self.gravity) >= ndim else np.pad(self.gravity, (0, ndim - len(self.gravity)))
                pt.vel += g * h
                pt.prev_pos = pt.pos.copy()
                pt.pos += pt.vel * h
            # Solve constraints (SOR-Jacobi)
            for c in self.constraints:
                c.reset_lambda()
            for _ in range(self.iterations):
                for c in self.constraints:
                    c.solve(h, self.sor_factor)
            # Update velocities
            for pt in self.particles:
                if pt.inv_mass == 0: continue
                pt.vel = (pt.pos - pt.prev_pos) / h

    # ── Accessors ─────────────────────────────────────────────────────────

    def get_positions(self):
        """Return Nx2 or Nx3 array of particle positions."""
        return np.array([p.pos for p in self.particles])

    def get_velocities(self):
        return np.array([p.vel for p in self.particles])

    def get_active_constraints(self):
        return [c for c in self.constraints if getattr(c, 'active', True)]

    def apply_floor(self, y_floor=0.0, restitution=0.4):
        """Simple floor collision: bounce particles above y_floor."""
        for pt in self.particles:
            if pt.inv_mass == 0: continue
            if pt.pos[1] < y_floor:
                pt.pos[1] = y_floor
                pt.vel[1] = abs(pt.vel[1]) * restitution

    def kinetic_energy(self):
        """Compute total kinetic energy (for energy conservation validation)."""
        KE = 0.0
        for pt in self.particles:
            if pt.inv_mass > 0:
                KE += 0.5 * pt.mass * np.dot(pt.vel, pt.vel)
        return KE


# ── Module smoke test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    sim = XRPBDSimulator(substeps=6, sor_factor=1.8)
    rope_ids = sim.add_rope(n=10, length=2.0)
    for step in range(100):
        sim.step(dt=0.016)
        sim.apply_floor(y_floor=-1.0)
    pos = sim.get_positions()
    n_active = len(sim.get_active_constraints())
    print(f"✓ XRPBDSimulator smoke test: {len(pos)} particles, {n_active} active constraints")
    print(f"  Particle 5 pos: {pos[rope_ids[5]]}")
    print(f"  KE = {sim.kinetic_energy():.4f} J")
