import numpy as np

# 1. Coulomb's Law
def coulombs_law(charge1, charge2, r_vec):
    returns = "electrostatic_force"
    r = np.linalg.norm(r_vec)
    k_e = 8.9875517923e9  # N·m²/C²
    return k_e * charge1 * charge2 / r**2 if r != 0 else np.inf


# 2. Newton's Second Law
def newtons_second_law(mass, acceleration):
    returns = "force_vector"
    return mass * np.array(acceleration)

# 3. Kinetic Energy
def kinetic_energy(mass, velocity):
    returns = "kinetic_energy"
    v = np.linalg.norm(velocity)
    return 0.5 * mass * v**2

# 4. Potential Energy (gravitational)
def gravitational_potential_energy(
        mass,
        pos,
        g_vec, # gravty direction

):
    returns = "gravitational_potential_energy"
    return -mass * np.dot(pos, g_vec)

# 6. Ohm's Law
def ohms_law(voltage, resistance):
    returns = "current"
    return voltage / resistance

# 7. Einstein's Mass-Energy Equivalence
def mass_energy_equivalence(mass):
    returns = "mass_energy"
    c = 299_792_458
    return mass * c**2

# 8. Schrödinger's Energy (3D particle in a box)
def schrodinger_energy(n_xyz, m, L_xyz, h=6.62607015e-34):
    returns = "quantum_energy"
    n_x, n_y, n_z = n_xyz
    L_x, L_y, L_z = L_xyz
    term = (n_x**2 / L_x**2 + n_y**2 / L_y**2 + n_z**2 / L_z**2)
    return (h**2 * term) / (8 * m)

# 9. First Law of Thermodynamics
def first_law_thermodynamics(Q, W):
    returns = "internal_energy"
    return Q - W

# 10. Second Law of Thermodynamics
def entropy_change(Q, T):
    returns = "entropy_change"
    return Q / T if T != 0 else np.inf

# 11. Gauss's Law
def gauss_law_electric(E_field, area):
    returns = "electric_flux"
    epsilon_0 = 8.854187817e-12
    return np.dot(E_field, area) / epsilon_0

# 12. Boltzmann Entropy
def boltzmann_entropy(W):
    returns = "entropy"
    k_B = 1.380649e-23
    return k_B * np.log(W)

# 13. Heisenberg Uncertainty Principle
def heisenberg_uncertainty(delta_x, h=6.62607015e-34):
    returns = "uncertainty_momentum"
    return h / (4 * np.pi * delta_x)

# 14. Lorentz Force
def lorentz_force(q, v, B):
    returns = "lorentz_force"
    return q * np.cross(v, B)

# 15. Hooke's Law
def hookes_law(spring_constant, displacement):
    returns = "spring_force"
    return -spring_constant * np.array(displacement)


def compute_gravity_vector(pos, G=6.67430e-11, M=5.972e24, center=[0, 0, 0]):
    returns = "g_vec"
    r_vec = np.array(pos) - np.array(center)
    r = np.linalg.norm(r_vec)
    if r == 0:
        return np.array([0, 0, 0])
    g_mag = G * M / r**2
    return -g_mag * (r_vec / r)  # direction toward the center

def self_gravity_field(particle, target_pos):
    """
    Calculate the gravity field from a single particle at a given point in space.
    """
    returns = "g_vec"
    G = 6.67430e-11
    r_vec = np.array(target_pos) - np.array(particle["pos"])
    r = np.linalg.norm(r_vec)
    if r == 0:
        return np.array([0.0, 0.0, 0.0])  # No gravity at self
    g_mag = G * particle["mass"] / r**2
    return -g_mag * (r_vec / r)



